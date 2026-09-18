"""Adapter boundary for separately supplied SII decoder implementations."""

from __future__ import annotations

from collections.abc import Callable

from tsse.core.sii import DecodedSave, Decoder, SaveFormat


class ExternalDecoder:
    """Adapt a licensed external decoder without exposing its implementation to core."""

    def __init__(self, decode_opaque: Callable[[bytes], bytes]) -> None:
        self._decode_opaque = decode_opaque

    def decode(self, data: bytes) -> DecodedSave:
        """Delegate opaque decoding and return its plaintext result."""
        return DecodedSave(
            data=self._decode_opaque(data),
            source_format=SaveFormat.SCS_CONTAINER,
        )


def as_decoder(decoder: Decoder) -> Decoder:
    """Expose a decoder through the core contract for dependency injection."""
    return decoder
