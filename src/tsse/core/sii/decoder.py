"""Decoder contracts and format detection for SII save data."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Protocol

from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives.padding import PKCS7


class SaveFormat(StrEnum):
    """Observed SII container families, identified only from stable headers."""

    PLAINTEXT = "plaintext"
    SCS_CONTAINER = "scs-container"
    THREE_NK = "3nk"
    BINARY = "bsii"
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
    if data.startswith(b"BSII"):
        return SaveFormat.BINARY
    return SaveFormat.UNKNOWN


class PlaintextDecoder:
    """Decode fixture-compatible plaintext SII while rejecting opaque containers."""

    def decode(self, data: bytes) -> DecodedSave:
        """Return plaintext data unchanged after header validation."""
        source_format = detect_save_format(data)
        if source_format is SaveFormat.PLAINTEXT:
            return DecodedSave(data=data, source_format=source_format)
        if source_format in {SaveFormat.SCS_CONTAINER, SaveFormat.THREE_NK, SaveFormat.BINARY}:
            raise ExternalDecoderRequiredError(
                f"{source_format.value} save data requires a separately configured decoder"
            )
        raise UnsupportedSaveFormatError("unrecognized save header")


class ScsContainerDecoder:
    """Decode an ScsC envelope while retaining its source classification.

    The implementation is independent Python code based on the documented SCS
    envelope. Non-text inner payloads remain explicit unsupported formats until
    they have a lossless decoder suitable for the conservative SII parser.
    """

    _HEADER_SIZE = 56
    _KEY = bytes.fromhex(
        "2a5fcb1791d22fb60245b3d8369ed0b2"
        "c27371563fbf1f3c9edf6b11825a5d0a"
    )

    def decode(self, data: bytes) -> DecodedSave:
        """Decrypt, unpad, and inflate one ScsC save envelope."""
        import zlib

        if detect_save_format(data) is not SaveFormat.SCS_CONTAINER:
            return PlaintextDecoder().decode(data)
        if len(data) < self._HEADER_SIZE:
            raise DecodeError("ScsC save is smaller than its 56-byte header")

        initialization_vector = data[36:52]
        expected_size = int.from_bytes(data[52:56], "little")
        ciphertext = data[self._HEADER_SIZE :]
        block_size_bytes = algorithms.AES.block_size // 8
        if not ciphertext or len(ciphertext) % block_size_bytes:
            raise DecodeError("ScsC ciphertext must be a non-empty multiple of 16 bytes")

        decryptor = Cipher(algorithms.AES(self._KEY), modes.CBC(initialization_vector)).decryptor()
        padded = decryptor.update(ciphertext) + decryptor.finalize()
        try:
            unpadder = PKCS7(algorithms.AES.block_size).unpadder()
            compressed = unpadder.update(padded) + unpadder.finalize()
        except ValueError as error:
            raise DecodeError("ScsC AES payload has invalid PKCS#7 padding") from error
        try:
            plaintext = zlib.decompress(compressed)
        except zlib.error as error:
            raise DecodeError("ScsC AES payload is not a valid zlib stream") from error
        if len(plaintext) != expected_size:
            raise DecodeError(
                f"ScsC inflated size {len(plaintext)} does not match header size {expected_size}"
            )
        return DecodedSave(data=plaintext, source_format=SaveFormat.SCS_CONTAINER)
