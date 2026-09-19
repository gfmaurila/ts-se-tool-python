"""Bounded legacy Convoy Tools clipboard behavior, without GUI or save import."""

from __future__ import annotations

import gzip
import re

from tsse.core.sii import SiiDocument, parse_sii


class LegacyConvoyError(ValueError):
    """A legacy GPS payload or player placement cannot be safely consumed."""


_HEADER = "GPS_TruckPosition"


def copy_truck_position(raw_placement: str) -> str:
    """Mirror the legacy single-position copy as uppercase gzip hex."""
    if not isinstance(raw_placement, str) or not raw_placement:
        raise LegacyConvoyError("truck placement must be non-empty SII text")
    return gzip.compress(f"{_HEADER}\r\n{raw_placement}".encode()).hex().upper()


def paste_truck_position(payload: str) -> str:
    """Decode the first placement line accepted by the legacy paste handler."""
    try:
        usable = payload[: len(payload) - len(payload) % 2]
        text = gzip.decompress(bytes.fromhex(usable)).decode("utf-8-sig")
    except (TypeError, ValueError, OSError, UnicodeDecodeError) as error:
        raise LegacyConvoyError("invalid legacy GPS position payload") from error
    lines = text.split("\r\n")
    if len(lines) < 2 or lines[0] != _HEADER or not lines[1]:
        raise LegacyConvoyError("clipboard payload is not GPS truck position data")
    return lines[1]


def set_truck_position(document: SiiDocument, raw_placement: str) -> SiiDocument:
    """Apply the only proven Convoy Tools SII write: ``player.my_truck_placement``."""
    if not raw_placement:
        raise LegacyConvoyError("truck placement must not be empty")
    players = [block for block in document.blocks if block.type_name == "player"]
    if len(players) != 1 or not any(
        field.key == "my_truck_placement" for field in players[0].fields
    ):
        raise LegacyConvoyError("missing player.my_truck_placement")
    source, count = re.subn(
        r"(?m)^(?P<prefix>\s*my_truck_placement\s*:\s*)[^\r\n]*",
        rf"\g<prefix>{raw_placement}",
        document.source,
        count=1,
    )
    if count != 1:
        raise LegacyConvoyError("could not update player.my_truck_placement")
    return parse_sii(source)
