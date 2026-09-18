"""Targeted in-memory trailer repair over lossless SII source."""

from __future__ import annotations

import re

from tsse.core.saves.trailers import Trailer
from tsse.core.sii import SiiDocument, parse_sii


class TrailerEditError(ValueError):
    """Raised for missing trailers or unsupported repair requests."""


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
    """Zero legacy cargo, body, and chassis damage for one selected trailer."""
    find_trailer(document, identifier)
    header = re.escape(f"trailer : {identifier} {{")
    match = re.search(
        rf"(?s)(?P<head>{header})(?P<body>.*?)(?P<end>^}})", document.source, re.MULTILINE
    )
    if match is None:
        raise TrailerEditError("could not locate trailer source block")
    body = match.group("body")
    for key in ("cargo_damage", "trailer_body_wear", "chassis_wear"):
        body, count = re.subn(
            rf"(?m)^(?P<prefix>\s*{key}\s*:\s*)[^\r\n]*", r"\g<prefix>0", body, count=1
        )
        if count != 1:
            raise TrailerEditError(f"missing trailer.{key}")
    source = document.source[: match.start("body")] + body + document.source[match.end("body") :]
    return parse_sii(source)
