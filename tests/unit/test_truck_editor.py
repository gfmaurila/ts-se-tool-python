import pytest

from tsse.application.truck_editor import (
    TruckComponent,
    TruckEditError,
    find_truck,
    refuel_truck,
    repair_truck,
    repair_truck_component,
    set_condition,
)
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


REPAIR_SOURCE = """SiiNunit
{
vehicle : truck.repair {
 engine_wear: &3f000000
 transmission_wear: 0.4
 chassis_wear: 0.3
 cabin_wear: 0.2
 wheels_wear: 2
 wheels_wear[0]: 0.5
 wheels_wear[1]: 0.6
 fuel_relative: 0.25
 license_plate: \"KEEP|country\"
 odometer: 123
 odometer_float_part: &3e000000
 accessories: 1
 accessories[0]: accessory.keep
 unknown_future: preserve
}
}
"""


def _block_values(source: str) -> dict[str, str]:
    block = parse_sii(source).blocks[0]
    return {field.key: field.value for field in block.fields}


def test_total_repair_matches_legacy_and_preserves_unrelated_fields() -> None:
    edited = repair_truck(parse_sii(REPAIR_SOURCE), "truck.repair")
    values = _block_values(edited.serialize())

    fields = ("engine_wear", "transmission_wear", "chassis_wear", "cabin_wear")
    assert [values[key] for key in fields] == [
        "0",
        "0",
        "0",
        "0",
    ]
    assert values["wheels_wear"] == "0"
    assert not any(key.startswith("wheels_wear[") for key in values)
    assert values["fuel_relative"] == "0.25"
    assert values["license_plate"] == '"KEEP|country"'
    assert values["odometer"] == "123"
    assert values["odometer_float_part"] == "&3e000000"
    assert values["accessories[0]"] == "accessory.keep"
    assert values["unknown_future"] == "preserve"
    assert parse_sii(edited.serialize()).serialize() == edited.serialize()


@pytest.mark.parametrize(
    ("component", "expected_field"),
    [
        (TruckComponent.ENGINE, "engine_wear"),
        (TruckComponent.TRANSMISSION, "transmission_wear"),
        (TruckComponent.CHASSIS, "chassis_wear"),
        (TruckComponent.CABIN, "cabin_wear"),
        (TruckComponent.WHEELS, "wheels_wear"),
    ],
)
def test_individual_repair_targets_only_the_legacy_selected_component(
    component: TruckComponent, expected_field: str
) -> None:
    edited = repair_truck_component(parse_sii(REPAIR_SOURCE), "truck.repair", component)
    values = _block_values(edited.serialize())

    assert values[expected_field] == "0"
    if component is TruckComponent.WHEELS:
        assert not any(key.startswith("wheels_wear[") for key in values)
        assert values["engine_wear"] == "&3f000000"
    else:
        assert values["wheels_wear[0]"] == "0.5"
        assert values["wheels_wear[1]"] == "0.6"
        for key in {"engine_wear", "transmission_wear", "chassis_wear", "cabin_wear"} - {
            expected_field
        }:
            assert values[key] == _block_values(REPAIR_SOURCE)[key]
    assert values["unknown_future"] == "preserve"


def test_invalid_component_and_invalid_wheel_array_do_not_mutate_source() -> None:
    document = parse_sii(REPAIR_SOURCE)
    with pytest.raises(TruckEditError, match="unsupported"):
        repair_truck_component(document, "truck.repair", "tyre")  # type: ignore[arg-type]
    assert document.serialize() == REPAIR_SOURCE

    inconsistent = REPAIR_SOURCE.replace("wheels_wear: 2", "wheels_wear: 3")
    broken_document = parse_sii(inconsistent)
    with pytest.raises(TruckEditError, match="inconsistent"):
        repair_truck(broken_document, "truck.repair")
    assert broken_document.serialize() == inconsistent


def test_refuel_matches_legacy_without_repairing_parts() -> None:
    edited = refuel_truck(parse_sii(REPAIR_SOURCE), "truck.repair")
    values = _block_values(edited.serialize())

    assert values["fuel_relative"] == "1"
    assert values["engine_wear"] == "&3f000000"
    assert values["transmission_wear"] == "0.4"
    assert values["chassis_wear"] == "0.3"
    assert values["cabin_wear"] == "0.2"
    assert values["wheels_wear[0]"] == "0.5"
    assert values["wheels_wear[1]"] == "0.6"
    assert values["license_plate"] == '"KEEP|country"'
    assert values["odometer"] == "123"
    assert values["accessories[0]"] == "accessory.keep"
    assert values["unknown_future"] == "preserve"
    assert parse_sii(edited.serialize()).serialize() == edited.serialize()


def test_truck_operations_raise_typed_errors_for_missing_vehicle_or_field() -> None:
    with pytest.raises(TruckEditError, match="missing vehicle"):
        refuel_truck(parse_sii(REPAIR_SOURCE), "truck.missing")
    missing_fuel = REPAIR_SOURCE.replace(" fuel_relative: 0.25\n", "")
    with pytest.raises(TruckEditError, match="missing vehicle.fuel_relative"):
        refuel_truck(parse_sii(missing_fuel), "truck.repair")
