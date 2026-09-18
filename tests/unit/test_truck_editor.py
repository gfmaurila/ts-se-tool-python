from tsse.application.truck_editor import find_truck, set_condition
from tsse.core.sii import parse_sii

SOURCE = """SiiNunit
{
vehicle : truck.one {
 engine_wear: 5
 transmission_wear: 4
 cabin_wear: 3
 fuel_relative: 0.5
 future_field: keep
}
vehicle : truck.two {
 engine_wear: 1
 transmission_wear: 1
 cabin_wear: 1
 fuel_relative: 1
}
}
"""


def test_condition_edit_targets_one_truck_and_preserves_unknown_fields() -> None:
    edited = set_condition(parse_sii(SOURCE), "truck.one", 0, 1.0)

    truck = find_truck(edited, "truck.one")
    assert (truck.engine_wear, truck.transmission_wear, truck.cabin_wear) == (0, 0, 0)
    assert truck.fuel_relative == 1.0
    assert "future_field: keep" in edited.serialize()
    assert "vehicle : truck.two {\n engine_wear: 1" in edited.serialize()
    assert parse_sii(edited.serialize()).serialize() == edited.serialize()
