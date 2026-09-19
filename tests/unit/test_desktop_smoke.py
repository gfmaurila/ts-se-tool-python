import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import QSettings
from PySide6.QtWidgets import QApplication, QDialog, QFileDialog

from tsse.application.compatibility import GameVersion
from tsse.config import GameRootStore
from tsse.core.profiles import Game
from tsse.desktop.main import create_window

PROFILE = """SiiNunit
{
user_profile : profile.one {
 profile_name: "Original"
 creation_time: 10
 save_time: 20
}
}
"""
GAME = """SiiNunit
{
economy : economy.one {
 adr: 1
}
}
"""


def _profile(root, identity="profile-one"):
    directory = root / "profiles" / identity
    slot = directory / "save" / "autosave"
    slot.mkdir(parents=True)
    (directory / "profile.sii").write_text(PROFILE, encoding="utf-8")
    (slot / "game.sii").write_text(GAME, encoding="utf-8")
    for name in ("config.cfg", "config_local.cfg", "controls.sii"):
        (directory / name).write_text(name, encoding="utf-8")
    return directory, slot


def test_main_window_smoke(tmp_path) -> None:
    application = QApplication.instance() or QApplication([])

    settings = GameRootStore(QSettings(str(tmp_path / "settings.ini"), QSettings.Format.IniFormat))
    window = create_window(tmp_path / "Documents", settings)

    assert window.windowTitle() == "TS SE Tool Python"
    assert window.game.count() == 2
    assert window.profile.count() == 0
    window.close()
    assert application is not None


def test_configured_root_drives_refresh_and_game_switch(tmp_path) -> None:
    application = QApplication.instance() or QApplication([])
    ats = tmp_path / "ATS"
    ets = tmp_path / "ETS2"
    for root, profile in ((ats, "ats-profile"), (ets, "ets-profile")):
        directory = root / "profiles" / profile
        directory.mkdir(parents=True)
        (directory / "profile.sii").write_text("SiiNunit\n", encoding="utf-8")
    backend = QSettings(str(tmp_path / "settings.ini"), QSettings.Format.IniFormat)
    store = GameRootStore(backend)
    store.set_root(Game.ATS, ats)
    store.set_root(Game.ETS2, ets)
    window = create_window(tmp_path / "Documents", store)
    assert window.profile.currentData().profile_id == "ats-profile"
    window.game.setCurrentIndex(1)
    assert window.profile.currentData().profile_id == "ets-profile"
    window.close()
    assert application is not None


def test_profile_save_diagnostics_and_unknown_write_block(tmp_path) -> None:
    application = QApplication.instance() or QApplication([])
    root = tmp_path / "ATS"
    _profile(root)
    store = GameRootStore(QSettings(str(tmp_path / "settings.ini"), QSettings.Format.IniFormat))
    store.set_root(Game.ATS, root)
    window = create_window(tmp_path / "Documents", store)

    assert "Profile name: Original" in window.profile_details.text()
    assert window.save.currentData().name == "autosave"
    assert "UNKNOWN" in window.compatibility_details.text()
    assert "WRITE BLOCKED" in window.compatibility_details.text()
    diagnostic = window.inspect_selected_save()
    assert diagnostic.parse_ok is True
    assert diagnostic.write_allowed is False
    window.close()
    assert application is not None


def test_profile_previews_clone_and_unicode_rename(tmp_path) -> None:
    application = QApplication.instance() or QApplication([])
    root = tmp_path / "ATS"
    directory, _ = _profile(root)
    store = GameRootStore(QSettings(str(tmp_path / "settings.ini"), QSettings.Format.IniFormat))
    store.set_root(Game.ATS, root)
    window = create_window(tmp_path / "Documents", store)

    assert window.rename_preview("Café") == ("Café", "436166C3A9")
    assert window.clone_preview("Copy") == ("Copy", "436F7079")
    window.clone_selected_profile("Copy")
    assert (directory.parent / "436F7079" / "profile.sii").is_file()
    window.rename_selected_profile("Café")
    assert (directory.parent / "436166C3A9" / "profile.sii").is_file()
    window.close()
    assert application is not None


