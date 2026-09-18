from pathlib import Path

from tsse.application import ProfileCloner
from tsse.core.profiles import Game
from tsse.core.sii import parse_sii
from tsse.infrastructure.filesystem import DiscoverySettings, ProfileDiscovery


def _write_plain_profile(directory: Path) -> None:
    directory.mkdir(parents=True)
    (directory / "profile.sii").write_text(
        "SiiNunit\n{\nprofile : profile.one {\n name: \"Original\"\n}\n}\n", encoding="utf-8"
    )
    save = directory / "save" / "autosave"
    save.mkdir(parents=True)
    (save / "game.sii").write_text("SiiNunit\n{\n}\n", encoding="utf-8")
    (directory / "extra.bin").write_bytes(b"preserve me")


def test_clone_preserves_source_and_is_discoverable_and_parseable(tmp_path) -> None:
    documents = tmp_path / "Documents"
    game_root = documents / Game.ATS.documents_folder_name
    source_directory = game_root / "profiles" / "original"
    _write_plain_profile(source_directory)
    discovery = ProfileDiscovery(DiscoverySettings.with_defaults(documents))
    source = discovery.discover_profiles(Game.ATS)[0]
    source_before = source.profile_sii.read_bytes()

    result = ProfileCloner().clone(source, game_root / "profiles" / "independent-clone")

    assert source.profile_sii.read_bytes() == source_before
    assert (result.directory / "extra.bin").read_bytes() == b"preserve me"
    clone_document = parse_sii(result.profile_sii.read_text(encoding="utf-8"))

    assert clone_document.blocks[0].identifier == "profile.one"
    assert [profile.profile_id for profile in discovery.discover_profiles(Game.ATS)] == [
        "independent-clone",
        "original",
    ]
