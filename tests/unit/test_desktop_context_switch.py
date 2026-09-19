import os

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import QSettings
from PySide6.QtWidgets import QApplication

from tsse.application import PendingChangeDecision
from tsse.application.compatibility import GameVersion
from tsse.config import GameRootStore
from tsse.core.profiles import Game
from tsse.desktop.main import create_window

SAVE = '''SiiNunit
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
 money_account: 100
}
player : player.one {
 hq_city: garage.stable
}
}
'''
VALIDATED_VERSION = GameVersion("1.61")


def _add_profile(root, identity: str, save_names: tuple[str, ...]) -> None:
    profile = root / "profiles" / identity
    profile.mkdir(parents=True)
    (profile / "profile.sii").write_text("SiiNunit\n", encoding="utf-8")
    for name in save_names:
        slot = profile / "save" / name
        slot.mkdir(parents=True)
        (slot / "game.sii").write_text(SAVE, encoding="utf-8")


def _window_with_switch_targets(tmp_path):
    ats, ets = tmp_path / "ATS", tmp_path / "ETS2"
    _add_profile(ats, "ats-a", ("save-a", "save-b"))
    _add_profile(ats, "ats-b", ("save-c",))
    _add_profile(ets, "ets-a", ("save-d",))
    settings = GameRootStore(QSettings(str(tmp_path / "settings.ini"), QSettings.Format.IniFormat))
    settings.set_root(Game.ATS, ats)
    settings.set_root(Game.ETS2, ets)
    window = create_window(tmp_path / "Documents", settings)
    window._load_current_context(window.selected_save, VALIDATED_VERSION)
    window.editor_tabs.setCurrentIndex(1)
    return window


def _make_player_dirty(window) -> int:
    value = window.player_xp_spin.value() + 1
    window.player_xp_spin.setValue(value)
    assert window._has_pending_changes()
    return value


def _request_switch(window, selector: str) -> None:
    if selector == "game":
        window.game.setCurrentIndex(1)
    elif selector == "profile":
        window.profile.setCurrentIndex(1)
    else:
        window.save.setCurrentIndex(1)


def _selection_identity(window, selector: str):
    combo = getattr(window, selector)
    value = combo.currentData()
    return getattr(value, "directory", value)


@pytest.mark.parametrize("selector", ["game", "profile", "save"])
def test_clean_context_switches_immediately(tmp_path, selector: str) -> None:
    application = QApplication.instance() or QApplication([])
    window = _window_with_switch_targets(tmp_path)
    before = window.current_save_context

    _request_switch(window, selector)

    assert window.current_save_context is not before
    if selector == "game":
        assert window.selected_game != before.game
    else:
        assert _selection_identity(window, selector) != getattr(before, selector).directory
    window.close()
    assert application is not None


@pytest.mark.parametrize("selector", ["game", "profile", "save"])
def test_dirty_save_success_then_switches(tmp_path, monkeypatch, selector: str) -> None:
    application = QApplication.instance() or QApplication([])
    window = _window_with_switch_targets(tmp_path)
    _make_player_dirty(window)
    before = window.current_save_context
    monkeypatch.setattr(
        "tsse.desktop.main.PendingChangesPrompt.decide",
        lambda *_args: PendingChangeDecision.SAVE,
    )

    _request_switch(window, selector)

    assert window.current_save_context is not before
    assert not window._has_pending_changes()
    window.close()
    assert application is not None


@pytest.mark.parametrize("selector", ["game", "profile", "save"])
def test_dirty_save_failure_restores_visual_selection_and_context(
    tmp_path, monkeypatch, selector: str
) -> None:
    application = QApplication.instance() or QApplication([])
    window = _window_with_switch_targets(tmp_path)
    edited = _make_player_dirty(window)
    before, active, session = (
        window.current_save_context,
        window._active_editor,
        window._player_session,
    )
    previous = _selection_identity(window, selector)
    monkeypatch.setattr(
        "tsse.desktop.main.PendingChangesPrompt.decide",
        lambda *_args: PendingChangeDecision.SAVE,
    )

    def fail(*_args):
        raise RuntimeError("fail")

    monkeypatch.setattr(window._editor_service, "apply", fail)

    _request_switch(window, selector)

    assert _selection_identity(window, selector) == previous
    assert window.current_save_context is before
    assert window._active_editor is active and window._player_session is session
    assert window.player_xp_spin.value() == edited and window._has_pending_changes()
    window.close()
    assert application is not None


@pytest.mark.parametrize("selector", ["game", "profile", "save"])
def test_dirty_discard_then_switches(tmp_path, monkeypatch, selector: str) -> None:
    application = QApplication.instance() or QApplication([])
    window = _window_with_switch_targets(tmp_path)
    _make_player_dirty(window)
    before = window.current_save_context
    monkeypatch.setattr(
        "tsse.desktop.main.PendingChangesPrompt.decide",
        lambda *_args: PendingChangeDecision.DISCARD,
    )

    _request_switch(window, selector)

    assert window.current_save_context is not before
    assert not window._has_pending_changes()
    window.close()
    assert application is not None


@pytest.mark.parametrize("selector", ["game", "profile", "save"])
def test_dirty_cancel_restores_visual_selection_and_context(
    tmp_path, monkeypatch, selector: str
) -> None:
    application = QApplication.instance() or QApplication([])
    window = _window_with_switch_targets(tmp_path)
    edited = _make_player_dirty(window)
    before, active, session = (
        window.current_save_context,
        window._active_editor,
        window._player_session,
    )
    previous = _selection_identity(window, selector)
    monkeypatch.setattr(
        "tsse.desktop.main.PendingChangesPrompt.decide",
        lambda *_args: PendingChangeDecision.CANCEL,
    )

    _request_switch(window, selector)

    assert _selection_identity(window, selector) == previous
    assert window.current_save_context is before
    assert window._active_editor is active and window._player_session is session
    assert window.player_xp_spin.value() == edited and window._has_pending_changes()
    window.close()
    assert application is not None


def test_cancel_restoration_does_not_reenter_the_coordinator(tmp_path, monkeypatch) -> None:
    application = QApplication.instance() or QApplication([])
    window = _window_with_switch_targets(tmp_path)
    _make_player_dirty(window)
    calls = []
    monkeypatch.setattr(
        "tsse.desktop.main.PendingChangesPrompt.decide",
        lambda *_args: calls.append("prompt") or PendingChangeDecision.CANCEL,
    )

    _request_switch(window, "save")

    assert calls == ["prompt"]
    window.close()
    assert application is not None


def test_coordinator_uses_active_company_editor(tmp_path, monkeypatch) -> None:
    application = QApplication.instance() or QApplication([])
    window = _window_with_switch_targets(tmp_path)
    window.editor_tabs.setCurrentIndex(2)
    window.company_name_edit.setText("New Company")
    before = window.current_save_context
    monkeypatch.setattr(
        "tsse.desktop.main.PendingChangesPrompt.decide",
        lambda *_args: PendingChangeDecision.CANCEL,
    )

    _request_switch(window, "save")

    assert window.current_save_context is before and window._has_pending_changes()
    assert window.company_name_edit.text() == "New Company"
    window.close()
    assert application is not None
