"""Literal, in-memory garage slot moves from the legacy sale-content form."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import cast

from tsse.core.sii import SiiBlock, SiiDocument, parse_sii


class GarageRelocationError(ValueError):
    """Raised for invalid garage links, slots, or item references."""


class GarageSaleError(GarageRelocationError):
    """Raised when the legacy garage-sale preparation cannot be applied safely."""


_EMPTY = frozenset({"", "null", "nil"})


@dataclass(frozen=True)
class RemovedGarageItems:
    """The legacy form's transient parallel removed-item lists."""

    drivers: tuple[str | None, ...] = ()
    vehicles: tuple[str | None, ...] = ()

    def add_driver(self, reference: str) -> RemovedGarageItems:
        return RemovedGarageItems(self.drivers + (reference,), self.vehicles + (None,))

    def add_vehicle(self, reference: str) -> RemovedGarageItems:
        return RemovedGarageItems(self.drivers + (None,), self.vehicles + (reference,))


def resolve_garage(document: SiiDocument, identifier: str) -> SiiBlock:
    """Resolve one `economy.garages[]` reference to a real garage block."""
    economy = _single_block(document, "economy")
    garage_ids = _collection(economy, "garages")
    if identifier not in garage_ids:
        raise GarageRelocationError(f"garage is not referenced by economy: {identifier}")
    block = _blocks(document).get(identifier)
    if block is None:
        raise GarageRelocationError(f"garage reference is missing: {identifier}")
    if block.type_name != "garage":
        raise GarageRelocationError(f"garage reference has unexpected type: {block.type_name}")
    return block


def move_driver_out(
    document: SiiDocument,
    garage_identifier: str,
    slot: int,
    removed: RemovedGarageItems | None = None,
) -> tuple[SiiDocument, RemovedGarageItems]:
    """Port `buttonMoveDriversOut_Click`: clear a slot and retain transient data."""
    removed = removed or RemovedGarageItems()
    garage = resolve_garage(document, garage_identifier)
    drivers = _collection(garage, "drivers")
    reference = _slot(drivers, slot, "driver")
    _resolve_driver(document, reference)
    pool = _collection(_single_block(document, "economy"), "driver_pool", required=False)
    if pool and reference == pool[0]:
        return document, removed
    updated = list(drivers)
    updated[slot] = "null"
    return _replace_collections(
        document, {(garage.identifier, "drivers"): updated}
    ), removed.add_driver(reference)


def move_vehicle_out(
    document: SiiDocument,
    garage_identifier: str,
    slot: int,
    removed: RemovedGarageItems | None = None,
) -> tuple[SiiDocument, RemovedGarageItems]:
    """Port `buttonMoveTrucksOut_Click`: clear only the selected vehicle slot."""
    removed = removed or RemovedGarageItems()
    garage = resolve_garage(document, garage_identifier)
    vehicles = _collection(garage, "vehicles")
    reference = _slot(vehicles, slot, "vehicle")
    _resolve_vehicle(document, reference)
    updated = list(vehicles)
    updated[slot] = "null"
    return _replace_collections(
        document, {(garage.identifier, "vehicles"): updated}
    ), removed.add_vehicle(reference)


def move_drivers_in(
    document: SiiDocument, removed: RemovedGarageItems
) -> tuple[SiiDocument, RemovedGarageItems]:
    """Port the legacy handler's first-selected-driver / all-free-slots behavior."""
    reference = next((item for item in removed.drivers if item is not None), None)
    if reference is None:
        return document, removed
    _resolve_driver(document, reference)
    changes: dict[tuple[str, str], list[str]] = {}
    for garage in _garages(document):
        if _status(garage) == "0":
            continue
        slots = _collection(garage, "drivers")
        if any(value in _EMPTY for value in slots):
            changes[(garage.identifier, "drivers")] = [
                reference if value in _EMPTY else value for value in slots
            ]
    if not changes:
        return document, removed
    next_drivers = tuple(None if value == reference else value for value in removed.drivers)
    return _replace_collections(document, changes), RemovedGarageItems(
        next_drivers, removed.vehicles
    )


