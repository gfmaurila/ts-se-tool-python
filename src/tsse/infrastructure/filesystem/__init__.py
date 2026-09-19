"""Filesystem adapters."""

from tsse.infrastructure.filesystem.profile_discovery import DiscoverySettings, ProfileDiscovery
from tsse.infrastructure.filesystem.save_io import (
    AtomicReplaceError,
    BackupCreationError,
    SafeSaveWriteError,
    SafeSaveWriter,
    SaveChangedError,
    SaveValidationError,
    SaveWriteResult,
)

__all__ = [
    "AtomicReplaceError",
    "BackupCreationError",
    "DiscoverySettings",
    "ProfileDiscovery",
    "SafeSaveWriteError",
    "SafeSaveWriter",
    "SaveChangedError", "SaveValidationError", "SaveWriteResult",
]
