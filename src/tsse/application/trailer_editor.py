"""Targeted in-memory trailer repair over lossless SII source."""

from __future__ import annotations

import re
from enum import StrEnum

from tsse.core.saves.trailers import Trailer
from tsse.core.saves.vehicle_graph import VehicleGraphError, resolve_trailer_chain
from tsse.core.sii import SiiBlock, SiiDocument, parse_sii


class TrailerEditError(ValueError):
    """Raised for missing trailers or unsupported repair requests."""


class TrailerComponent(StrEnum):
    """The four repair controls exposed by the legacy trailer tab."""

    CARGO = "cargo"
    BODY = "body"
    CHASSIS = "chassis"
    WHEELS = "wheels"


_COMPONENT_FIELDS = {
    TrailerComponent.CARGO: "cargo_damage",
    TrailerComponent.BODY: "trailer_body_wear",
    TrailerComponent.CHASSIS: "chassis_wear",
}
_REPAIR_FIELDS = (*_COMPONENT_FIELDS.values(),)


def find_trailer(document: SiiDocument, identifier: str) -> Trailer:
    """Return a supported trailer condition view."""
    block = next(
        (
            item
            for item in document.blocks
            if item.type_name == "trailer" and item.identifier == identifier
        ),
        None,
    )
    if block is None:
        raise TrailerEditError(f"missing trailer: {identifier}")
    values = {field.key: field.value for field in block.fields}
    try:
        return Trailer(
            identifier,
            float(values["cargo_damage"]),
            float(values["trailer_body_wear"]),
            float(values["chassis_wear"]),
        )
    except (KeyError, ValueError) as error:
        raise TrailerEditError("trailer lacks supported condition fields") from error


def repair_trailer(document: SiiDocument, identifier: str) -> SiiDocument:
    """Apply the legacy total repair across the selected slave-trailer chain."""
    chain = _resolve_slave_chain(document, identifier)
    changes: list[tuple[re.Match[str], str]] = []
    for block in chain:
        body, match = _trailer_body(document, block.identifier)
        for key in _REPAIR_FIELDS:
            body = _replace_required_field(body, key, "0")
        changes.append((match, _clear_wheels_wear(block, body)))
    return _reparse_bodies(document, changes)


def repair_trailer_component(
    document: SiiDocument, identifier: str, component: TrailerComponent
) -> SiiDocument:
    """Apply one legacy repair control across the selected slave-trailer chain."""
    if not isinstance(component, TrailerComponent):
        raise TrailerEditError(f"unsupported trailer repair component: {component!r}")
    chain = _resolve_slave_chain(document, identifier)
    changes: list[tuple[re.Match[str], str]] = []
    for selected in chain:
        body, match = _trailer_body(document, selected.identifier)
        if component is TrailerComponent.WHEELS:
            body = _clear_wheels_wear(selected, body)
        else:
            body = _replace_required_field(body, _COMPONENT_FIELDS[component], "0")
        changes.append((match, body))
    return _reparse_bodies(document, changes)


def _resolve_slave_chain(document: SiiDocument, identifier: str) -> list[SiiBlock]:
    try:
        return list(resolve_trailer_chain(document, identifier))
    except VehicleGraphError as error:
        message = str(error)
        if message.startswith("missing SII unit reference:"):
            message = message.replace("missing SII unit reference:", "missing trailer:", 1)
        elif message.startswith("expected trailer, found"):
            message = message.replace(
                "expected trailer, found", "slave_trailer target has unexpected type", 1
            )
        raise TrailerEditError(message) from error


def _trailer_body(document: SiiDocument, identifier: str) -> tuple[str, re.Match[str]]:
    header = re.escape(f"trailer : {identifier} {{")
    match = re.search(
        rf"(?s)(?P<head>{header})(?P<body>.*?)(?P<end>^}})", document.source, re.MULTILINE
    )
    if match is None:
        raise TrailerEditError("could not locate trailer source block")
    return match.group("body"), match


def _replace_required_field(body: str, key: str, value: str) -> str:
    updated, count = re.subn(
        rf"(?m)^(?P<prefix>\s*{key}\s*:\s*)[^\r\n]*", rf"\g<prefix>{value}", body, count=1
    )
    if count != 1:
        raise TrailerEditError(f"missing trailer.{key}")
    return updated


def _clear_wheels_wear(block: SiiBlock, body: str) -> str:
    declared = next((field.value for field in block.fields if field.key == "wheels_wear"), None)
    indexes = [field.array_index for field in block.fields if field.name == "wheels_wear"]
    if declared is None:
        raise TrailerEditError("missing trailer.wheels_wear")
    try:
        count = int(declared)
    except ValueError as error:
        raise TrailerEditError("invalid trailer.wheels_wear count") from error
    if count < 0 or sorted(index for index in indexes if index is not None) != list(range(count)):
        raise TrailerEditError("inconsistent trailer.wheels_wear array")
    updated = _replace_required_field(body, "wheels_wear", "0")
    return re.sub(r"(?m)^\s*wheels_wear\[\d+\]\s*:[^\r\n]*(?:\r?\n|$)", "", updated)


def _reparse_bodies(document: SiiDocument, changes: list[tuple[re.Match[str], str]]) -> SiiDocument:
    source = document.source
    for match, body in sorted(changes, key=lambda change: change[0].start("body"), reverse=True):
        source = source[: match.start("body")] + body + source[match.end("body") :]
    return parse_sii(source)
