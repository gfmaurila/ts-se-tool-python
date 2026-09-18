from tsse.application.trailer_editor import find_trailer, repair_trailer
from tsse.core.sii import parse_sii

SOURCE = """SiiNunit
{
trailer : trailer.one {
 cargo_damage: 0.5
 trailer_body_wear: 0.2
 chassis_wear: 0.1
 unknown_future: preserve
}
trailer : trailer.two {
 cargo_damage: 1
 trailer_body_wear: 1
 chassis_wear: 1
}
}
"""


def test_repair_targets_selected_trailer_and_preserves_unknown_content() -> None:
    edited = repair_trailer(parse_sii(SOURCE), "trailer.one")

    trailer = find_trailer(edited, "trailer.one")
    assert (trailer.cargo_damage, trailer.body_wear, trailer.chassis_wear) == (0.0, 0.0, 0.0)
    assert "unknown_future: preserve" in edited.serialize()
    assert "trailer : trailer.two {\n cargo_damage: 1" in edited.serialize()
    assert parse_sii(edited.serialize()).serialize() == edited.serialize()
