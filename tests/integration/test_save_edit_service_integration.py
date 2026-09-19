from pathlib import Path

import pytest

from tsse.application.player_editor import set_skill
from tsse.application.save_edit_service import SaveEditService
from tsse.core.sii import SaveFormat, parse_sii


@pytest.mark.parametrize(
    "fixture",
    [
        Path("projeto_atual/ATS/67666D617572696C61202D207A657261646F/save/autosave/game.sii"),
        Path("projeto_atual/ETS/4D4150415F455453/save/autosave/game.sii"),
    ],
)
def test_real_161_fixture_is_written_as_plaintext_siin_without_mutating_source(
    fixture: Path, tmp_path: Path
) -> None:
    original = fixture.read_bytes()
    game = tmp_path / "game.sii"
    game.write_bytes(original)

    result = SaveEditService().save(game, lambda document: set_skill(document, "adr", 1))

    document = parse_sii(game.read_text(encoding="utf-8"))
    economy = next(block for block in document.blocks if block.type_name == "economy")
    assert result.original_format is SaveFormat.SCS_CONTAINER
    assert game.read_bytes().startswith(b"SiiNunit")
    assert next(field.value for field in economy.fields if field.key == "adr") == "1"
    assert fixture.read_bytes() == original
