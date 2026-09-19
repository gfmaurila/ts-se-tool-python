import pytest

from tsse.application import (
    CompanyEditorSession,
    EditorService,
    GarageEditorSession,
    PendingChangeDecision,
    PlayerEditorSession,
    resolve_pending_change,
    set_experience,
)
from tsse.application.compatibility import (
    CompatibilityAssessment,
    CompatibilityRegistry,
    CompatibilityStatus,
    CompatibilityWriteBlockedError,
    GameVersion,
)
from tsse.core.profiles import Game

SAVE = """SiiNunit
{
economy : economy.one {
 experience_points: 1
 adr: 1
}
user_profile : profile.one {
 male: true
 company_name: "Old"
}
player : player.one {
 hq_city: city.old
}
bank : bank.one {
 money_account: 10
}
}
"""


def test_apply_uses_safe_editor_and_reloads_persisted_document(tmp_path) -> None:
    game = tmp_path / "game.sii"
    game.write_text(SAVE, encoding="utf-8")
    assessment = CompatibilityRegistry().assess(Game.ATS, GameVersion("1.61"))

    result, state = EditorService().apply(game, assessment, lambda doc: set_experience(doc, 42))

    assert result.backup_path.is_file()
    assert "experience_points: 42" in state.document.source


def test_apply_blocks_unknown_before_read_or_backup(tmp_path) -> None:
    game = tmp_path / "game.sii"
    game.write_text(SAVE, encoding="utf-8")
    assessment = CompatibilityRegistry().assess(Game.ATS, None)

    try:
        EditorService().apply(game, assessment, lambda doc: set_experience(doc, 42))
    except CompatibilityWriteBlockedError:
        pass
    else:
        raise AssertionError("unknown compatibility must block writes")
    assert not tuple(tmp_path.glob("game.sii.tsse-backup-*"))


def test_player_session_is_dirty_saves_and_reloads(tmp_path) -> None:
    game = tmp_path / "game.sii"
    game.write_text(SAVE, encoding="utf-8")
    assessment = CompatibilityRegistry().assess(Game.ATS, GameVersion("1.61"))
    service = EditorService()
    session = PlayerEditorSession(service.load(game, assessment))
    session.experience, session.adr, session.male = "42", "3", False
    assert session.dirty
    result = session.save(service, game)
    assert result.backup_path.is_file()
    assert not session.dirty
    assert "experience_points: 42" in game.read_text(encoding="utf-8")


def test_player_session_discard_never_writes(tmp_path) -> None:
    game = tmp_path / "game.sii"
    game.write_text(SAVE, encoding="utf-8")
    assessment = CompatibilityRegistry().assess(Game.ATS, GameVersion("1.61"))
    session = PlayerEditorSession(EditorService().load(game, assessment))
    session.experience = "42"
    session.discard()
    assert session.experience == "1"
    assert not session.dirty
    assert not tuple(tmp_path.glob("game.sii.tsse-backup-*"))


@pytest.mark.parametrize("failure", [RuntimeError("validation"), RuntimeError("backup")])
def test_player_save_error_retains_dirty_values(tmp_path, monkeypatch, failure) -> None:
    game = tmp_path / "game.sii"
    game.write_text(SAVE, encoding="utf-8")
    service = EditorService()
    assessment = CompatibilityRegistry().assess(Game.ATS, GameVersion("1.61"))
    session = PlayerEditorSession(service.load(game, assessment))
    session.experience = "42"
    monkeypatch.setattr(service, "apply", lambda *_args: (_ for _ in ()).throw(failure))
    with pytest.raises(RuntimeError):
        session.save(service, game)
    assert session.dirty and session.experience == "42"


@pytest.mark.parametrize(
    "status", [CompatibilityStatus.UNVALIDATED, CompatibilityStatus.UNSUPPORTED]
)
def test_nonvalidated_player_write_is_blocked_without_backup(tmp_path, status) -> None:
    game = tmp_path / "game.sii"
    game.write_text(SAVE, encoding="utf-8")
    assessment = CompatibilityAssessment(Game.ATS, GameVersion("future"), status)
    session = PlayerEditorSession(EditorService().load(game, assessment))
    session.experience = "42"
    assert not session.write_allowed
    with pytest.raises(CompatibilityWriteBlockedError):
        session.save(EditorService(), game)
    assert not tuple(tmp_path.glob("game.sii.tsse-backup-*"))


def test_pending_change_decisions_save_discard_and_cancel(tmp_path) -> None:
    game = tmp_path / "game.sii"
    game.write_text(SAVE, encoding="utf-8")
    service = EditorService()
    assessment = CompatibilityRegistry().assess(Game.ATS, GameVersion("1.61"))
    session = PlayerEditorSession(service.load(game, assessment))
    session.experience = "42"
    assert not resolve_pending_change(session, PendingChangeDecision.CANCEL, service, game)
    assert session.dirty and session.experience == "42"
    assert resolve_pending_change(session, PendingChangeDecision.DISCARD, service, game)
    assert not session.dirty and not tuple(tmp_path.glob("game.sii.tsse-backup-*"))
    session.experience = "42"
    assert resolve_pending_change(session, PendingChangeDecision.SAVE, service, game)
    assert not session.dirty and tuple(tmp_path.glob("game.sii.tsse-backup-*"))


def test_company_session_saves_reloads_and_discards(tmp_path) -> None:
    game = tmp_path / "game.sii"
    game.write_text(SAVE, encoding="utf-8")
    service = EditorService()
    assessment = CompatibilityRegistry().assess(Game.ATS, GameVersion("1.61"))
    session = CompanyEditorSession(service.load(game, assessment))
    session.name, session.money, session.hq_city = "New", "99", "city.new"
    assert session.dirty
    session.save(service, game)
    assert not session.dirty
    assert "money_account: 99" in game.read_text(encoding="utf-8")
    session.money = "100"
    session.discard()
    assert session.money == "99" and not session.dirty


def test_garage_session_uses_stable_identifier_and_reloads_status(tmp_path) -> None:
    game = tmp_path / "game.sii"
    game.write_text(
        SAVE[:-2] + "garage : garage.stable {\n status: 1\n}\n}\n",
        encoding="utf-8",
    )
    service = EditorService()
    assessment = CompatibilityRegistry().assess(Game.ATS, GameVersion("1.61"))
    session = GarageEditorSession(service.load(game, assessment))
    assert session.garages == ("garage.stable",)
    session.set_status(service, game, "garage.stable", 2)
    assert "status: 2" in game.read_text(encoding="utf-8")


def test_garage_session_blocks_unknown_before_backup(tmp_path) -> None:
    game = tmp_path / "game.sii"
    game.write_text(SAVE[:-2] + "garage : garage.stable {\n status: 1\n}\n}\n", encoding="utf-8")
    session = GarageEditorSession(
        EditorService().load(game, CompatibilityRegistry().assess(Game.ATS, None))
    )
    with pytest.raises(CompatibilityWriteBlockedError):
        session.set_status(EditorService(), game, "garage.stable", 2)
    assert not tuple(tmp_path.glob("game.sii.tsse-backup-*"))
