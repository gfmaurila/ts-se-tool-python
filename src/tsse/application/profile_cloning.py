"""Safe full-profile cloning use case."""

from __future__ import annotations

import re
import shutil
import time
import uuid
from dataclasses import dataclass
from pathlib import Path

from tsse.application.profile_identity import (
    ProfileIdentityError,
    profile_directory_identity,
    validate_profile_name,
)
from tsse.core.profiles import Profile
from tsse.infrastructure.filesystem import SafeSaveWriter


class ProfileCloneError(RuntimeError):
    """Raised when a profile cannot be cloned safely."""


@dataclass(frozen=True, slots=True)
class CloneResult:
    """The independently located clone."""

    directory: Path
    profile_sii: Path


class ProfileCloner:
    """Copy a profile through a sibling staging directory, never changing source."""

    def clone(self, source: Profile, destination_directory: Path) -> CloneResult:
        """Create a complete clone at a new path, rolling back staging on failure."""
        if destination_directory.exists():
            raise ProfileCloneError(f"destination already exists: {destination_directory}")
        if not source.directory.is_dir() or not source.profile_sii.is_file():
            raise ProfileCloneError("source profile is incomplete or unavailable")

        staging = destination_directory.with_name(f".tsse-stage-{uuid.uuid4().hex[:8]}")
        try:
            shutil.copytree(source.directory, staging, copy_function=shutil.copy2)
            profile_sii = staging / "profile.sii"
            if not profile_sii.is_file():
                raise ProfileCloneError("staged clone has no profile.sii")
            staging.replace(destination_directory)
        except OSError as error:
            raise ProfileCloneError(f"could not clone profile: {error}") from error
        finally:
            if staging.exists():
                shutil.rmtree(staging)
        return CloneResult(destination_directory, destination_directory / "profile.sii")

    def clone_named(self, source: Profile, name: str, *, full: bool = False) -> CloneResult:
        """Create the selective legacy clone with a new internal/directory identity."""
        normalized = validate_profile_name(name)
        if not source.directory.is_dir() or not source.profile_sii.is_file():
            raise ProfileCloneError("source profile is incomplete or unavailable")
        destination = source.directory.with_name(profile_directory_identity(normalized))
        if destination.exists():
            raise ProfileCloneError(f"destination already exists: {destination}")
        staging = destination.with_name(f".tsse-stage-{uuid.uuid4().hex[:8]}")
        try:
            staging.mkdir()
            self._copy_legacy_profile_files(source.directory, staging)
            self._copy_legacy_saves(source.directory / "save", staging / "save", full)
            self._set_clone_identity(staging / "profile.sii", normalized)
            staging.replace(destination)
        except (OSError, ProfileIdentityError) as error:
            raise ProfileCloneError(f"could not create profile clone: {error}") from error
        finally:
            if staging.exists():
                shutil.rmtree(staging)
        return CloneResult(destination, destination / "profile.sii")

    def clone_many(
        self, source: Profile, names: list[str], *, full: bool = False
    ) -> tuple[CloneResult, ...]:
        """Clone each nonblank legacy dialog line; undo this batch on a failure."""
        created: list[CloneResult] = []
        try:
            for raw_name in names:
                if not raw_name.strip(" "):
                    continue
                created.append(self.clone_named(source, raw_name, full=full))
        except ProfileCloneError:
            for result in reversed(created):
                if result.directory.exists():
                    shutil.rmtree(result.directory)
            raise
        return tuple(created)

    @staticmethod
    def _copy_legacy_profile_files(source: Path, destination: Path) -> None:
        names = {"avatar.png", "profile.sii", "controls.sii", "config.cfg", "config_local.cfg"}
        for file in source.iterdir():
            if file.is_file() and (file.name in names or file.name.startswith("gearbox_layout_")):
                shutil.copy2(file, destination / file.name)
        if not (destination / "profile.sii").is_file():
            raise ProfileCloneError("source profile is missing profile.sii")

    @staticmethod
    def _copy_legacy_saves(source: Path, destination: Path, full: bool) -> None:
        allowed = {"game.sii", "info.sii", "preview.tga", "preview.mat", "preview.tobj"}
        roots = [source] if full else [source / "autosave"]
        for root in roots:
            if not root.is_dir():
                raise ProfileCloneError(f"source saves are unavailable: {root}")
            for file in root.rglob("*"):
                if file.is_file() and file.name in allowed:
                    target = destination / file.relative_to(source)
                    target.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(file, target)

    @staticmethod
    def _set_clone_identity(profile_sii: Path, name: str) -> None:
        """Apply the two fields the legacy clone changes: name and creation time."""
        source = profile_sii.read_text(encoding="utf-8")
        from tsse.application.profile_identity import replace_profile_name

        text = replace_profile_name(source, name)
        replacement, count = re.subn(
            r"(?m)^(?P<indent>\s*)creation_time\s*:\s*.*$",
            lambda match: f"{match.group('indent')}creation_time: {int(time.time())}",
            text,
            count=1,
        )
        if count != 1:
            raise ProfileCloneError("profile_name clone source is missing creation_time")
        SafeSaveWriter().write_text(profile_sii, replacement)
