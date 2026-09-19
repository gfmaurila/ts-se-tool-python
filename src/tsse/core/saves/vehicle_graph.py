"""Typed, read-only relationships used by the legacy vehicle and trailer tabs."""

from __future__ import annotations

from tsse.core.sii import (
    ReferenceResolutionError,
    SiiBlock,
    SiiDocument,
    SiiGraph,
    TypedUnitReference,
)

_ACCESSORY_TYPES = (
    "vehicle_accessory",
    "vehicle_wheel_accessory",
    "vehicle_addon_accessory",
    "vehicle_paint_job_accessory",
)


class VehicleGraphError(ValueError):
    """A proven vehicle/trailer relationship cannot be resolved safely."""


def resolve_assigned_truck(document: SiiDocument) -> SiiBlock | None:
    """Resolve legacy ``player.assigned_truck`` as a ``vehicle`` or explicit null."""
    return _resolve_player_reference(document, "assigned_truck", "vehicle")


def resolve_assigned_trailer(document: SiiDocument) -> SiiBlock | None:
    """Resolve legacy ``player.assigned_trailer`` as a ``trailer`` or explicit null."""
    return _resolve_player_reference(document, "assigned_trailer", "trailer")


def resolve_vehicle(document: SiiDocument, identifier: str) -> SiiBlock:
    """Resolve one vehicle block by ID without accepting another unit type."""
    return _unit_of_type(SiiGraph(document), identifier, "vehicle")


def resolve_trailer(document: SiiDocument, identifier: str) -> SiiBlock:
    """Resolve one trailer block by ID without accepting another unit type."""
    return _unit_of_type(SiiGraph(document), identifier, "trailer")


def resolve_trailer_chain(document: SiiDocument, identifier: str) -> tuple[SiiBlock, ...]:
    """Follow the legacy ``trailer.slave_trailer`` chain with typed resolution."""
    graph = SiiGraph(document)
    current = _unit_of_type(graph, identifier, "trailer")
    chain: list[SiiBlock] = []
    visited: set[str] = set()
    while True:
        if current.identifier in visited:
            raise VehicleGraphError(f"slave_trailer cycle at: {current.identifier}")
        visited.add(current.identifier)
        chain.append(current)
        try:
            target = graph.resolve(graph.field_reference(current, "slave_trailer", "trailer"))
        except ReferenceResolutionError as error:
            raise VehicleGraphError(str(error)) from error
        if target is None:
            return tuple(chain)
        current = target


def resolve_accessories(
    document: SiiDocument, owner: SiiBlock
) -> tuple[tuple[int, SiiBlock | None], ...]:
    """Resolve indexed vehicle/trailer accessories with the known legacy types."""
    graph = SiiGraph(document)
    resolved: list[tuple[int, SiiBlock | None]] = []
    for index, reference in graph.indexed_references(owner, "accessories", _ACCESSORY_TYPES):
        try:
            target = graph.resolve(reference)
        except ReferenceResolutionError as error:
            raise VehicleGraphError(str(error)) from error
        resolved.append((index, target))
    return tuple(resolved)


def inspect_accessories(
    document: SiiDocument, owner: SiiBlock
) -> tuple[tuple[int, TypedUnitReference, SiiBlock | None], ...]:
    """Inspect accessory links without raising, preserving missing/unknown evidence for views."""
    graph = SiiGraph(document)
    result: list[tuple[int, TypedUnitReference, SiiBlock | None]] = []
    for index, reference in graph.indexed_references(owner, "accessories"):
        resolution = graph.inspect(reference)
        result.append((index, reference, resolution.target))
    return tuple(result)


def _resolve_player_reference(
    document: SiiDocument, field_name: str, expected_type: str
) -> SiiBlock | None:
    players = [block for block in document.blocks if block.type_name == "player"]
    if len(players) != 1:
        raise VehicleGraphError(f"expected exactly one player, found {len(players)}")
    graph = SiiGraph(document)
    try:
        return graph.resolve(graph.field_reference(players[0], field_name, expected_type))
    except ReferenceResolutionError as error:
        raise VehicleGraphError(str(error)) from error


def _unit_of_type(graph: SiiGraph, identifier: str, expected_type: str) -> SiiBlock:
    try:
        target = graph.unit(identifier)
        if target.type_name != expected_type:
            raise VehicleGraphError(
                f"expected {expected_type}, found {target.type_name}: {identifier}"
            )
        return target
    except ReferenceResolutionError as error:
        raise VehicleGraphError(str(error)) from error