def move_vehicles_in(
    document: SiiDocument, removed: RemovedGarageItems
) -> tuple[SiiDocument, RemovedGarageItems]:
    """Port legacy sequential placement into free slots of active garages."""
    queue = [item for item in removed.vehicles if item is not None]
    if not queue:
        return document, removed
    for reference in queue:
        _resolve_vehicle(document, reference)
    changes: dict[tuple[str, str], list[str]] = {}
    consumed: list[str] = []
    for garage in _garages(document):
        if _status(garage) == "0" or not queue:
            continue
        slots = _collection(garage, "vehicles")
        updated = list(slots)
        for index, value in enumerate(updated):
            if value in _EMPTY and queue:
                reference = queue.pop(0)
                updated[index] = reference
                consumed.append(reference)
        if updated != slots:
            changes[(garage.identifier, "vehicles")] = updated
    if not changes:
        return document, removed
    next_vehicles = tuple(None if value in consumed else value for value in removed.vehicles)
    return _replace_collections(document, changes), RemovedGarageItems(
        removed.drivers, next_vehicles
    )


def sell_garage(
    document: SiiDocument, garage_identifier: str, hq_identifier: str
) -> SiiDocument:
    """Apply the legacy Sell button plus ``PrepareGarages`` write preparation.

    The desktop UI changed the selected garage status and immediately normalized
    *all* garage lists to the legacy capacities: not-owned=0, small=3,
    large=5, and HQ/tiny=1.  This domain operation is intentionally atomic:
    it validates every referenced block and all paired lists before replacing
    any source text.
    """
    garages = _garages(document)
    by_id = {garage.identifier: garage for garage in garages}
    if garage_identifier not in by_id:
        raise GarageSaleError(f"garage is not referenced by economy: {garage_identifier}")
    if hq_identifier not in by_id:
        raise GarageSaleError(f"HQ garage is not referenced by economy: {hq_identifier}")

    state: dict[str, dict[str, list[str] | str]] = {}
    extra_drivers: list[str] = []
    extra_vehicles: list[str] = []
    extra_trailers: list[str] = []
    for garage in garages:
        status = "6" if garage.identifier == garage_identifier == hq_identifier else (
            "0" if garage.identifier == garage_identifier else _status(garage)
        )
        drivers = _collection(garage, "drivers")
        vehicles = _collection(garage, "vehicles")
        trailers = _collection(garage, "trailers")
        if len(drivers) != len(vehicles):
            raise GarageSaleError(
                f"garage driver/vehicle slots differ: {garage.identifier}"
            )
        state[garage.identifier] = {
            "status": status,
            "drivers": list(drivers),
            "vehicles": list(vehicles),
            "trailers": list(trailers),
        }

    # Literal DataManipulation.PrepareGarages capacity pass.
    capacities = {"2": 3, "3": 5, "6": 1}
    for garage in garages:
        current = state[garage.identifier]
        state_status = cast(str, current["status"])
        capacity = capacities.get(state_status, 0)
        drivers = cast(list[str], current["drivers"])
        vehicles = cast(list[str], current["vehicles"])
        trailers = cast(list[str], current["trailers"])
        if capacity == 0:
            extra_vehicles.extend(vehicles)
            extra_drivers.extend(drivers)
            extra_trailers.extend(trailers)
            current["vehicles"] = []
            current["drivers"] = []
            current["trailers"] = []
        elif capacity < len(vehicles):
            extra_vehicles.extend(vehicles[capacity:])
            extra_drivers.extend(drivers[capacity:])
            current["vehicles"] = vehicles[:capacity]
            current["drivers"] = drivers[:capacity]
        elif capacity > len(vehicles):
            pad = ["null"] * (capacity - len(vehicles))
            current["vehicles"] = vehicles + pad
            current["drivers"] = drivers + pad
        # PrepareGarages only clears trailers for capacity zero.  Unlike
        # driver/vehicle slots, it does not truncate trailers in active garages.

    hq = state[hq_identifier]
    hq_trailers = cast(list[str], hq["trailers"])
    hq["trailers"] = hq_trailers + extra_trailers

    # The legacy removes pairs whose references are equal (including null/null).
    kept_pairs = [
        (driver, vehicle)
        for driver, vehicle in zip(extra_drivers, extra_vehicles, strict=True)
        if driver != vehicle
    ]
    extra_drivers = [driver for driver, _vehicle in kept_pairs]
    extra_vehicles = [vehicle for _driver, vehicle in kept_pairs]

    economy = _single_block(document, "economy")
    driver_pool = _collection(economy, "driver_pool")
    if extra_drivers and driver_pool and driver_pool[0] in extra_drivers:
        hq_drivers = cast(list[str], hq["drivers"])
        hq_vehicles = cast(list[str], hq["vehicles"])
        free = next(
            (index for index, pair in enumerate(zip(hq_drivers, hq_vehicles, strict=True))
             if pair[0] in _EMPTY and pair[1] in _EMPTY),
            0,
        )
        if not hq_drivers:
            raise GarageSaleError("legacy HQ pool-driver swap has no HQ slot")
        extra_drivers.append(hq_drivers[free])
        extra_vehicles.append(hq_vehicles[free])
        pool_index = extra_drivers.index(driver_pool[0])
        hq_drivers[free] = extra_drivers[pool_index]
        hq_vehicles[free] = extra_vehicles[pool_index]
        del extra_drivers[pool_index]
        del extra_vehicles[pool_index]

    # PrepareDriversTrucksWrite appends non-null leftovers to driver_pool.
    final_pool = driver_pool + [driver for driver in extra_drivers if driver not in _EMPTY]
    changes: dict[tuple[str, str], str | list[str]] = {
        (identifier, name): value
        for identifier, values in state.items()
        for name, value in values.items()
    }
    changes[(economy.identifier, "driver_pool")] = final_pool
    return _replace_values(document, changes)


