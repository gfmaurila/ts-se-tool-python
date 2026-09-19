"""Production orchestration for safe, plaintext SiiN save edits."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from tsse.application.compatibility import CompatibilityAssessment, CompatibilityRegistry
from tsse.core.sii import (
    SaveFormat,
    SiiDocument,
    SiiParseError,
    UnsupportedSaveFormatError,
    detect_save_format,
    parse_sii,
)
from tsse.infrastructure.decoder import SiiDecoder
from tsse.infrastructure.filesystem import SafeSaveWriter, SaveWriteResult

SaveMutation = Callable[[SiiDocument], SiiDocument]
SaveValidation = Callable[[SiiDocument], None]


class SaveEditError(RuntimeError):
    """Base error for a production save edit that did not reach replacement."""


class SaveStructureError(SaveEditError):
    """A decoded, mutated, or staged document lacks required SiiN structure."""


@dataclass(frozen=True, slots=True)
class ProductionSaveWriteResult:
    """Evidence retained from one completed production save write."""

    game_sii_path: Path
    backup_path: Path
    original_format: SaveFormat
    original_sha256: str
    backup_sha256: str
    written_sha256: str


class SaveEditService:
    """Decode, mutate, validate, back up, and atomically persist one game save.

    Domain rules remain in the supplied mutation and optional validation callables.
    This service has no GUI dependency and always emits plaintext SiiN on writes.
    """

    def __init__(
        self, decoder: SiiDecoder | None = None, writer: SafeSaveWriter | None = None
    ) -> None:
        self._decoder = decoder or SiiDecoder()
        self._writer = writer or SafeSaveWriter()

    def save(
        self,
        game_sii: Path,
        mutation: SaveMutation,
        *,
        validate: SaveValidation | None = None,
        compatibility: CompatibilityAssessment | None = None,
        unsafe_version_override: bool = False,
    ) -> ProductionSaveWriteResult:
        """Persist one validated AST mutation through the safe-write boundary."""
        if compatibility is not None:
            CompatibilityRegistry.require_write(
                compatibility, unsafe_override=unsafe_version_override
            )
        original = game_sii.read_bytes()
        if detect_save_format(original) is SaveFormat.UNKNOWN:
            raise UnsupportedSaveFormatError("unrecognized save header")
        decoded = self._decoder.decode_file(game_sii)
        try:
            document = parse_sii(decoded.data.decode("utf-8"))
        except (UnicodeDecodeError, SiiParseError) as error:
            raise SaveStructureError("decoded save is not valid UTF-8 SiiN") from error
        self._validate_structure(document)
        edited = mutation(document)
        if not isinstance(edited, SiiDocument):
            raise SaveEditError("save mutation must return an SiiDocument")
        self._validate_document(edited, validate)
        serialized = edited.serialize()
        if not serialized or not serialized.startswith("SiiNunit"):
            raise SaveStructureError("serialized save must be non-empty SiiN plaintext")

        def validate_staging(text: str) -> None:
            try:
                staged = parse_sii(text)
            except SiiParseError as error:
                raise SaveStructureError("staged save did not reparse") from error
            self._validate_document(staged, validate)

        written = self._writer.write_text(
            game_sii,
            serialized,
            expected_original=original,
            validator=validate_staging,
        )
        return self._result(written, decoded.source_format)

    def restore(self, game_sii: Path, backup: Path) -> ProductionSaveWriteResult:
        """Explicitly restore a selected TSSE backup; it is never deleted."""
        original = game_sii.read_bytes()
        written = self._writer.restore_backup(game_sii, backup, expected_original=original)
        return self._result(written, detect_save_format(backup.read_bytes()))

    def discover_backups(self, game_sii: Path) -> tuple[Path, ...]:
        """List only TSSE backups for this game save, newest first."""
        return self._writer.discover_backups(game_sii)

    @staticmethod
    def _validate_structure(document: SiiDocument) -> None:
        if not document.source.startswith("SiiNunit") or not document.blocks:
            raise SaveStructureError("SiiN document must contain at least one block")

    def _validate_document(self, document: SiiDocument, validate: SaveValidation | None) -> None:
        self._validate_structure(document)
        if validate is not None:
            validate(document)

    @staticmethod
    def _result(written: SaveWriteResult, original_format: SaveFormat) -> ProductionSaveWriteResult:
        return ProductionSaveWriteResult(
            game_sii_path=written.target,
            backup_path=written.backup,
            original_format=original_format,
            original_sha256=written.original_sha256,
            backup_sha256=written.backup_sha256,
            written_sha256=written.written_sha256,
        )
