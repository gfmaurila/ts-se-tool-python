"""Validated, atomic persistence for plaintext SII save-family files."""

from __future__ import annotations

import os
import shutil
import uuid
from collections.abc import Callable
from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path

from tsse.core.sii import SaveFormat, SiiParseError, detect_save_format, parse_sii

_SAVE_NAMES = frozenset({"game.sii", "info.sii", "profile.sii"})


class SafeSaveWriteError(RuntimeError):
    """Base error for an aborted safe SII write."""


class SaveChangedError(SafeSaveWriteError):
    """The target changed after it was read and before replacement."""


class SaveValidationError(SafeSaveWriteError):
    """Candidate text cannot be re-opened as an SiiN document."""


class BackupCreationError(SafeSaveWriteError):
    """The original could not be preserved before replacement."""


class AtomicReplaceError(SafeSaveWriteError):
    """The validated staging file could not replace the target."""


@dataclass(frozen=True, slots=True)
class SaveWriteResult:
    """Paths produced by one successful staged write."""

    target: Path
    backup: Path
    original_sha256: str
    backup_sha256: str
    written_sha256: str


class SafeSaveWriter:
    """Back up, validate, and atomically replace one known SII file.

    The candidate is parsed before and after it reaches a sibling temporary
    file. The original is compared again immediately before replacement.
    """

    def write_text(
        self,
        target: Path,
        text: str,
        *,
        expected_original: bytes | None = None,
        validator: Callable[[str], object] | None = None,
    ) -> SaveWriteResult:
        """Persist validated UTF-8 SiiN *text* without direct truncation."""
        if target.name not in _SAVE_NAMES:
            raise SafeSaveWriteError(f"unsupported SII target: {target.name}")
        if not target.is_file():
            raise SafeSaveWriteError(f"save file not found: {target}")
        try:
            parse_sii(text)
        except SiiParseError as error:
            raise SaveValidationError("candidate is not valid SiiN text") from error

        encoded = text.encode("utf-8")

        def validate(data: bytes) -> None:
            try:
                staged = data.decode("utf-8")
                parse_sii(staged)
            except (UnicodeDecodeError, SiiParseError) as error:
                raise SaveValidationError("staged SII file did not reparse") from error
            if validator is not None:
                validator(staged)

        return self._write_bytes(target, encoded, expected_original, validate)

    def restore_backup(
        self, target: Path, backup: Path, *, expected_original: bytes | None = None
    ) -> SaveWriteResult:
        """Explicitly restore a selected TSSE backup using staged atomic I/O.

        A new backup of the current target is retained before replacement; the
        selected historical backup is never removed or overwritten.
        """
        if not backup.is_file() or backup.stat().st_size == 0:
            raise SaveValidationError(f"backup is missing or empty: {backup}")
        if backup.parent != target.parent or not backup.name.startswith(
            f"{target.name}.tsse-backup-"
        ):
            raise SaveValidationError(f"backup does not belong to target: {backup}")
        content = backup.read_bytes()

        def validate(data: bytes) -> None:
            save_format = detect_save_format(data)
            if save_format is SaveFormat.UNKNOWN or not data:
                raise SaveValidationError("backup has an unsupported or empty save format")
            if save_format is SaveFormat.PLAINTEXT:
                try:
                    parse_sii(data.decode("utf-8"))
                except (UnicodeDecodeError, SiiParseError) as error:
                    raise SaveValidationError("plaintext backup did not reparse") from error

        return self._write_bytes(target, content, expected_original, validate)

    @staticmethod
    def discover_backups(target: Path) -> tuple[Path, ...]:
        """Return only TSSE backups for *target*, newest filesystem timestamp first."""
        if not target.parent.is_dir():
            return ()
        prefix = f"{target.name}.tsse-backup-"
        return tuple(
            sorted(
                (
                    path
                    for path in target.parent.iterdir()
                    if path.is_file() and path.name.startswith(prefix)
                ),
                key=lambda path: (path.stat().st_mtime_ns, path.name),
                reverse=True,
            )
        )

    def _write_bytes(
        self,
        target: Path,
        content: bytes,
        expected_original: bytes | None,
        validator: Callable[[bytes], None],
    ) -> SaveWriteResult:
        if target.name not in _SAVE_NAMES:
            raise SafeSaveWriteError(f"unsupported SII target: {target.name}")
        if not target.is_file():
            raise SafeSaveWriteError(f"save file not found: {target}")
        if not content:
            raise SaveValidationError("candidate must not be empty")
        original = target.read_bytes()
        if expected_original is not None and original != expected_original:
            raise SaveChangedError(f"save changed before staging: {target}")
        token = uuid.uuid4().hex
        temporary = target.with_name(f".{target.name}.tsse-write-{token}.tmp")
        backup = target.with_name(f"{target.name}.tsse-backup-{token}")
        try:
            with temporary.open("xb") as stream:
                stream.write(content)
                stream.flush()
                os.fsync(stream.fileno())
            try:
                validator(temporary.read_bytes())
            except OSError as error:
                raise SaveValidationError("could not validate staged SII file") from error
            if target.read_bytes() != original:
                raise SaveChangedError(f"save changed while staging: {target}")
            try:
                shutil.copy2(target, backup)
            except OSError as error:
                raise BackupCreationError(f"could not create backup: {backup}") from error
            if backup.read_bytes() != original:
                raise BackupCreationError(f"backup bytes differ from original: {backup}")
            try:
                os.replace(temporary, target)
            except OSError as error:
                raise AtomicReplaceError(f"could not atomically replace save: {target}") from error
        except OSError as error:
            raise SafeSaveWriteError(f"could not safely write {target}: {error}") from error
        finally:
            if temporary.exists():
                temporary.unlink()
        return SaveWriteResult(
            target=target,
            backup=backup,
            original_sha256=sha256(original).hexdigest(),
            backup_sha256=sha256(backup.read_bytes()).hexdigest(),
            written_sha256=sha256(content).hexdigest(),
        )
