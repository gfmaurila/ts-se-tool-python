"""Lossless SII document model and decoder contracts."""

from tsse.core.sii.binary import BinarySiiDecodeError, BinarySiiDecoder
from tsse.core.sii.decoder import (
    DecodedSave,
    DecodeError,
    Decoder,
    ExternalDecoderRequiredError,
    PlaintextDecoder,
    SaveFormat,
    ScsContainerDecoder,
    UnsupportedSaveFormatError,
    detect_save_format,
)
from tsse.core.sii.parser import SiiBlock, SiiDocument, SiiField, SiiParseError, parse_sii
from tsse.core.sii.references import (
    DuplicateUnitIdentifierError,
    MalformedReferenceError,
    MissingReferenceTargetError,
    ReferenceResolution,
    ReferenceResolutionError,
    ReferenceStatus,
    SiiGraph,
    TypedUnitReference,
    WrongReferenceTypeError,
)

__all__ = [
    "DecodeError",
    "BinarySiiDecodeError",
    "BinarySiiDecoder",
    "DecodedSave",
    "Decoder",
    "ExternalDecoderRequiredError",
    "PlaintextDecoder",
    "ScsContainerDecoder",
    "SaveFormat",
    "UnsupportedSaveFormatError",
    "detect_save_format",
    "SiiBlock",
    "SiiDocument",
    "SiiField",
    "SiiParseError",
    "parse_sii",
    "DuplicateUnitIdentifierError",
    "MalformedReferenceError",
    "MissingReferenceTargetError",
    "ReferenceResolution",
    "ReferenceResolutionError",
    "ReferenceStatus",
    "SiiGraph",
    "TypedUnitReference",
    "WrongReferenceTypeError",
]
