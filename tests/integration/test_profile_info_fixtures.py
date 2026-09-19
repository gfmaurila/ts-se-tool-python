import shutil
from pathlib import Path

import pytest

from tsse.application.profile_info import ProfileInfoService, parse_info_sii, parse_profile_sii


@pytest.mark.parametrize(
    "profile_fixture, info_fixture",
    [
        (
            Path("projeto_atual/ATS/67666D617572696C61202D207A657261646F/profile.sii"),
            Path("projeto_atual/ATS/67666D617572696C61202D207A657261646F/save/autosave/info.sii"),
        ),
        (
            Path("projeto_atual/ETS/4D4150415F455453/profile.sii"),
            Path("projeto_atual/ETS/4D4150415F455453/save/autosave/info.sii"),
        ),
    ],
)
def test_copied_real_profile_and_info_are_safely_written_as_siin(
    profile_fixture: Path, info_fixture: Path, tmp_path: Path
) -> None:
    profile_original = profile_fixture.read_bytes()
    info_original = info_fixture.read_bytes()
    profile = tmp_path / "profile.sii"
    info = tmp_path / "info.sii"
    shutil.copy2(profile_fixture, profile)
    shutil.copy2(info_fixture, info)
    service = ProfileInfoService()

    profile_result = service.rename_profile(profile, "Caf\u00e9")
    info_model = service.read_info(info)
    info_result = service.set_info_money(info, (info_model.money_account or 0) + 1)

    assert parse_profile_sii(profile.read_text(encoding="utf-8")).profile_name == "Caf\u00e9"
    assert parse_info_sii(info.read_text(encoding="utf-8")).money_account == (
        info_model.money_account or 0
    ) + 1
    assert profile_result.write.backup.read_bytes() == profile_original
    assert info_result.write.backup.read_bytes() == info_original
    assert profile_fixture.read_bytes() == profile_original
    assert info_fixture.read_bytes() == info_original
