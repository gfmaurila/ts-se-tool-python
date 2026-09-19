"""Safe, lossless profile-name editing for plaintext ``profile.sii`` files."""

from __future__ import annotations

import re
import shutil
import uuid
from dataclasses import dataclass
from pathlib import Path

from tsse.core.sii import SiiParseError, parse_sii
from tsse.infrastructure.filesystem import SafeSaveWriter, SaveWriteResult

_PROFILE_NAME = re.compile(r"^(?P<indent>\s*)profile_name\s*:\s*.*$", re.MULTILINE)
_FORBIDDEN = frozenset({"\\", "|"})
_MAX_NAME_LENGTH = 30


def profile_directory_identity(name: str) -> str:
    """Return the legacy profile-folder identity (uppercase UTF-8 hexadecimal)."""
    return validate_profile_name(name).encode("utf-8").hex().upper()


class ProfileIdentityError(ValueError):
    """A requested profile identity does not meet legacy UI constraints."""


def validate_profile_name(name: str) -> str:
    """Trim spaces and enforce the legacy rename dialog's 1–30-char policy."""
    normalized = name.strip(" ")
    if not normalized or len(normalized) > _MAX_NAME_LENGTH:
        raise ProfileIdentityError("profile name must contain 1 to 30 characters")
    if any(character in _FORBIDDEN for character in normalized):
        raise ProfileIdentityError("profile name contains a forbidden character")
    return normalized


def replace_profile_name(source: str, name: str) -> str:
    """Replace exactly one ``profile_name`` field without normalizing other text."""
    normalized = validate_profile_name(name)
    try:
        parse_sii(source)
    except SiiParseError as error:
        raise ProfileIdentityError("profile source is not valid SiiN") from error
    replacement, count = _PROFILE_NAME.subn(
        lambda match: f'{match.group("indent")}profile_name: "{normalized}"', source, count=1
    )
    if count != 1:
        raise ProfileIdentityError("profile_name field is missing")
    return replacement


class ProfileIdentityEditor:
    """Persist a plaintext profile identity through the safe filesystem port."""

    def __init__(self, writer: SafeSaveWriter | None = None) -> None:
        self._writer = writer or SafeSaveWriter()

    def rename(self, profile_sii: Path, name: str) -> SaveWriteResult:
        """Update only the internal identity; directory rename is a separate transfer step."""
        if profile_sii.name != "profile.sii":
            raise ProfileIdentityError("identity edits require profile.sii")
        try:
            source = profile_sii.read_text(encoding="utf-8")
        except OSError as error:
            raise ProfileIdentityError(f"could not read profile: {profile_sii}") from error
        return self._writer.write_text(profile_sii, replace_profile_name(source, name))

    def rename_directory(self, profile_sii: Path, name: str) -> DirectoryRenameResult:
        """Rename a profile directory transactionally while updating its SiiN identity.

        The legacy tool copies then deletes.  A sibling staging copy and rollback
        directory provide the same visible result without exposing an edited source.
        """
        normalized = validate_profile_name(name)
        source = profile_sii.parent
        if profile_sii.name != "profile.sii" or not source.is_dir():
            raise ProfileIdentityError("identity edits require an existing profile.sii")
        destination = source.with_name(profile_directory_identity(normalized))
        if destination == source:
            return DirectoryRenameResult(source, destination)
        if destination.exists():
            raise ProfileIdentityError(f"profile destination already exists: {destination}")
        staging = source.with_name(f".tsse-stage-{uuid.uuid4().hex[:8]}")
        rollback = source.with_name(f".tsse-rollback-{uuid.uuid4().hex[:8]}")
        try:
            shutil.copytree(source, staging, copy_function=shutil.copy2)
            self.rename(staging / "profile.sii", normalized)
            source.replace(rollback)
            try:
                staging.replace(destination)
            except OSError:
                rollback.replace(source)
                raise
            shutil.rmtree(rollback)
        except OSError as error:
            raise ProfileIdentityError(f"could not safely rename profile: {error}") from error
        finally:
            if staging.exists():
                shutil.rmtree(staging)
            if rollback.exists() and source.exists():
                shutil.rmtree(rollback)
        return DirectoryRenameResult(source, destination)


@dataclass(frozen=True, slots=True)
class DirectoryRenameResult:
    """The old and new directory locations of a completed rename."""

    source: Path
    destination: Path
