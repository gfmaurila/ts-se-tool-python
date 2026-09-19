
from tsse.application import CurrentSaveContext, EditorService
from tsse.application.compatibility import CompatibilityRegistry, GameVersion
from tsse.core.profiles import Game, Profile, SaveSlot


def test_context_retains_editor_assessment_and_creates_garage_session(tmp_path) -> None:
    game_sii = tmp_path / "game.sii"
    game_sii.write_text("SiiNunit\n{\ngarage : garage.one {\n status: 1\n}\n}\n", encoding="utf-8")
    slot = SaveSlot("save", game_sii.parent, game_sii)
    profile = Profile(Game.ATS, "profile", tmp_path, tmp_path / "profile.sii", (), False)
    editor = EditorService()
    assessment = CompatibilityRegistry().assess(Game.ATS, GameVersion("1.61"))
    context = CurrentSaveContext(
        Game.ATS,
        profile,
        slot,
        assessment,
        editor,
        editor.load(game_sii, assessment),
    )
    assert context.editor is editor
    assert context.assessment is assessment
    assert context.garage_session().garages == ("garage.one",)
