from pathlib import Path

from tsse.core.profiles import Game
from tsse.infrastructure.filesystem import DiscoverySettings, ProfileDiscovery


def _profile(root: Path, collection: str, profile_id: str, *save_names: str) -> Path:
    directory = root / collection / profile_id
    directory.mkdir(parents=True)
    (directory / "profile.sii").write_text("SiiNunit\n", encoding="utf-8")
    for save_name in save_names:
        save_directory = directory / "save" / save_name
        save_directory.mkdir(parents=True)
        (save_directory / "game.sii").write_text("SiiNunit\n", encoding="utf-8")
    return directory


def test_discovers_standard_and_steam_profiles_with_valid_save_slots(tmp_path) -> None:
    documents = tmp_path / "Documents"
    game_root = documents / Game.ETS2.documents_folder_name
    local = _profile(game_root, "profiles", "BETA", "quicksave", "autosave")
    steam = _profile(game_root, "steam_profiles", "alpha", "manual")
    incomplete = game_root / "profiles" / "incomplete"
    incomplete.mkdir(parents=True)
    (incomplete / "save" / "broken").mkdir(parents=True)

    discovery = ProfileDiscovery(DiscoverySettings.with_defaults(documents))

    profiles = discovery.discover_profiles(Game.ETS2)

    assert [profile.profile_id for profile in profiles] == ["BETA", "alpha"]
    assert profiles[0].directory == local
    assert [slot.name for slot in profiles[0].save_slots] == ["autosave", "quicksave"]
    assert profiles[1].directory == steam
    assert profiles[1].is_steam is True


def test_custom_game_folder_replaces_standard_documents_location(tmp_path) -> None:
    custom_root = tmp_path / "portable-ats"
    _profile(custom_root, "profiles", "profile-one", "slot")
    documents = tmp_path / "Documents"
    _profile(documents / Game.ATS.documents_folder_name, "profiles", "ignored", "slot")
    settings = DiscoverySettings(documents, {Game.ATS: custom_root}, {})

    profiles = ProfileDiscovery(settings).discover_profiles(Game.ATS)

    assert [profile.profile_id for profile in profiles] == ["profile-one"]


def test_discover_installations_reports_configured_paths_without_accessing_them(tmp_path) -> None:
    settings = DiscoverySettings(
        tmp_path / "Documents",
        {Game.ETS2: tmp_path / "custom-ets2"},
        {Game.ATS: tmp_path / "SteamLibrary" / "common" / "American Truck Simulator"},
    )

    installations = ProfileDiscovery(settings).discover_installations()

    assert installations[0].game is Game.ATS
    assert installations[0].installation_directory == settings.installation_folders[Game.ATS]
    assert installations[1].documents_directory == settings.custom_game_folders[Game.ETS2]


def test_missing_game_directory_has_no_profiles(tmp_path) -> None:
    discovery = ProfileDiscovery(DiscoverySettings.with_defaults(tmp_path / "Documents"))

    assert discovery.discover_all_profiles() == ()
