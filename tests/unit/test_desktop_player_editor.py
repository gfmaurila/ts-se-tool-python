import os

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import QSettings
from PySide6.QtWidgets import QApplication

from tsse.application.compatibility import CompatibilityAssessment, CompatibilityStatus, GameVersion
from tsse.application.editor_service import PlayerEditorSession
from tsse.config import GameRootStore
from tsse.core.profiles import Game
from tsse.desktop.main import create_window

PLAYER_SAVE = '''SiiNunit
{
economy : economy.one {
 experience_points: 10
 adr: 2
}
user_profile : profile.one {
 male: true
}
}
'''


def _window_with_player(tmp_path, version=None):
    root = tmp_path / "ATS"
    slot = root / "profiles" / "profile" / "save" / "autosave"
    slot.mkdir(parents=True)
    (slot.parent.parent / "profile.sii").write_text("SiiNunit\n", encoding="utf-8")
    (slot / "game.sii").write_text(PLAYER_SAVE, encoding="utf-8")
    settings = GameRootStore(QSettings(str(tmp_path / "settings.ini"), QSettings.Format.IniFormat))
    settings.set_root(Game.ATS, root)
    window = create_window(tmp_path / "Documents", settings)
    window._load_current_context(window.selected_save, version)
    window._load_player_widgets()
    window.editor_tabs.setCurrentIndex(1)
    return window


def test_player_editor_widgets_exist_and_no_context_is_safe(tmp_path) -> None:
    application = QApplication.instance() or QApplication([])
    settings = GameRootStore(QSettings(str(tmp_path / "settings.ini"), QSettings.Format.IniFormat))
    window = create_window(tmp_path / "Documents", settings)

    assert window.player_xp_spin.objectName() == "playerXpSpin"
    assert window.player_adr_spin.objectName() == "playerAdrSpin"
    assert window.player_male_check.objectName() == "playerMaleCheck"
    assert window.player_save_button.objectName() == "playerSaveButton"
    assert window.player_discard_button.objectName() == "playerDiscardButton"
    assert window._player_session is None
    assert window._active_editor is None
    assert not window.player_xp_spin.isEnabled()
    assert not window.player_adr_spin.isEnabled()
    assert not window.player_male_check.isEnabled()
    window.close()
    assert application is not None


def test_player_load_and_widget_edits_mark_pending(tmp_path) -> None:
    application = QApplication.instance() or QApplication([])
    window = _window_with_player(tmp_path, GameVersion("1.61"))
    assert window.player_xp_spin.value() == 10
    assert window.player_adr_spin.value() == 2
    assert window.player_male_check.isChecked()
    assert window._player_session is not None and not window._player_session.dirty
    window.player_xp_spin.setValue(11)
    assert window._player_session.dirty and window._has_pending_changes()
    window.close()
    assert application is not None


def test_player_adr_widget_marks_dirty(tmp_path) -> None:
    application = QApplication.instance() or QApplication([])
    window = _window_with_player(tmp_path, GameVersion("1.61"))
    original = window.player_adr_spin.value()
    window.player_adr_spin.setValue(original + 1 if original < 6 else original - 1)
    assert window._player_session is not None and window._player_session.dirty
    assert window._active_editor is not None and window._active_editor.is_dirty
    assert window._has_pending_changes()
    window.close()
    assert application is not None


def test_player_gender_widget_marks_dirty(tmp_path) -> None:
    application = QApplication.instance() or QApplication([])
    window = _window_with_player(tmp_path, GameVersion("1.61"))
    window.player_male_check.setChecked(not window.player_male_check.isChecked())
    assert window._player_session is not None and window._player_session.dirty
    assert window._active_editor is not None and window._active_editor.is_dirty
    assert window._has_pending_changes()
    window.close()
    assert application is not None


def test_validated_enables_and_blocked_versions_disable_player_inputs(tmp_path) -> None:
    application = QApplication.instance() or QApplication([])
    validated = _window_with_player(tmp_path / "validated", GameVersion("1.61"))
    assert validated.player_xp_spin.isEnabled()
    validated.close()
    for name, version in (("unknown", None), ("unvalidated", GameVersion("1.62"))):
        window = _window_with_player(tmp_path / name, version)
        assert not window.player_xp_spin.isEnabled()
        assert not window.player_adr_spin.isEnabled()
        assert not window.player_male_check.isEnabled()
        window.close()
    assert application is not None


def test_unsupported_player_context_disables_mutation_inputs(tmp_path) -> None:
    application = QApplication.instance() or QApplication([])
    window = _window_with_player(tmp_path, GameVersion("1.61"))
    assert window.current_save_context is not None
    assessment = CompatibilityAssessment(
        Game.ATS, GameVersion("unsupported"), CompatibilityStatus.UNSUPPORTED
    )
    state = window.current_save_context.editor.load(
        window.current_save_context.save.game_sii, assessment
    )
    window._player_session = PlayerEditorSession(state)
    window._load_player_widgets()
    assert not window.player_xp_spin.isEnabled()
    assert not window.player_adr_spin.isEnabled()
    assert not window.player_male_check.isEnabled()
    assert not window.player_save_button.isEnabled()
    window.close()
    assert application is not None


def test_player_save_success_clears_dirty_and_persists(tmp_path) -> None:
    application = QApplication.instance() or QApplication([])
    window = _window_with_player(tmp_path, GameVersion("1.61"))
    window.player_xp_spin.setValue(11)
    active = window._active_editor
    window.player_save_button.click()
    assert window._player_session is not None and not window._player_session.dirty
    assert not window._has_pending_changes() and window._active_editor is active
    saved = window.current_save_context.save.game_sii.read_text(encoding="utf-8")
    assert "experience_points: 11" in saved
    window.close()
    assert application is not None


def test_player_discard_restores_widgets(tmp_path) -> None:
    application = QApplication.instance() or QApplication([])
    window = _window_with_player(tmp_path, GameVersion("1.61"))
    original = (
        window.player_xp_spin.value(),
        window.player_adr_spin.value(),
        window.player_male_check.isChecked(),
    )
    window.player_xp_spin.setValue(11)
    window.player_adr_spin.setValue(3)
    window.player_male_check.setChecked(False)
    active = window._active_editor
    window.player_discard_button.click()
    current = (
        window.player_xp_spin.value(),
        window.player_adr_spin.value(),
        window.player_male_check.isChecked(),
    )
    assert current == original
    assert window._player_session is not None and not window._player_session.dirty
    assert window._active_editor is active
    window.close()
    assert application is not None


def test_player_save_failure_preserves_state(tmp_path, monkeypatch) -> None:
    application = QApplication.instance() or QApplication([])
    window = _window_with_player(tmp_path, GameVersion("1.61"))
    window.player_xp_spin.setValue(11)
    session, active = window._player_session, window._active_editor
    context = window.current_save_context

    def fail(*_args):
        raise RuntimeError("write failed")

    monkeypatch.setattr(window._editor_service, "apply", fail)
    with pytest.raises(RuntimeError, match="write failed"):
        window._save_player()
    assert session is not None and session.dirty and session.experience == "11"
    assert window.player_xp_spin.value() == 11
    assert window._player_session is session and window._active_editor is active
    assert window.current_save_context is context and window._has_pending_changes()
    window.close()
    assert application is not None
