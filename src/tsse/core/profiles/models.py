"""Immutable domain models for game profile discovery."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path


class Game(StrEnum):
    """Supported SCS games and their standard Documents folder names."""

    ATS = "ats"
    ETS2 = "ets2"

    @property
    def documents_folder_name(self) -> str:
        """Return the game folder normally stored under Windows Documents."""
        return {
            Game.ATS: "American Truck Simulator",
            Game.ETS2: "Euro Truck Simulator 2",
        }[self]


@dataclass(frozen=True, slots=True)
class SaveSlot:
    """A save directory containing a `game.sii` file."""

    name: str
    directory: Path
    game_sii: Path


@dataclass(frozen=True, slots=True)
class Profile:
    """A discovered local or Steam profile, without parsing its contents."""

    game: Game
    profile_id: str
    directory: Path
    profile_sii: Path
    save_slots: tuple[SaveSlot, ...]
    is_steam: bool


@dataclass(frozen=True, slots=True)
class GameInstallation:
    """Configured locations for one game; neither location is modified."""

    game: Game
    documents_directory: Path
    installation_directory: Path | None = None
