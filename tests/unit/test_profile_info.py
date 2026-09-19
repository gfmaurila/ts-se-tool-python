from pathlib import Path

import pytest

from tsse.application.profile_info import (
    ProfileInfoError,
    ProfileInfoService,
    parse_info_sii,
    parse_profile_sii,
)
from tsse.infrastructure.filesystem import SafeSaveWriter, SaveChangedError

PROFILE = '''SiiNunit
{
user_profile : profile.one {
 profile_name: "Old Name"
 creation_time: 10
 save_time: 20
 unknown_future: preserve
}
future_profile : opaque.one {
 keep: yes
}
}
'''

INFO = '''SiiNunit
{
save_container : save.one {
 name: "Slot"
 time: 10
 file_time: 20
 version: 97
 info_version: 1
 info_players_experience: 30
 info_money_account: 40
 info_explored_ratio: &3cc0a4f6
 unknown_future: preserve
}
future_info : opaque.one {
 keep: yes
}
}
'''


def test_profile_and_info_models_read_proven_fields_and_preserve_unknown_content() -> None:
    profile = parse_profile_sii(PROFILE)
    info = parse_info_sii(INFO)

    assert (profile.profile_name, profile.creation_time, profile.save_time) == ("Old Name", 10, 20)
    assert (info.time, info.file_time, info.version, info.money_account) == (10, 20, 97, 40)
    assert "unknown_future: preserve" in profile.document.serialize()
    assert "future_info : opaque.one" in info.document.serialize()


def test_safe_profile_and_info_writes_create_exact_unique_backups(tmp_path: Path) -> None:
    profile_path = tmp_path / "profile.sii"
    info_path = tmp_path / "info.sii"
    profile_path.write_text(PROFILE, encoding="utf-8")
    info_path.write_text(INFO, encoding="utf-8")
    service = ProfileInfoService()
    original_profile = profile_path.read_bytes()
    original_info = info_path.read_bytes()

    profile_result = service.rename_profile(profile_path, "Caf\u00e9")
    info_result = service.set_info_money(info_path, -50)

    assert parse_profile_sii(profile_path.read_text(encoding="utf-8")).profile_name == "Caf\u00e9"
    assert parse_info_sii(info_path.read_text(encoding="utf-8")).money_account == -50
    assert profile_result.write.backup.read_bytes() == original_profile
    assert info_result.write.backup.read_bytes() == original_info
    assert profile_result.write.original_sha256 == profile_result.write.backup_sha256
    assert info_result.write.original_sha256 == info_result.write.backup_sha256
    assert "unknown_future: preserve" in profile_path.read_text(encoding="utf-8")
    assert "unknown_future: preserve" in info_path.read_text(encoding="utf-8")
    assert len(list(tmp_path.glob("profile.sii.tsse-backup-*"))) == 1
    assert len(list(tmp_path.glob("info.sii.tsse-backup-*"))) == 1


def test_malformed_models_and_concurrent_profile_change_abort(tmp_path: Path) -> None:
    with pytest.raises(ProfileInfoError):
        parse_profile_sii("SiiNunit\n{\nuser_profile : one {\n profile_name: x\n}\n}\n")
    with pytest.raises(ProfileInfoError):
        parse_info_sii("SiiNunit\n{\nsave_container : one {\n name: x\n}\n}\n")

    path = tmp_path / "profile.sii"
    path.write_text(PROFILE, encoding="utf-8")

    class RaceWriter(SafeSaveWriter):
        def write_text(self, target: Path, text: str, **kwargs: object):  # type: ignore[no-untyped-def]
            target.write_text(PROFILE.replace("Old Name", "External"), encoding="utf-8")
            return super().write_text(target, text, **kwargs)  # type: ignore[arg-type]

    with pytest.raises(SaveChangedError):
        ProfileInfoService(writer=RaceWriter()).rename_profile(path, "New Name")
    assert parse_profile_sii(path.read_text(encoding="utf-8")).profile_name == "External"
