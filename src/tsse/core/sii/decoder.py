"""Decoder contracts and format detection for SII save data."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Protocol


class SaveFormat(StrEnum):
    """Observed SII container families, identified only from stable headers."""

    PLAINTEXT = "plaintext"
    SCS_CONTAINER = "scs-container"
    THREE_NK = "3nk"
    UNKNOWN = "unknown"


class DecodeError(Exception):
    """Base class for save decoding errors."""


class UnsupportedSaveFormatError(DecodeError):
    """Raised when the header is not a known SII container family."""


class ExternalDecoderRequiredError(DecodeError):
    """Raised for a recognized non-plaintext format without a configured decoder."""


@dataclass(frozen=True, slots=True)
class DecodedSave:
    """Plain UTF-8 SII bytes and their original detected format."""

    data: bytes
    source_format: SaveFormat


class Decoder(Protocol):
    """Port for decoding a save buffer into plaintext SII bytes."""

    def decode(self, data: bytes) -> DecodedSave:
        """Decode data or raise a typed :class:`DecodeError`."""


def detect_save_format(data: bytes) -> SaveFormat:
    """Detect only headers evidenced by legacy code or supplied fixtures."""
    if data.startswith(b"SiiNunit"):
        return SaveFormat.PLAINTEXT
    if data.startswith(b"ScsC"):
        return SaveFormat.SCS_CONTAINER
    if data.startswith(b"3nK"):
        return SaveFormat.THREE_NK
    return SaveFormat.UNKNOWN


class PlaintextDecoder:
    """Decode fixture-compatible plaintext SII while rejecting opaque containers."""

    def decode(self, data: bytes) -> DecodedSave:
        """Return plaintext data unchanged after header validation."""
        source_format = detect_save_format(data)
        if source_format is SaveFormat.PLAINTEXT:
            return DecodedSave(data=data, source_format=source_format)
        if source_format in {SaveFormat.SCS_CONTAINER, SaveFormat.THREE_NK}:
            raise ExternalDecoderRequiredError(
                f"{source_format.value} save data requires a separately configured decoder"
            )
        raise UnsupportedSaveFormatError("unrecognized save header")
