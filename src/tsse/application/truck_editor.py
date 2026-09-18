"""Targeted in-memory truck edits over the conservative SII document."""

from __future__ import annotations

import re

from tsse.core.saves.trucks import Truck
from tsse.core.sii import SiiDocument, parse_sii


class TruckEditError(ValueError):
    """Raised for missing trucks or invalid supported field values."""


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
