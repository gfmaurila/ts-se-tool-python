import os

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import QSettings
from PySide6.QtWidgets import QApplication

from tsse.application.compatibility import GameVersion
from tsse.application.editor_service import EditorService
from tsse.config import GameRootStore
from tsse.core.profiles import Game
from tsse.desktop.main import create_window

SAVE = '''SiiNunit
{
economy : economy.one {
 experience_points: 10
 adr: 2
 garages: 1
 garages[0]: garage.stable
 driver_pool: 0
}
user_profile : profile.one {
 male: true
 company_name: "Acme"
}
bank : bank.one {
 money_account: 100
}
player : player.one {
 hq_city: garage.stable
}
garage : garage.stable {
 status: 1
 drivers: 0
 vehicles: 0
 trailers: 0
}
}
'''


def _window(tmp_path, tab: int = 1):
    root = tmp_path / "ATS"
    slot = root / "profiles" / "profile" / "save" / "autosave"
    slot.mkdir(parents=True)
    (slot.parent.parent / "profile.sii").write_text("SiiNunit\n", encoding="utf-8")
    (slot / "game.sii").write_text(SAVE, encoding="utf-8")
    settings = GameRootStore(QSettings(str(tmp_path / "settings.ini"), QSettings.Format.IniFormat))
    settings.set_root(Game.ATS, root)
    window = create_window(tmp_path / "Documents", settings)
    window._load_current_context(window.selected_save, GameVersion("1.61"))
    window.editor_tabs.setCurrentIndex(tab)
    if tab == 3:
        window.garage_list.setCurrentRow(0)
    return window


def test_reload_rebuilds_all_context_sessions_and_reprojects(tmp_path) -> None:
    application = QApplication.instance() or QApplication([])
    window = _window(tmp_path, 1)
    window.player_xp_spin.setValue(11)
    old_context = window.current_save_context
    old_editor = old_context.editor
    old_player, old_company, old_garage = (
        window._player_session,
        window._company_session,
        window._garage_session,
    )
    old_active = window._active_editor

    window.player_save_button.click()

    assert window.current_save_context is not old_context
    assert window.current_save_context.editor is not old_editor
    assert window.current_save_context.assessment is not old_context.assessment
    assert window._player_session is not old_player
    assert window._company_session is not old_company
    assert window._garage_session is not old_garage
    assert window._active_editor is old_active
    assert window._active_editor._session is window._player_session
    assert window.player_xp_spin.value() == 11
    assert not window._has_pending_changes()
    window.close()
    assert application is not None


@pytest.mark.parametrize(
    ("tab", "session_name"),
    [(1, "_player_session"), (2, "_company_session"), (3, "_garage_session")],
)
def test_reload_rebinds_active_editor_for_each_feature(
    tmp_path, tab: int, session_name: str
) -> None:
    application = QApplication.instance() or QApplication([])
    window = _window(tmp_path, tab)
    if tab == 1:
        window.player_xp_spin.setValue(11)
        window.player_save_button.click()
    elif tab == 2:
        window.company_name_edit.setText("New Company")
        window.company_save_button.click()
    else:
        window.garage_status.setValue(2)
        window.garage_save_button.click()

    assert window._active_editor is not None
    assert window._active_editor._session is getattr(window, session_name)
    assert not window._has_pending_changes()
    window.close()
    assert application is not None


def test_reload_restores_garage_selection_by_stable_identifier(tmp_path) -> None:
    application = QApplication.instance() or QApplication([])
    window = _window(tmp_path, 3)
    assert window.garage_identifier.text() == "garage.stable"
    window.reload_current_save()

    assert window.garage_identifier.text() == "garage.stable"
    assert window._garage_session is not None
    assert window._garage_session.selected_identifier == "garage.stable"
    assert not window._garage_session.dirty
    window.close()
    assert application is not None


@pytest.mark.parametrize(
    "error", [ValueError("parse failed"), RuntimeError("service failed")]
)
def test_reload_failure_preserves_coherent_old_state(
    tmp_path, monkeypatch, error: Exception
) -> None:
    application = QApplication.instance() or QApplication([])
    window = _window(tmp_path, 1)
    old = (
        window.current_save_context,
        window.current_save_context.editor,
        window.current_save_context.assessment,
        window._player_session,
        window._company_session,
        window._garage_session,
        window._active_editor,
    )
    def fail(*_args):
        raise error

    monkeypatch.setattr(window, "_build_save_reload_candidate", fail)

    assert window.reload_current_save() is False
    assert window.current_save_context is old[0]
    assert window.current_save_context.editor is old[1]
    assert window.current_save_context.assessment is old[2]
    assert window._player_session is old[3]
    assert window._company_session is old[4]
    assert window._garage_session is old[5]
    assert window._active_editor is old[6]
    assert window.player_xp_spin.value() == 10
    window.close()
    assert application is not None


def test_reload_reprojection_does_not_mark_dirty(tmp_path) -> None:
    application = QApplication.instance() or QApplication([])
    window = _window(tmp_path, 2)
    assert window.reload_current_save()

    assert window._company_session is not None and not window._company_session.dirty
    assert window.company_name_edit.text() == "Acme"
    assert not window._has_pending_changes()
    window.close()
    assert application is not None


def test_candidate_editor_service_failure_keeps_old_context(tmp_path, monkeypatch) -> None:
    application = QApplication.instance() or QApplication([])
    window = _window(tmp_path, 1)
    old_context, old_session, old_active = (
        window.current_save_context,
        window._player_session,
        window._active_editor,
    )

    def fail(*_args):
        raise RuntimeError("candidate load failed")

    monkeypatch.setattr(EditorService, "load", fail)
    assert window.reload_current_save() is False
    assert window.current_save_context is old_context
    assert window._player_session is old_session
    assert window._active_editor is old_active
    window.close()
    assert application is not None


def test_candidate_session_validation_failure_keeps_old_context(tmp_path, monkeypatch) -> None:
    application = QApplication.instance() or QApplication([])
    window = _window(tmp_path, 2)
    old_context, old_session = window.current_save_context, window._company_session

    def fail(*_args):
        raise ValueError("candidate validation failed")

    monkeypatch.setattr("tsse.desktop.main.CompanyEditorSession", fail)
    assert window.reload_current_save() is False
    assert window.current_save_context is old_context
    assert window._company_session is old_session
    window.close()
    assert application is not None


def test_write_success_reload_failure_keeps_memory_coherent(tmp_path, monkeypatch) -> None:
    application = QApplication.instance() or QApplication([])
    window = _window(tmp_path, 1)
    old_context = window.current_save_context
    window.player_xp_spin.setValue(11)

    def fail(*_args):
        raise RuntimeError("reload failed after write")

    monkeypatch.setattr(window, "_build_save_reload_candidate", fail)
    window.player_save_button.click()

    assert window.current_save_context is old_context
    assert window._active_editor is not None
    assert window._active_editor._session is window._player_session
    assert window.player_xp_spin.value() == 10
    assert "experience_points: 11" in old_context.save.game_sii.read_text(encoding="utf-8")
    window.close()
    assert application is not None
