import zipfile
from pathlib import Path

import pytest

from tsse.application import ProfileSettingsZip, ProfileSettingsZipError


def test_settings_zip_round_trip(tmp_path: Path) -> None:
    source, target, archive = tmp_path / "source", tmp_path / "target", tmp_path / "settings.zip"
    source.mkdir()
    target.mkdir()
    (source / "config.cfg").write_text("source", encoding="utf-8")
    (source / "gearbox_x.sii").write_text("layout", encoding="utf-8")
    (target / "config.cfg").write_text("old", encoding="utf-8")
    service = ProfileSettingsZip()
    service.export(source, archive, ["config.cfg", "gearbox_x.sii"])
    assert set(zipfile.ZipFile(archive).namelist()) == {"config.cfg", "gearbox_x.sii"}
    service.import_(archive, target, ["config.cfg", "gearbox_x.sii"])
    assert (target / "config.cfg").read_text() == "source"


@pytest.mark.parametrize("entry", ["../x", "..\\x", "/x", "C:\\x", "\\\\server\\share\\x"])
def test_settings_zip_rejects_traversal(tmp_path: Path, entry: str) -> None:
    archive, target = tmp_path / "bad.zip", tmp_path / "target"
    target.mkdir()
    with zipfile.ZipFile(archive, "w") as output:
        output.writestr(entry, "bad")
        output.writestr("config.cfg", "ok")
    with pytest.raises(ProfileSettingsZipError):
        ProfileSettingsZip().import_(archive, target, ["config.cfg"])
