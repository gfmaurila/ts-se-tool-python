import pytest

from tsse.application.garage_relocation import (
    GarageRelocationError,
    RemovedGarageItems,
    move_driver_out,
    move_drivers_in,
    move_vehicle_out,
    move_vehicles_in,
    resolve_garage,
    sell_garage,
)
from tsse.core.sii import parse_sii

SOURCE = """SiiNunit
{
economy : economy.1 {
 garages: 2
 garages[0]: garage.a
 garages[1]: garage.b
 driver_pool: 1
 driver_pool[0]: driver.pool
}
garage : garage.a {
 status: 0
 drivers: 3
 drivers[0]: driver.player
 drivers[1]: null
 drivers[2]: driver.ai
 vehicles: 3
 vehicles[0]: vehicle.a
 vehicles[1]: null
 vehicles[2]: vehicle.b
 trailers: 1
 trailers[0]: trailer.keep
 unknown_garage: keep
}
garage : garage.b {
 status: 3
 drivers: 2
 drivers[0]: null
 drivers[1]: driver.pool
 vehicles: 2
 vehicles[0]: null
 vehicles[1]: vehicle.c
 trailers: 1
 trailers[0]: trailer.keep
}
driver_player : driver.player {
 unknown_driver: keep
}
driver_ai : driver.ai {
 unknown_driver: keep
}
driver_ai : driver.pool {
 unknown_driver: keep
}
vehicle : vehicle.a {
 unknown_vehicle: keep
}
vehicle : vehicle.b {
 unknown_vehicle: keep
}
vehicle : vehicle.c {
 unknown_vehicle: keep
}
trailer : trailer.keep {
 unknown_trailer: keep
}
}
"""


def _collection(text: str, garage: str, name: str) -> list[str]:
    block = next(item for item in parse_sii(text).blocks if item.identifier == garage)
    return [
        field.value
        for field in block.fields
        if field.name == name and field.array_index is not None
    ]


def test_driver_out_and_in_preserve_slots_and_unknowns() -> None:
    out, removed = move_driver_out(parse_sii(SOURCE), "garage.a", 0)
    edited, remaining = move_drivers_in(out, removed)

    assert _collection(edited.serialize(), "garage.a", "drivers") == ["null", "null", "driver.ai"]
    assert _collection(edited.serialize(), "garage.b", "drivers") == [
        "driver.player",
        "driver.pool",
    ]
    assert remaining.drivers == (None,)
    assert "unknown_driver: keep" in edited.serialize()
    assert "unknown_garage: keep" in edited.serialize()
    assert parse_sii(edited.serialize()).serialize() == edited.serialize()


def test_vehicle_out_and_in_preserve_order_trailers_and_vehicle_block() -> None:
    out, removed = move_vehicle_out(parse_sii(SOURCE), "garage.a", 2)
    edited, remaining = move_vehicles_in(out, removed)

    assert _collection(edited.serialize(), "garage.a", "vehicles") == ["vehicle.a", "null", "null"]
    assert _collection(edited.serialize(), "garage.b", "vehicles") == ["vehicle.b", "vehicle.c"]
    assert _collection(edited.serialize(), "garage.a", "trailers") == ["trailer.keep"]
    assert remaining.vehicles == (None,)
    assert "unknown_vehicle: keep" in edited.serialize()


@pytest.mark.parametrize(
    "source, function, args",
    [
        (SOURCE, move_driver_out, ("garage.a", 1)),
        (
            SOURCE.replace("driver_player : driver.player", "vehicle : driver.player"),
            move_driver_out,
            ("garage.a", 0),
        ),
        (
            SOURCE.replace("vehicle : vehicle.a", "driver_ai : vehicle.a"),
            move_vehicle_out,
            ("garage.a", 0),
        ),
    ],
)
def test_invalid_out_operations_are_typed_and_do_not_mutate(
    source: str, function: object, args: tuple[object, ...]
) -> None:
    document = parse_sii(source)
    with pytest.raises(GarageRelocationError):
        function(document, *args)  # type: ignore[operator]
    assert document.serialize() == source


