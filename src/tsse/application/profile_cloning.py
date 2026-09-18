"""Safe full-profile cloning use case."""

from __future__ import annotations

import shutil
import uuid
from dataclasses import dataclass
from pathlib import Path

from tsse.core.profiles import Profile


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

        staging = destination_directory.with_name(
            f".{destination_directory.name}.tsse-staging-{uuid.uuid4().hex}"
        )
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
