"""Application configuration independent from UI and filesystem operations."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from PySide6.QtCore import QSettings

from tsse.core.profiles import Game


@dataclass(frozen=True, slots=True)
class AppSettings:
    """Runtime settings resolved from explicit inputs or safe defaults."""

    data_directory: Path
    log_level: str = "INFO"

    @classmethod
    def defaults(cls) -> AppSettings:
        """Return defaults without reading or modifying game save directories."""
        return cls(data_directory=Path.cwd() / "data")


class GameRootStore:
    """Persistent per-game data roots, kept outside save/profile files."""

    def __init__(self, settings: QSettings | None = None) -> None:
        self._settings = settings if settings is not None else QSettings(
            QSettings.Format.IniFormat,
            QSettings.Scope.UserScope,
            "TSSETool",
            "TSSETool",
        )

    def get_root(self, game: Game) -> Path | None:
        value = self._settings.value(f"game_roots/{game.value}", "")
        return Path(str(value)) if value else None

    def set_root(self, game: Game, root: Path) -> None:
        self._settings.setValue(f"game_roots/{game.value}", str(root))
        self._settings.sync()

    def clear_root(self, game: Game) -> None:
        self._settings.remove(f"game_roots/{game.value}")
        self._settings.sync()
