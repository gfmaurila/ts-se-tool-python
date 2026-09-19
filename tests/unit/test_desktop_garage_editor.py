import os

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import QSettings
from PySide6.QtWidgets import QApplication

from tsse.application import PendingChangeDecision
from tsse.application.compatibility import CompatibilityAssessment, CompatibilityStatus, GameVersion
from tsse.application.editor_service import GarageEditorSession
from tsse.config import GameRootStore
from tsse.core.profiles import Game
from tsse.desktop.main import create_window

GARAGE_SAVE = '''SiiNunit
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
VALIDATED_VERSION = GameVersion("1.61")


def _window_with_garage(tmp_path, version=VALIDATED_VERSION):
    root = tmp_path / "ATS"
    slot = root / "profiles" / "profile" / "save" / "autosave"
    slot.mkdir(parents=True)
    (slot.parent.parent / "profile.sii").write_text("SiiNunit\n", encoding="utf-8")
    (slot / "game.sii").write_text(GARAGE_SAVE, encoding="utf-8")
    settings = GameRootStore(QSettings(str(tmp_path / "settings.ini"), QSettings.Format.IniFormat))
    settings.set_root(Game.ATS, root)
    window = create_window(tmp_path / "Documents", settings)
    window._load_current_context(window.selected_save, version)
    window.editor_tabs.setCurrentIndex(3)
    window.garage_list.setCurrentRow(0)
    return window


def test_garage_loads_persistent_session_without_dirty(tmp_path) -> None:
    application = QApplication.instance() or QApplication([])
    window = _window_with_garage(tmp_path)

    assert window.garage_list.count() == 1
    assert window.garage_identifier.text() == "garage.stable"
    assert window.garage_status.value() == 1
    assert window._garage_session is not None and not window._garage_session.dirty
    window.close()
    assert application is not None


def test_garage_status_widget_marks_session_dirty_and_pending(tmp_path) -> None:
    application = QApplication.instance() or QApplication([])
    window = _window_with_garage(tmp_path)
    window.garage_status.setValue(2)

    assert window._garage_session is not None and window._garage_session.dirty
    assert window._active_editor is not None and window._active_editor.is_dirty
    assert window._has_pending_changes()
    window.close()
    assert application is not None


def test_garage_active_editor_uses_persistent_session(tmp_path) -> None:
    application = QApplication.instance() or QApplication([])
    window = _window_with_garage(tmp_path)
    session = window._garage_session

    window.editor_tabs.setCurrentIndex(1)
    window.editor_tabs.setCurrentIndex(3)

    assert session is not None and window._garage_session is session
    assert window._active_editor is not None
    window.close()
    assert application is not None


@pytest.mark.parametrize(
    ("version", "enabled"),
    [(GameVersion("1.61"), True), (None, False), (GameVersion("1.62"), False)],
)
def test_garage_compatibility_controls_editability(tmp_path, version, enabled: bool) -> None:
    application = QApplication.instance() or QApplication([])
    window = _window_with_garage(tmp_path, version)

    assert window.garage_status.isEnabled() is enabled
    window.close()
    assert application is not None


def test_unsupported_garage_context_disables_mutation_inputs(tmp_path) -> None:
    application = QApplication.instance() or QApplication([])
    window = _window_with_garage(tmp_path)
    assert window.current_save_context is not None
    assessment = CompatibilityAssessment(
        Game.ATS, GameVersion("unsupported"), CompatibilityStatus.UNSUPPORTED
    )
    state = window.current_save_context.editor.load(
        window.current_save_context.save.game_sii, assessment
    )
    window._garage_session = GarageEditorSession(state)
    window.editor_tabs.setCurrentIndex(1)
    window.editor_tabs.setCurrentIndex(3)
    window.garage_list.setCurrentRow(0)

    assert not window.garage_status.isEnabled()
    assert not window.garage_save_button.isEnabled()
    window.close()
    assert application is not None


def test_garage_save_success_clears_dirty_and_persists(tmp_path) -> None:
    application = QApplication.instance() or QApplication([])
    window = _window_with_garage(tmp_path)
    window.garage_status.setValue(2)
    session, active, context = (
        window._garage_session,
        window._active_editor,
        window.current_save_context,
    )

    window.garage_save_button.click()

    assert session is not None and not session.dirty
    assert not window._has_pending_changes()
    assert window._garage_session is not session and window._active_editor is active
    assert window.current_save_context is not context
    assert window.garage_identifier.text() == "garage.stable"
    saved = window.current_save_context.save.game_sii.read_text(encoding="utf-8")
    assert "status: 2" in saved
    window.close()
    assert application is not None


def test_garage_save_failure_preserves_state_and_selection(tmp_path, monkeypatch) -> None:
    application = QApplication.instance() or QApplication([])
    window = _window_with_garage(tmp_path)
    window.garage_status.setValue(2)
    session, active, context = (
        window._garage_session,
        window._active_editor,
        window.current_save_context,
    )

    def fail(*_args):
        raise RuntimeError("write failed")

    monkeypatch.setattr(window._editor_service, "apply", fail)
    with pytest.raises(RuntimeError, match="write failed"):
        window._save_garage()

    assert session is not None and session.dirty and session.status() == 2
    assert window.garage_status.value() == 2
    assert window._garage_session is session and window._active_editor is active
    assert window.current_save_context is context and window._has_pending_changes()
    assert window.garage_identifier.text() == "garage.stable"
    window.close()
    assert application is not None


def test_garage_discard_restores_status_and_selection(tmp_path) -> None:
    application = QApplication.instance() or QApplication([])
    window = _window_with_garage(tmp_path)
    window.garage_status.setValue(2)
    active = window._active_editor

    window.garage_discard_button.click()

    assert window.garage_status.value() == 1
    assert window.garage_identifier.text() == "garage.stable"
    assert window._garage_session is not None and not window._garage_session.dirty
    assert not window._has_pending_changes() and window._active_editor is active
    window.close()
    assert application is not None


def test_garage_sale_uses_existing_session_and_confirmation(tmp_path, monkeypatch) -> None:
    application = QApplication.instance() or QApplication([])
    window = _window_with_garage(tmp_path)
    monkeypatch.setattr(
        "tsse.desktop.main.GarageSaleConfirmation.confirm", lambda *_args: True
    )

    assert window.garage_sell_button.isEnabled()
    window.garage_sell_button.click()

    assert window._garage_session is not None and not window._garage_session.dirty
    assert window.garage_identifier.text() == "garage.stable"
    saved = window.current_save_context.save.game_sii.read_text(encoding="utf-8")
    assert "status: 6" in saved
    window.close()
    assert application is not None


def test_garage_dirty_sale_cancel_preserves_pending_status(tmp_path, monkeypatch) -> None:
    application = QApplication.instance() or QApplication([])
    window = _window_with_garage(tmp_path)
    window.garage_status.setValue(2)
    monkeypatch.setattr(
        "tsse.desktop.main.PendingChangesPrompt.decide",
        lambda *_args: PendingChangeDecision.CANCEL,
    )
    monkeypatch.setattr(
        "tsse.desktop.main.GarageSaleConfirmation.confirm",
        lambda *_args: pytest.fail("sale confirmation must not be shown"),
    )

    window.garage_sell_button.click()

    assert window._garage_session is not None and window._garage_session.dirty
    assert window.garage_status.value() == 2 and window._has_pending_changes()
    saved = window.current_save_context.save.game_sii.read_text(encoding="utf-8")
    assert "status: 1" in saved
    window.close()
    assert application is not None


def test_garage_without_context_is_safe(tmp_path) -> None:
    application = QApplication.instance() or QApplication([])
    settings = GameRootStore(QSettings(str(tmp_path / "settings.ini"), QSettings.Format.IniFormat))
    window = create_window(tmp_path / "Documents", settings)
    window.editor_tabs.setCurrentIndex(3)

    assert window._garage_session is None and window._active_editor is None
    assert not window.garage_status.isEnabled()
    assert not window.garage_save_button.isEnabled()
    assert not window.garage_sell_button.isEnabled()
    window.close()
    assert application is not None
