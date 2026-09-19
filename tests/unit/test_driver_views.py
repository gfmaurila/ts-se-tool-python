import pytest

from tsse.core.saves.drivers import (
    DriverGraphError,
    build_driver_view,
    driver_garage,
    resolve_driver_truck,
    resolve_player_driver,
)
from tsse.core.sii import parse_sii

SOURCE = """SiiNunit
{
player : player.one {
 drivers: 1
 drivers[0]: driver.ai
}
garage : garage.one {
 drivers: 1
 drivers[0]: driver.ai
}
driver_ai : driver.ai {
 adr: 2
 long_dist: 3
 heavy: 4
 fragile: 5
 urgent: 6
 mechanical: 1
 experience_points: 100
 training_policy: 2
 assigned_truck: vehicle.one
 assigned_trailer: null
 future: preserve
}
vehicle : vehicle.one {
 future: preserve
}
}
"""


def test_driver_graph_and_view_are_typed_and_side_effect_free() -> None:
    document = parse_sii(SOURCE)
    original = document.serialize()
    driver = resolve_player_driver(document, 0)
    view = build_driver_view(document, driver)

    assert driver.identifier == "driver.ai"
    assert resolve_driver_truck(document, driver).identifier == "vehicle.one"  # type: ignore[union-attr]
    assert driver_garage(document, driver).identifier == "garage.one"  # type: ignore[union-attr]
    assert (view.adr, view.experience_points, view.garage) == ("2", "100", "garage.one")
    assert document.serialize() == original


@pytest.mark.parametrize(
    ("source", "message"),
    [
        (
            SOURCE.replace("drivers[0]: driver.ai", "drivers[0]: missing.driver", 1),
            "missing SII unit reference",
        ),
        (
            SOURCE.replace("drivers[0]: driver.ai", "drivers[0]: vehicle.one", 1),
            "expected driver_ai",
        ),
        (SOURCE.replace("drivers[0]: driver.ai", 'drivers[0]: "driver.ai"', 1), "malformed"),
    ],
)
def test_driver_reference_errors_are_explicit(source: str, message: str) -> None:
    with pytest.raises(DriverGraphError, match=message):
        resolve_player_driver(parse_sii(source), 0)


def test_driver_assignment_wrong_type_and_duplicate_garage_are_rejected() -> None:
    wrong = parse_sii(SOURCE.replace("vehicle : vehicle.one", "trailer : vehicle.one"))
    with pytest.raises(DriverGraphError, match="expected vehicle"):
        resolve_driver_truck(wrong, resolve_player_driver(wrong, 0))

    duplicate = parse_sii(
        SOURCE.replace(
            "}\nvehicle : vehicle.one",
            "}\n"
            "garage : garage.two {\n drivers: 1\n drivers[0]: driver.ai\n}\n"
            "vehicle : vehicle.one",
        )
    )
    with pytest.raises(DriverGraphError, match="multiple garages"):
        driver_garage(duplicate, resolve_player_driver(duplicate, 0))