def test_settings_zip_and_backup_restore_use_services(tmp_path) -> None:
    application = QApplication.instance() or QApplication([])
    root = tmp_path / "ATS"
    directory, slot = _profile(root)
    game = slot / "game.sii"
    backup = slot / "game.sii.tsse-backup-fixture"
    backup.write_text(GAME.replace("adr: 1", "adr: 0"), encoding="utf-8")
    store = GameRootStore(QSettings(str(tmp_path / "settings.ini"), QSettings.Format.IniFormat))
    store.set_root(Game.ATS, root)
    window = create_window(tmp_path / "Documents", store)

    archive = tmp_path / "settings.zip"
    assert window.export_settings(archive) == archive
    (directory / "controls.sii").write_text("changed", encoding="utf-8")
    window.import_settings(archive)
    assert (directory / "controls.sii").read_text(encoding="utf-8") == "controls.sii"
    window.refresh_backups()
    assert window.backup.count() == 1
    window.restore_selected_backup()
    assert "adr: 0" in game.read_text(encoding="utf-8")
    assert len(list(slot.glob("game.sii.tsse-backup-*"))) == 2
    window.close()
    assert application is not None


def test_gui_state_paths_and_dialogs_are_safe_without_user_write(tmp_path, monkeypatch) -> None:
    application = QApplication.instance() or QApplication([])
    root = tmp_path / "ATS"
    directory, slot = _profile(root)
    store = GameRootStore(QSettings(str(tmp_path / "settings.ini"), QSettings.Format.IniFormat))
    store.set_root(Game.ATS, root)
    window = create_window(tmp_path / "Documents", store)

    # Explicit caller-provided validation is displayed, while unknown remains blocked.
    diagnostic = window.inspect_selected_save(GameVersion("1.61"))
    assert diagnostic.write_allowed is True
    assert (
        "VALIDATED" in window.compatibility_details.text()
        or diagnostic.compatibility.value == "validated"
    )
    with window._busy_operation() as outer:
        assert outer is True
        with window._busy_operation() as nested:
            assert nested is False

    # Malformed profile metadata is reported without preventing discovery.
    (directory / "profile.sii").write_text("not sii", encoding="utf-8")
    window._show_profile(window.selected_profile)
    assert "Unavailable" in window.profile_details.text()

    # Dialog construction and validation paths are exercised without opening an interactive dialog.
    monkeypatch.setattr(QDialog, "exec", lambda self: self.reject())
    window.rename_selected_profile_dialog()
    window.clone_selected_profile_dialog()
    window.open_settings()
    monkeypatch.setattr(QFileDialog, "getSaveFileName", lambda *args: ("", ""))
    monkeypatch.setattr(QFileDialog, "getOpenFileName", lambda *args: ("", ""))
    window.export_settings_dialog()
    window.import_settings_dialog()
    window.restore_selected_backup_dialog()
    assert window.selected_save.directory == slot
    window.close()
    assert application is not None


def test_gui_error_and_disabled_action_paths(tmp_path) -> None:
    application = QApplication.instance() or QApplication([])
    root = tmp_path / "ATS"
    directory, _ = _profile(root)
    store = GameRootStore(QSettings(str(tmp_path / "settings.ini"), QSettings.Format.IniFormat))
    store.set_root(Game.ATS, root)
    window = create_window(tmp_path / "Documents", store)
    (directory / "save" / "autosave" / "game.sii").write_text("bad", encoding="utf-8")
    window._on_save_selected()
    assert "FAIL" in window.save_details.text() or "failed" in window.save_details.text().lower()
    window.backup.clear()
    window._update_actions()
    assert window.restore_backup_button.isEnabled() is False
    window._status("Write blocked: version unknown")
    assert window.statusBar().currentMessage().startswith("Write blocked")
    window.close()
    assert application is not None
