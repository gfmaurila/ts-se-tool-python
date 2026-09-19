"""Legacy ``TruckPaint`` clipboard payload, independent from SII mutation.

The 0.3.11.0 handlers copy and replace ``UserCompanyTruckDataPart.PartData``.
They do not map that transient list to ``vehicle_paint_job_accessory`` fields or
write a SII block.  This module deliberately preserves that boundary.
"""

from __future__ import annotations

import gzip
from collections.abc import Sequence
from dataclasses import dataclass


class LegacyPaintClipboardError(ValueError):
    """Raised when a value cannot be consumed as a legacy TruckPaint payload."""


_HEADER = "TruckPaint"
_LINE_ENDING = "\r\n"


@dataclass(frozen=True)
class LegacyPaintClipboard:
    """An immutable snapshot of the legacy transient ``PartData`` list."""

    part_data: tuple[str, ...]

    @classmethod
    def copy_from_part_data(cls, part_data: Sequence[str]) -> LegacyPaintClipboard:
        """Copy the list exactly; callers cannot retain a mutable AST/list alias."""
        if any(not isinstance(value, str) for value in part_data):
            raise LegacyPaintClipboardError("legacy paint PartData must contain strings")
        return cls(tuple(part_data))

    def to_hex_payload(self) -> str:
        """Produce the gzip/uppercase-hex clipboard representation used by the UI."""
        text = _HEADER + _LINE_ENDING + "".join(
            value + _LINE_ENDING for value in self.part_data
        )
        return gzip.compress(text.encode("utf-8")).hex().upper()

    @classmethod
    def from_hex_payload(cls, payload: str) -> LegacyPaintClipboard:
        """Parse a legacy clipboard payload without imposing field-level validation."""
        if not isinstance(payload, str) or not payload:
            raise LegacyPaintClipboardError("legacy paint clipboard payload is empty")
        try:
            # ``ZipDataUtilities.unzipText`` allocates ``Length / 2`` pairs,
            # so a final unpaired hex character is ignored by the legacy UI.
            usable = payload[: len(payload) - (len(payload) % 2)]
            compressed = bytes(
                int(usable[index : index + 2], 16)
                for index in range(0, len(usable), 2)
            )
            text = gzip.decompress(compressed).decode("utf-8-sig")
        except (UnicodeDecodeError, ValueError, OSError) as error:
            raise LegacyPaintClipboardError("invalid legacy paint clipboard payload") from error

        lines = text.split(_LINE_ENDING)
        if not lines or lines[0] != _HEADER:
            raise LegacyPaintClipboardError("clipboard payload is not TruckPaint data")
        # StringSplitOptions.None in the legacy handler deliberately keeps the
        # trailing empty entry emitted by the copy action.
        return cls(tuple(lines[1:]))