def test_missing_reference_and_inconsistent_collection_are_rejected() -> None:
    missing = parse_sii(SOURCE.replace("driver.player", "driver.missing", 1))
    with pytest.raises(GarageRelocationError, match="missing"):
        move_driver_out(missing, "garage.a", 0)
    inconsistent = parse_sii(SOURCE.replace("vehicles: 3", "vehicles: 2", 1))
    with pytest.raises(GarageRelocationError, match="inconsistent"):
        move_vehicle_out(inconsistent, "garage.a", 0)


def test_driver_pool_zero_is_only_protected_by_the_legacy_out_handler() -> None:
    document = parse_sii(SOURCE)
    unchanged, removed = move_driver_out(document, "garage.b", 1)
    assert unchanged is document
    assert removed == RemovedGarageItems()


def test_in_without_space_is_legacy_noop_and_preserves_transient_item() -> None:
    source = SOURCE.replace("drivers[0]: null", "drivers[0]: driver.ai")
    document = parse_sii(source)
    unchanged, removed = move_drivers_in(document, RemovedGarageItems(("driver.player",), (None,)))
    assert unchanged is document
    assert removed.drivers == ("driver.player",)


def test_resolver_rejects_unreferenced_or_wrong_type_garages() -> None:
    document = parse_sii(SOURCE)
    with pytest.raises(GarageRelocationError):
        resolve_garage(document, "garage.missing")
    wrong = parse_sii(SOURCE.replace("garage : garage.b", "vehicle : garage.b"))
    with pytest.raises(GarageRelocationError, match="unexpected"):
        resolve_garage(wrong, "garage.b")


def test_sale_applies_legacy_status_capacity_and_transfers_trailers() -> None:
    edited = sell_garage(parse_sii(SOURCE), "garage.a", "garage.b")
    text = edited.serialize()
    garage_a = next(block for block in edited.blocks if block.identifier == "garage.a")
    economy = next(block for block in edited.blocks if block.type_name == "economy")

    assert next(field.value for field in garage_a.fields if field.key == "status") == "0"
    assert _collection(text, "garage.a", "drivers") == []
    assert _collection(text, "garage.a", "vehicles") == []
    assert _collection(text, "garage.a", "trailers") == []
    assert _collection(text, "garage.b", "drivers") == [
        "null", "driver.pool", "null", "null", "null"
    ]
    assert _collection(text, "garage.b", "vehicles") == [
        "null", "vehicle.c", "null", "null", "null"
    ]
    assert _collection(text, "garage.b", "trailers") == ["trailer.keep", "trailer.keep"]
    assert _collection(text, economy.identifier, "driver_pool") == [
        "driver.pool", "driver.player", "driver.ai"
    ]
    assert "unknown_garage: keep" in text
    assert "unknown_driver: keep" in text
    assert parse_sii(text).serialize() == text


def test_sale_hq_keeps_tiny_status_and_swaps_protected_pool_driver() -> None:
    edited = sell_garage(parse_sii(SOURCE), "garage.b", "garage.b")
    text = edited.serialize()
    garage_b = next(block for block in edited.blocks if block.identifier == "garage.b")
    assert next(field.value for field in garage_b.fields if field.key == "status") == "6"
    assert _collection(text, "garage.b", "drivers") == ["driver.pool"]
    assert _collection(text, "garage.b", "vehicles") == ["vehicle.c"]
    assert _collection(text, "garage.b", "trailers") == ["trailer.keep", "trailer.keep"]
    assert _collection(text, "economy.1", "driver_pool") == [
        "driver.pool", "driver.player", "driver.ai"
    ]


def test_sale_is_transactional_for_misaligned_driver_vehicle_slots() -> None:
    source = SOURCE.replace("vehicles: 3", "vehicles: 2", 1)
    document = parse_sii(source)
    with pytest.raises(GarageRelocationError, match="inconsistent|differ"):
        sell_garage(document, "garage.a", "garage.b")
    assert document.serialize() == source
