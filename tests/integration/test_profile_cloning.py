from pathlib import Path

import pytest

from tsse.application import ProfileCloneError, ProfileCloner
from tsse.core.profiles import Game
from tsse.core.sii import parse_sii
from tsse.infrastructure.filesystem import DiscoverySettings, ProfileDiscovery


def _write_plain_profile(directory: Path) -> None:
    directory.mkdir(parents=True)
    (directory / "profile.sii").write_text(
        "SiiNunit\n{\nprofile : profile.one {\n profile_name: \"Original\"\n"
        " creation_time: 1\n}\n}\n", encoding="utf-8"
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


def test_named_clone_is_selective_identified_and_rolls_back_batch(tmp_path: Path) -> None:
    documents = tmp_path / "Documents"
    root = documents / Game.ATS.documents_folder_name / "profiles"
    source_directory = root / "4F726იგ"
    _write_plain_profile(source_directory)
    (source_directory / "save" / "autosave" / "ignored.bin").write_bytes(b"not legacy")
    discovery = ProfileDiscovery(DiscoverySettings.with_defaults(documents))
    source = discovery.discover_profiles(Game.ATS)[0]
    before = source.profile_sii.read_bytes()

    result = ProfileCloner().clone_named(source, "Clone Name")

    assert source.profile_sii.read_bytes() == before
    assert result.directory.name == "436C6F6E65204E616D65"
    text = result.profile_sii.read_text(encoding="utf-8")
    assert 'profile_name: "Clone Name"' in text and "creation_time:" in text
    assert not (result.directory / "ignored.bin").exists()
    with pytest.raises(ProfileCloneError):
        ProfileCloner().clone_many(source, ["One", "Clone Name"])
    assert not (root / "4F6E65").exists()
