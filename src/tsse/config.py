"""Application configuration independent from UI and filesystem operations."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True, slots=True)
class AppSettings:
    """Runtime settings resolved from explicit inputs or safe defaults."""

    data_directory: Path
    log_level: str = "INFO"

    @classmethod
    def defaults(cls) -> AppSettings:
        """Return defaults without reading or modifying game save directories."""
        return cls(data_directory=Path.cwd() / "data")
