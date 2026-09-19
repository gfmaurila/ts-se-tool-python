from pathlib import Path

import pytest

from tsse.application import (
    ProfileIdentityEditor,
    ProfileIdentityError,
    profile_directory_identity,
    replace_profile_name,
)
from tsse.core.sii import parse_sii


def _profile(name: str = "Original") -> str:
    return (
        "SiiNunit\n{\nuser_profile : profile.id {\n"
        f' profile_name: "{name}"\n unknown_future: preserve\n' "}\n}\n"
    )


def test_replaces_internal_name_and_preserves_unknown_text() -> None:
    edited = replace_profile_name(_profile(), " New Name ")

    assert 'profile_name: "New Name"' in edited
    assert "unknown_future: preserve" in edited
    assert parse_sii(edited).blocks[0].fields[-1].key == "unknown_future"


@pytest.mark.parametrize("name", ["", " " * 2, "a" * 31, "bad|name", "bad\\name"])
def test_rejects_invalid_legacy_profile_names(name: str) -> None:
    with pytest.raises(ProfileIdentityError):
        replace_profile_name(_profile(), name)


def test_missing_name_and_safe_persisted_round_trip(tmp_path: Path) -> None:
    target = tmp_path / "profile.sii"
    original = _profile()
    target.write_text(original, encoding="utf-8")

    result = ProfileIdentityEditor().rename(target, "Renamed")

    assert result.backup.read_text(encoding="utf-8") == original
    assert 'profile_name: "Renamed"' in target.read_text(encoding="utf-8")
    with pytest.raises(ProfileIdentityError, match="missing"):
        replace_profile_name("SiiNunit\n{\nuser_profile : id {\n}\n}\n", "Name")


def test_legacy_directory_identity_uses_uppercase_utf8_hex() -> None:
    assert profile_directory_identity("Simple Name") == "53696D706C65204E616D65"
    assert profile_directory_identity("Café") == "436166C3A9"


def test_directory_rename_updates_staged_identity_and_keeps_backup(tmp_path: Path) -> None:
    source = tmp_path / "4F6C64"
    source.mkdir()
    profile = source / "profile.sii"
    profile.write_text(_profile("Old"), encoding="utf-8")

    result = ProfileIdentityEditor().rename_directory(profile, "New Name")

    assert not source.exists()
    assert result.destination.name == "4E6577204E616D65"
    assert 'profile_name: "New Name"' in (result.destination / "profile.sii").read_text()
    assert list(result.destination.glob("profile.sii.tsse-backup-*"))


def test_directory_rename_rejects_conflict_or_missing_source(tmp_path: Path) -> None:
    source = tmp_path / "source"
    source.mkdir()
    (source / "profile.sii").write_text(_profile(), encoding="utf-8")
    (tmp_path / profile_directory_identity("Taken")).mkdir()
    with pytest.raises(ProfileIdentityError, match="already exists"):
        ProfileIdentityEditor().rename_directory(source / "profile.sii", "Taken")
    with pytest.raises(ProfileIdentityError, match="existing"):
        ProfileIdentityEditor().rename_directory(tmp_path / "absent" / "profile.sii", "New")
