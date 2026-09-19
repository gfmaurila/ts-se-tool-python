import os

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import QSettings
from PySide6.QtWidgets import QApplication

from tsse.application.compatibility import CompatibilityAssessment, CompatibilityStatus, GameVersion
from tsse.application.editor_service import CompanyEditorSession
from tsse.config import GameRootStore
from tsse.core.profiles import Game
from tsse.desktop.main import create_window

COMPANY_SAVE = '''SiiNunit
{
economy : economy.one {
 experience_points: 10
 adr: 2
}
user_profile : profile.one {
 male: true
 company_name: "Acme"
}
bank : bank.one {
 money_account: 12345
}
player : player.one {
 hq_city: test.city
}
}
'''
VALIDATED_VERSION = GameVersion("1.61")


def _window_with_company(tmp_path, version=VALIDATED_VERSION):
    root = tmp_path / "ATS"
    slot = root / "profiles" / "profile" / "save" / "autosave"
    slot.mkdir(parents=True)
    (slot.parent.parent / "profile.sii").write_text("SiiNunit\n", encoding="utf-8")
    (slot / "game.sii").write_text(COMPANY_SAVE, encoding="utf-8")
    settings = GameRootStore(QSettings(str(tmp_path / "settings.ini"), QSettings.Format.IniFormat))
    settings.set_root(Game.ATS, root)
    window = create_window(tmp_path / "Documents", settings)
    window._load_current_context(window.selected_save, version)
    window._load_company_widgets()
    window.editor_tabs.setCurrentIndex(2)
    return window


def test_company_widgets_exist(tmp_path) -> None:
    application = QApplication.instance() or QApplication([])
    window = _window_with_company(tmp_path)

    assert window.company_name_edit.objectName() == "companyNameEdit"
    assert window.company_money_edit.objectName() == "companyMoneyEdit"
    assert window.company_hq_city_edit.objectName() == "companyHqCityEdit"
    assert window.company_save_button.objectName() == "companySaveButton"
    assert window.company_discard_button.objectName() == "companyDiscardButton"
    window.close()
    assert application is not None


def test_company_loads_without_dirty(tmp_path) -> None:
    application = QApplication.instance() or QApplication([])
    window = _window_with_company(tmp_path)

    assert window.company_name_edit.text() == "Acme"
    assert window.company_money_edit.text() == "12345"
    assert window.company_hq_city_edit.text() == "test.city"
    assert window._company_session is not None and not window._company_session.dirty
    window.close()
    assert application is not None


@pytest.mark.parametrize("field", ["name", "money", "hq"])
def test_company_widgets_mark_session_dirty(tmp_path, field: str) -> None:
    application = QApplication.instance() or QApplication([])
    window = _window_with_company(tmp_path / field)

    if field == "name":
        window.company_name_edit.setText("New Company")
    elif field == "money":
        window.company_money_edit.setText("54321")
    else:
        window.company_hq_city_edit.setText("new.city")

    assert window._company_session is not None and window._company_session.dirty
    assert window._active_editor is not None and window._active_editor.is_dirty
    assert window._has_pending_changes()
    window.close()
    assert application is not None


def test_company_active_editor_uses_persistent_session(tmp_path) -> None:
    application = QApplication.instance() or QApplication([])
    window = _window_with_company(tmp_path)
    session = window._company_session

    window.editor_tabs.setCurrentIndex(1)
    window.editor_tabs.setCurrentIndex(2)

    assert session is not None and window._company_session is session
    assert window._active_editor is not None
    window.company_name_edit.setText("New Company")
    assert window._active_editor.is_dirty
    window.close()
    assert application is not None


@pytest.mark.parametrize(
    ("version", "enabled"),
    [(GameVersion("1.61"), True), (None, False), (GameVersion("1.62"), False)],
)
def test_company_compatibility_controls_editability(tmp_path, version, enabled: bool) -> None:
    application = QApplication.instance() or QApplication([])
    window = _window_with_company(tmp_path, version)

    assert window.company_name_edit.isEnabled() is enabled
    assert window.company_money_edit.isEnabled() is enabled
    assert window.company_hq_city_edit.isEnabled() is enabled
    window.close()
    assert application is not None


