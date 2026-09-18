"""Targeted in-memory garage status editing."""

from __future__ import annotations

import re

from tsse.core.saves.garages import Garage
from tsse.core.sii import SiiDocument, parse_sii


class GarageEditError(ValueError):
    """Raised for unavailable garages or invalid status values."""


def find_garage(document: SiiDocument, identifier: str) -> Garage:
    """Read the proven garage status field."""
    block = next(
        (
            item
            for item in document.blocks
            if item.type_name == "garage" and item.identifier == identifier
        ),
        None,
    )
    if block is None:
        raise GarageEditError(f"missing garage: {identifier}")
    status = next((field.value for field in block.fields if field.key == "status"), None)
    try:
        return Garage(identifier, int(status or ""))
    except ValueError as error:
        raise GarageEditError("garage lacks integer status") from error


def set_garage_status(document: SiiDocument, identifier: str, status: int) -> SiiDocument:
    """Set one garage's legacy status while preserving all non-target content."""
    if status < 0:
        raise GarageEditError("garage status must be non-negative")
    find_garage(document, identifier)
    header = re.escape(f"garage : {identifier} {{")
    match = re.search(
        rf"(?s)(?P<head>{header})(?P<body>.*?)(?P<end>^}})", document.source, re.MULTILINE
    )
    if match is None:
        raise GarageEditError("could not locate garage source block")
    body, count = re.subn(
        r"(?m)^(?P<prefix>\s*status\s*:\s*)[^\r\n]*",
        rf"\g<prefix>{status}",
        match.group("body"),
        count=1,
    )
    if count != 1:
        raise GarageEditError("missing garage.status")
    source = document.source[: match.start("body")] + body + document.source[match.end("body") :]
    return parse_sii(source)