def _blocks(document: SiiDocument) -> dict[str, SiiBlock]:
    return {block.identifier: block for block in document.blocks}


def _single_block(document: SiiDocument, type_name: str) -> SiiBlock:
    matches = [block for block in document.blocks if block.type_name == type_name]
    if len(matches) != 1:
        raise GarageRelocationError(f"expected exactly one {type_name} block")
    return matches[0]


def _collection(block: SiiBlock, name: str, *, required: bool = True) -> list[str]:
    count_value = next((field.value for field in block.fields if field.key == name), None)
    if count_value is None:
        if required:
            raise GarageRelocationError(f"missing {block.type_name}.{name}")
        return []
    try:
        count = int(count_value)
    except ValueError as error:
        raise GarageRelocationError(f"invalid {block.type_name}.{name} count") from error
    values = {
        field.array_index: field.value
        for field in block.fields
        if field.name == name and field.array_index is not None
    }
    if count < 0 or sorted(values) != list(range(count)):
        raise GarageRelocationError(f"inconsistent {block.type_name}.{name} collection")
    return [values[index] for index in range(count)]


def _slot(values: list[str], slot: int, kind: str) -> str:
    if not isinstance(slot, int) or slot < 0 or slot >= len(values):
        raise GarageRelocationError(f"{kind} slot does not exist: {slot}")
    if values[slot] in _EMPTY:
        raise GarageRelocationError(f"{kind} slot is empty: {slot}")
    return values[slot]


def _resolve_driver(document: SiiDocument, reference: str) -> SiiBlock:
    block = _blocks(document).get(reference)
    if block is None:
        raise GarageRelocationError(f"driver reference is missing: {reference}")
    if block.type_name not in {"driver_player", "driver_ai"}:
        raise GarageRelocationError(f"driver reference has unexpected type: {block.type_name}")
    return block