def test_unsupported_company_context_disables_mutation_inputs(tmp_path) -> None:
    application = QApplication.instance() or QApplication([])
    window = _window_with_company(tmp_path)
    assert window.current_save_context is not None
    assessment = CompatibilityAssessment(
        Game.ATS, GameVersion("unsupported"), CompatibilityStatus.UNSUPPORTED
    )
    state = window.current_save_context.editor.load(
        window.current_save_context.save.game_sii, assessment
    )
    window._company_session = CompanyEditorSession(state)
    window._load_company_widgets()

    assert not window.company_name_edit.isEnabled()
    assert not window.company_money_edit.isEnabled()
    assert not window.company_hq_city_edit.isEnabled()
    assert not window.company_save_button.isEnabled()
    window.close()
    assert application is not None


def test_company_without_context_is_safe(tmp_path) -> None:
    application = QApplication.instance() or QApplication([])
    settings = GameRootStore(QSettings(str(tmp_path / "settings.ini"), QSettings.Format.IniFormat))
    window = create_window(tmp_path / "Documents", settings)
    window.editor_tabs.setCurrentIndex(2)

    assert window._company_session is None
    assert window._active_editor is None
    assert not window.company_name_edit.isEnabled()
    assert not window.company_money_edit.isEnabled()
    assert not window.company_hq_city_edit.isEnabled()
    assert not window.company_save_button.isEnabled()
    window.close()
    assert application is not None


def test_company_save_success_clears_dirty_and_persists(tmp_path) -> None:
    application = QApplication.instance() or QApplication([])
    window = _window_with_company(tmp_path)
    window.company_name_edit.setText("New Company")
    active, context, session = (
        window._active_editor,
        window.current_save_context,
        window._company_session,
    )

    window.company_save_button.click()

    assert window._company_session is not None and not window._company_session.dirty
    assert not window._has_pending_changes()
    assert window._active_editor is active and window.current_save_context is not context
    assert window._company_session is not session
    saved = window.current_save_context.save.game_sii.read_text(encoding="utf-8")
    assert 'company_name: "New Company"' in saved
    window.close()
    assert application is not None


def test_company_save_failure_preserves_state(tmp_path, monkeypatch) -> None:
    application = QApplication.instance() or QApplication([])
    window = _window_with_company(tmp_path)
    window.company_name_edit.setText("New Company")
    session, active, context = (
        window._company_session,
        window._active_editor,
        window.current_save_context,
    )

    def fail(*_args):
        raise RuntimeError("write failed")

    monkeypatch.setattr(window._editor_service, "apply", fail)
    with pytest.raises(RuntimeError, match="write failed"):
        window._save_company()

    assert session is not None and session.dirty and session.name == "New Company"
    assert window.company_name_edit.text() == "New Company"
    assert window._company_session is session and window._active_editor is active
    assert window.current_save_context is context and window._has_pending_changes()
    window.close()
    assert application is not None


def test_company_discard_restores_widgets(tmp_path) -> None:
    application = QApplication.instance() or QApplication([])
    window = _window_with_company(tmp_path)
    original = (
        window.company_name_edit.text(),
        window.company_money_edit.text(),
        window.company_hq_city_edit.text(),
    )
    window.company_name_edit.setText("New Company")
    window.company_money_edit.setText("54321")
    window.company_hq_city_edit.setText("new.city")
    active = window._active_editor

    window.company_discard_button.click()

    current = (
        window.company_name_edit.text(),
        window.company_money_edit.text(),
        window.company_hq_city_edit.text(),
    )
    assert current == original
    assert window._company_session is not None and not window._company_session.dirty
    assert not window._has_pending_changes() and window._active_editor is active
    window.close()
    assert application is not None
