"""Read-only filesystem discovery for ATS and ETS2 profiles."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path

from tsse.core.profiles import Game, GameInstallation, Profile, SaveSlot

PROFILE_FILE = "profile.sii"
SAVE_FILE = "game.sii"
PROFILE_COLLECTIONS = (("profiles", False), ("steam_profiles", True))


@dataclass(frozen=True, slots=True)
class DiscoverySettings:
    """Input directories for profile discovery.

    A custom folder replaces the standard game folder below `documents_directory`
    for that game. Values are treated as game roots, not profile directories.
    """

    documents_directory: Path
    custom_game_folders: Mapping[Game, Path]
    installation_folders: Mapping[Game, Path]

    @classmethod
    def with_defaults(cls, documents_directory: Path) -> DiscoverySettings:
        """Create settings with no custom game or installation locations."""
        return cls(documents_directory, {}, {})

    def game_documents_directory(self, game: Game) -> Path:
        """Resolve the configured Documents root for a game."""
        return self.custom_game_folders.get(
            game, self.documents_directory / game.documents_folder_name
        )


class ProfileDiscovery:
    """Discover valid profile and save directories without parsing or writing files."""

    def __init__(self, settings: DiscoverySettings) -> None:
        self._settings = settings

    def set_configured_root(self, game: Game, root: Path | None) -> None:
        """Update one manual root while retaining automatic fallback."""
        custom = dict(self._settings.custom_game_folders)
        if root is None:
            custom.pop(game, None)
        else:
            custom[game] = root
        self._settings = DiscoverySettings(
            self._settings.documents_directory,
            custom,
            self._settings.installation_folders,
        )

    @staticmethod
    def root_has_profile_collections(root: Path) -> bool:
        """Return whether a root contains either supported profile collection."""
        return any((root / collection).is_dir() for collection, _ in PROFILE_COLLECTIONS)

    def root_for_game(self, game: Game) -> Path:
        """Return the effective configured-or-automatic root for status text."""
        return self._settings.game_documents_directory(game)

    def discover_installations(self) -> tuple[GameInstallation, ...]:
        """Return configured game locations, including missing paths for diagnostics."""
        return tuple(
            GameInstallation(
                game=game,
                documents_directory=self._settings.game_documents_directory(game),
                installation_directory=self._settings.installation_folders.get(game),
            )
            for game in Game
        )

    def discover_profiles(self, game: Game) -> tuple[Profile, ...]:
        """Return profiles with `profile.sii`, ordered predictably by storage and ID."""
        game_directory = self._settings.game_documents_directory(game)
        profiles: list[Profile] = []
        for collection_name, is_steam in PROFILE_COLLECTIONS:
            collection = game_directory / collection_name
            if not collection.is_dir():
                continue
            for directory in sorted(collection.iterdir(), key=lambda path: path.name.casefold()):
                profile_sii = directory / PROFILE_FILE
                if directory.is_dir() and profile_sii.is_file():
                    profiles.append(
                        Profile(
                            game=game,
                            profile_id=directory.name,
                            directory=directory,
                            profile_sii=profile_sii,
                            save_slots=self._discover_save_slots(directory),
                            is_steam=is_steam,
                        )
                    )
        return tuple(profiles)

    def discover_all_profiles(self) -> tuple[Profile, ...]:
        """Return profiles for both supported games in enum order."""
        return tuple(profile for game in Game for profile in self.discover_profiles(game))

    @staticmethod
    def _discover_save_slots(profile_directory: Path) -> tuple[SaveSlot, ...]:
        save_directory = profile_directory / "save"
        if not save_directory.is_dir():
            return ()
        return tuple(
            SaveSlot(name=directory.name, directory=directory, game_sii=directory / SAVE_FILE)
            for directory in sorted(save_directory.iterdir(), key=lambda path: path.name.casefold())
            if directory.is_dir() and (directory / SAVE_FILE).is_file()
        )