def _resolve_vehicle(document: SiiDocument, reference: str) -> SiiBlock:
    block = _blocks(document).get(reference)
    if block is None:
        raise GarageRelocationError(f"vehicle reference is missing: {reference}")
    if block.type_name != "vehicle":
        raise GarageRelocationError(f"vehicle reference has unexpected type: {block.type_name}")
    return block


def _garages(document: SiiDocument) -> list[SiiBlock]:
    return [
        resolve_garage(document, identifier)
        for identifier in _collection(_single_block(document, "economy"), "garages")
    ]


def _status(garage: SiiBlock) -> str:
    status = next((field.value for field in garage.fields if field.key == "status"), None)
    if status is None:
        raise GarageRelocationError(f"missing garage.status: {garage.identifier}")
    return status


def _replace_collections(
    document: SiiDocument, changes: dict[tuple[str, str], list[str]]
) -> SiiDocument:
    blocks = _blocks(document)
    for (identifier, name), _values in changes.items():
        garage = blocks.get(identifier)
        if garage is None or garage.type_name != "garage":
            raise GarageRelocationError(f"missing garage during mutation: {identifier}")
        _collection(garage, name)
    source = document.source
    for (identifier, name), values in sorted(
        changes.items(), key=lambda item: item[0][0], reverse=True
    ):
        header = re.escape(f"garage : {identifier} {{")
        match = re.search(rf"(?s)({header})(?P<body>.*?)(^}})", source, re.MULTILINE)
        if match is None:
            raise GarageRelocationError(f"could not locate garage source: {identifier}")
        replacement = f"\n {name}: {len(values)}\n" + "".join(
            f" {name}[{index}]: {value}\n" for index, value in enumerate(values)
        )
        body, count = re.subn(
            rf"(?m)^\s*{name}:.*\n(?:\s*{name}\[\d+\]:.*\n)*",
            replacement,
            match.group("body"),
            count=1,
        )
        if count != 1:
            raise GarageRelocationError(f"could not update garage.{name}")
        source = source[: match.start("body")] + body + source[match.end("body") :]
    return parse_sii(source)


def _replace_values(
    document: SiiDocument, changes: dict[tuple[str, str], str | list[str]]
) -> SiiDocument:
    """Replace scalar/array fields after all sale validation has succeeded."""
    blocks = _blocks(document)
    for (identifier, name), value in changes.items():
        block = blocks.get(identifier)
        if block is None:
            raise GarageSaleError(f"missing block during mutation: {identifier}")
        if isinstance(value, list):
            _collection(block, name)
        elif not any(field.key == name for field in block.fields):
            raise GarageSaleError(f"missing {block.type_name}.{name}")
    source = document.source
    for (identifier, name), value in sorted(changes.items(), reverse=True):
        block = blocks[identifier]
        header = re.escape(f"{block.type_name} : {identifier} {{")
        match = re.search(rf"(?s)({header})(?P<body>.*?)(^}})", source, re.MULTILINE)
        if match is None:
            raise GarageSaleError(f"could not locate source block: {identifier}")
        if isinstance(value, list):
            replacement = f"\n {name}: {len(value)}\n" + "".join(
                f" {name}[{index}]: {item}\n" for index, item in enumerate(value)
            )
            pattern = rf"(?m)^[ \t]*{name}:.*\n(?:[ \t]*{name}\[\d+\]:.*\n)*"
        else:
            replacement = f"\n {name}: {value}\n"
            pattern = rf"(?m)^[ \t]*{name}:.*\n"
        body, count = re.subn(pattern, replacement, match.group("body"), count=1)
        if count != 1:
            raise GarageSaleError(f"could not update {block.type_name}.{name}")
        source = source[: match.start("body")] + body + source[match.end("body") :]
    return parse_sii(source)
