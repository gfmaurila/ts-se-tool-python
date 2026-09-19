"""Read-only typed driver relationships proven by the legacy company view."""

from __future__ import annotations

from dataclasses import dataclass

from tsse.core.sii import ReferenceResolutionError, SiiBlock, SiiDocument, SiiGraph


class DriverGraphError(ValueError):
    """A legacy driver relationship is absent, malformed, or has a wrong type."""


@dataclass(frozen=True, slots=True)
class DriverView:
    """Lossless projection of fields parsed by legacy ``Driver_AI``."""

    identifier: str
    adr: str | None
    long_dist: str | None
    heavy: str | None
    fragile: str | None
    urgent: str | None
    mechanical: str | None
    experience_points: str | None
    training_policy: str | None
    assigned_truck: str | None
    assigned_trailer: str | None
    garage: str | None


def resolve_player_driver(document: SiiDocument, index: int) -> SiiBlock:
    """Resolve a typed ``player.drivers[index]`` relation without mutation."""
    players = [block for block in document.blocks if block.type_name == "player"]
    if len(players) != 1:
        raise DriverGraphError(f"expected exactly one player, found {len(players)}")
    graph = SiiGraph(document)
    references = dict(
        graph.indexed_references(players[0], "drivers", ("driver_ai", "driver_player"))
    )
    try:
        reference = references[index]
        target = graph.resolve(reference)
    except KeyError as error:
        raise DriverGraphError(f"driver index does not exist: {index}") from error
    except ReferenceResolutionError as error:
        raise DriverGraphError(str(error)) from error
    if target is None:
        raise DriverGraphError(f"driver reference is null: {index}")
    return target


def resolve_driver_truck(document: SiiDocument, driver: SiiBlock) -> SiiBlock | None:
    """Resolve ``driver_ai.assigned_truck`` where the field exists."""
    if driver.type_name != "driver_ai":
        raise DriverGraphError(f"driver is not driver_ai: {driver.identifier}")
    try:
        return SiiGraph(document).resolve(
            SiiGraph(document).field_reference(driver, "assigned_truck", "vehicle")
        )
    except ReferenceResolutionError as error:
        raise DriverGraphError(str(error)) from error


def driver_garage(document: SiiDocument, driver: SiiBlock) -> SiiBlock | None:
    """Return the one garage whose indexed ``drivers`` list contains this driver."""
    matches = [
        garage
        for garage in document.blocks
        if garage.type_name == "garage"
        if any(
            field.name == "drivers"
            and field.array_index is not None
            and field.value == driver.identifier
            for field in garage.fields
        )
    ]
    if len(matches) > 1:
        raise DriverGraphError(f"driver belongs to multiple garages: {driver.identifier}")
    return matches[0] if matches else None


def build_driver_view(document: SiiDocument, driver: SiiBlock) -> DriverView:
    """Build a side-effect-free legacy driver projection."""
    if driver.type_name != "driver_ai":
        raise DriverGraphError(f"driver is not driver_ai: {driver.identifier}")
    values = {field.key: field.value for field in driver.fields}
    garage = driver_garage(document, driver)
    return DriverView(
        identifier=driver.identifier,
        adr=values.get("adr"),
        long_dist=values.get("long_dist"),
        heavy=values.get("heavy"),
        fragile=values.get("fragile"),
        urgent=values.get("urgent"),
        mechanical=values.get("mechanical"),
        experience_points=values.get("experience_points"),
        training_policy=values.get("training_policy"),
        assigned_truck=values.get("assigned_truck"),
        assigned_trailer=values.get("assigned_trailer"),
        garage=garage.identifier if garage else None,
    )
