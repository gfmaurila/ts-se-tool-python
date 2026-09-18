from tsse.application.garage_editor import find_garage, set_garage_status
from tsse.core.sii import parse_sii

SOURCE = """SiiNunit
{
garage : garage.one {
 vehicles: 5
 status: 1
 unknown_future: keep
}
garage : garage.two {
 status: 3
}
}
"""


def test_status_edit_is_scoped_and_lossless_for_unknown_fields() -> None:
    edited = set_garage_status(parse_sii(SOURCE), "garage.one", 2)

    assert find_garage(edited, "garage.one").status == 2
    assert "unknown_future: keep" in edited.serialize()
    assert "garage : garage.two {\n status: 3" in edited.serialize()
    assert parse_sii(edited.serialize()).serialize() == edited.serialize()
