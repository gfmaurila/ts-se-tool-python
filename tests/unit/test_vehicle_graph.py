import pytest

from tsse.core.saves.vehicle_graph import (
    VehicleGraphError,
    resolve_accessories,
    resolve_assigned_trailer,
    resolve_assigned_truck,
    resolve_trailer_chain,
)
from tsse.core.sii import parse_sii

SOURCE = """SiiNunit
{
player : player.one {
 assigned_truck: vehicle.one
 assigned_trailer: trailer.one
}
vehicle : vehicle.one {
 accessories: 2
 accessories[0]: accessory.engine
 accessories[1]: null
}
trailer : trailer.one {
 slave_trailer: trailer.two
}
trailer : trailer.two {
 slave_trailer: null
}
vehicle_accessory : accessory.engine {
 data_path: "/def/vehicle/truck/engine.sii"
}
}
"""


def test_resolves_assigned_units_and_indexed_accessories_without_mutation() -> None:
    document = parse_sii(SOURCE)
    original = document.serialize()

    assert resolve_assigned_truck(document).identifier == "vehicle.one"  # type: ignore[union-attr]
    assert resolve_assigned_trailer(document).identifier == "trailer.one"  # type: ignore[union-attr]
    vehicle = resolve_assigned_truck(document)
    assert vehicle is not None
    accessories = [
        (index, block.identifier if block else None)
        for index, block in resolve_accessories(document, vehicle)
    ]
    assert accessories == [
        (0, "accessory.engine"),
        (1, None),
    ]
    assert [block.identifier for block in resolve_trailer_chain(document, "trailer.one")] == [
        "trailer.one",
        "trailer.two",
    ]
    assert document.serialize() == original


@pytest.mark.parametrize(
    ("replacement", "message"),
    [
        ("assigned_truck: missing.vehicle", "missing SII unit reference"),
        ("assigned_truck: trailer.one", "expected vehicle"),
        ('assigned_truck: "vehicle.one"', "malformed"),
    ],
)
def test_assigned_truck_rejects_missing_wrong_and_malformed_references(
    replacement: str, message: str
) -> None:
    document = parse_sii(SOURCE.replace("assigned_truck: vehicle.one", replacement))

    with pytest.raises(VehicleGraphError, match=message):
        resolve_assigned_truck(document)


def test_accessories_reject_missing_and_wrong_component_types() -> None:
    vehicle = resolve_assigned_truck(parse_sii(SOURCE))
    assert vehicle is not None
    missing = parse_sii(SOURCE.replace("accessory.engine", "accessory.missing", 1))
    with pytest.raises(VehicleGraphError, match="missing SII unit reference"):
        resolve_accessories(missing, resolve_assigned_truck(missing))  # type: ignore[arg-type]

    wrong = parse_sii(
        SOURCE.replace("vehicle_accessory : accessory.engine", "trailer : accessory.engine")
    )
    with pytest.raises(VehicleGraphError, match="expected vehicle_accessory"):
        resolve_accessories(wrong, resolve_assigned_truck(wrong))  # type: ignore[arg-type]
