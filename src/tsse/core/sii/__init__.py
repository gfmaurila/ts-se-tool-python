"""Lossless SII document model and decoder contracts."""

from tsse.core.sii.decoder import (
    DecodedSave,
    DecodeError,
    Decoder,
    ExternalDecoderRequiredError,
    PlaintextDecoder,
    SaveFormat,
    UnsupportedSaveFormatError,
    detect_save_format,
)
from tsse.core.sii.parser import SiiBlock, SiiDocument, SiiField, SiiParseError, parse_sii

__all__ = [
    "DecodeError",
    "DecodedSave",
    "Decoder",
    "ExternalDecoderRequiredError",
    "PlaintextDecoder",
    "SaveFormat",
    "UnsupportedSaveFormatError",
    "detect_save_format",
    "SiiBlock",
    "SiiDocument",
    "SiiField",
    "SiiParseError",
    "parse_sii",
]
