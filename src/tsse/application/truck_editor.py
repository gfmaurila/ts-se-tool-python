"""Targeted in-memory truck edits over the conservative SII document."""

from __future__ import annotations

import re
from enum import StrEnum

from tsse.core.saves.trucks import Truck
from tsse.core.sii import SiiDocument, parse_sii


class TruckEditError(ValueError):
    """Raised for missing trucks or invalid supported field values."""


class TruckComponent(StrEnum):
    """The five repair controls exposed by the legacy truck tab."""

    ENGINE = "engine"
    TRANSMISSION = "transmission"
    CHASSIS = "chassis"
    CABIN = "cabin"
    WHEELS = "wheels"


_COMPONENT_FIELDS = {
    TruckComponent.ENGINE: "engine_wear",
    TruckComponent.TRANSMISSION: "transmission_wear",
    TruckComponent.CHASSIS: "chassis_wear",
    TruckComponent.CABIN: "cabin_wear",
}
_REPAIR_FIELDS = (*_COMPONENT_FIELDS.values(),)


def find_truck(document: SiiDocument, identifier: str) -> Truck:
    """Return the supported condition view for a vehicle block."""
    block = next(
        (
            item
            for item in document.blocks
            if item.type_name == "vehicle" and item.identifier == identifier
        ),
        None,
    )
    if block is None:
        raise TruckEditError(f"missing vehicle: {identifier}")
    values = {field.key: field.value for field in block.fields}
    try:
        return Truck(
            identifier,
            int(values["engine_wear"]),
            int(values["transmission_wear"]),
            int(values["cabin_wear"]),
            float(values["fuel_relative"]),
        )
    except (KeyError, ValueError) as error:
        raise TruckEditError("vehicle lacks supported condition fields") from error


def set_condition(
    document: SiiDocument, identifier: str, wear: int, fuel_relative: float
) -> SiiDocument:
    """Set legacy vehicle wear fields and fuel ratio while preserving other content."""
    if wear < 0:
        raise TruckEditError("wear must be non-negative")
    if not 0 <= fuel_relative <= 1:
        raise TruckEditError("fuel_relative must be between 0 and 1")
    find_truck(document, identifier)
    header = re.escape(f"vehicle : {identifier} {{")
    block_pattern = re.compile(rf"(?s)(?P<head>{header})(?P<body>.*?)(?P<end>^}})", re.MULTILINE)
    match = block_pattern.search(document.source)
    if match is None:
        raise TruckEditError("could not locate vehicle source block")
    body = match.group("body")
    replacements = {
        "engine_wear": str(wear),
        "transmission_wear": str(wear),
        "cabin_wear": str(wear),
        "fuel_relative": str(fuel_relative),
    }
    for key, value in replacements.items():
        body, count = re.subn(
            rf"(?m)^(?P<prefix>\s*{key}\s*:\s*)[^\r\n]*", rf"\g<prefix>{value}", body, count=1
        )
        if count != 1:
            raise TruckEditError(f"missing vehicle.{key}")
    source = document.source[: match.start("body")] + body + document.source[match.end("body") :]
    return parse_sii(source)


def repair_truck(document: SiiDocument, identifier: str) -> SiiDocument:
    """Apply the legacy total-repair action to one vehicle block."""
    body, match = _vehicle_body(document, identifier)
    for key in _REPAIR_FIELDS:
        body = _replace_required_field(body, key, "0")
    body = _clear_wheels_wear(document, identifier, body)
    return _reparse_body(document, match, body)


def repair_truck_component(
    document: SiiDocument, identifier: str, component: TruckComponent
) -> SiiDocument:
    """Apply exactly one of the five legacy truck repair controls."""
    if not isinstance(component, TruckComponent):
        raise TruckEditError(f"unsupported truck repair component: {component!r}")
    body, match = _vehicle_body(document, identifier)
    if component is TruckComponent.WHEELS:
        body = _clear_wheels_wear(document, identifier, body)
    else:
        body = _replace_required_field(body, _COMPONENT_FIELDS[component], "0")
    return _reparse_body(document, match, body)


def refuel_truck(document: SiiDocument, identifier: str) -> SiiDocument:
    """Apply the legacy refuel action, which assigns ``fuel_relative: 1``."""
    body, match = _vehicle_body(document, identifier)
    body = _replace_required_field(body, "fuel_relative", "1")
    return _reparse_body(document, match, body)


def _vehicle_body(document: SiiDocument, identifier: str) -> tuple[str, re.Match[str]]:
    block = next(
        (
            item
            for item in document.blocks
            if item.type_name == "vehicle" and item.identifier == identifier
        ),
        None,
    )
    if block is None:
        raise TruckEditError(f"missing vehicle: {identifier}")
    header = re.escape(f"vehicle : {identifier} {{")
    match = re.search(
        rf"(?s)(?P<head>{header})(?P<body>.*?)(?P<end>^}})", document.source, re.MULTILINE
    )
    if match is None:
        raise TruckEditError("could not locate vehicle source block")
    return match.group("body"), match


def _replace_required_field(body: str, key: str, value: str) -> str:
    updated, count = re.subn(
        rf"(?m)^(?P<prefix>\s*{key}\s*:\s*)[^\r\n]*", rf"\g<prefix>{value}", body, count=1
    )
    if count != 1:
        raise TruckEditError(f"missing vehicle.{key}")
    return updated


def _clear_wheels_wear(document: SiiDocument, identifier: str, body: str) -> str:
    block = next(
        item
        for item in document.blocks
        if item.type_name == "vehicle" and item.identifier == identifier
    )
    declared = next((field.value for field in block.fields if field.key == "wheels_wear"), None)
    indexed = [field.array_index for field in block.fields if field.name == "wheels_wear"]
    if declared is None:
        raise TruckEditError("missing vehicle.wheels_wear")
    try:
        count = int(declared)
    except ValueError as error:
        raise TruckEditError("invalid vehicle.wheels_wear count") from error
    if count < 0 or sorted(index for index in indexed if index is not None) != list(range(count)):
        raise TruckEditError("inconsistent vehicle.wheels_wear array")
    updated = _replace_required_field(body, "wheels_wear", "0")
    return re.sub(r"(?m)^\s*wheels_wear\[\d+\]\s*:[^\r\n]*(?:\r?\n|$)", "", updated)


def _reparse_body(document: SiiDocument, match: re.Match[str], body: str) -> SiiDocument:
    source = document.source[: match.start("body")] + body + document.source[match.end("body") :]
    return parse_sii(source)
