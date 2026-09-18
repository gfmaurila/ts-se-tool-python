from pathlib import Path

import pytest

from tsse.core.sii import SiiParseError, parse_sii


def test_preserves_order_ids_lists_references_and_unknown_fields() -> None:
    source = (
        "SiiNunit\r\n{\r\nplayer : player.01 {\r\n"
        "  truck: vehicle.abc\r\n  tags[0]: \"one\"\r\n"
        "  tags[1]: \"two\"\r\n  future_field: token value\r\n}\r\n}\r\n"
    )

    document = parse_sii(source)

    block = document.blocks[0]
    assert (block.type_name, block.identifier) == ("player", "player.01")
    assert [field.key for field in block.fields] == ["truck", "tags[0]", "tags[1]", "future_field"]
    assert [field.array_index for field in block.fields] == [None, 0, 1, None]
    assert document.serialize() == source


def test_golden_plaintext_fixture_round_trips_byte_for_byte() -> None:
    fixture = Path("samples/ETS/4D4150415F455453/save/autosave/game_TB_decrypted.sii")
    source = fixture.read_bytes().decode("utf-8")

    document = parse_sii(source)

    assert len(document.blocks) > 1
    assert document.serialize().encode("utf-8") == fixture.read_bytes()


@pytest.mark.parametrize(
    "source, message",
    [
        ("not sii\n", "header"),
        ("SiiNunit\n{\nplayer : id {\n", "unterminated"),
        ("SiiNunit\nplayer : id {\n}\n", "braces"),
    ],
)
def test_invalid_documents_raise_typed_errors(source: str, message: str) -> None:
    with pytest.raises(SiiParseError, match=message):
        parse_sii(source)
