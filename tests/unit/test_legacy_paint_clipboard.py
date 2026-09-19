"""Regression coverage for the literal TS SE Tool TruckPaint clipboard contract."""

import gzip

import pytest

from tsse.application.legacy_paint_clipboard import (
    LegacyPaintClipboard,
    LegacyPaintClipboardError,
)


def test_copy_creates_immutable_snapshot_and_uses_uppercase_gzip_hex() -> None:
    source = ["paint-line-a", "paint-line-b"]
    payload = LegacyPaintClipboard.copy_from_part_data(source)
    source[0] = "changed-after-copy"

    encoded = payload.to_hex_payload()

    assert payload.part_data == ("paint-line-a", "paint-line-b")
    assert encoded == encoded.upper()
    assert gzip.decompress(bytes.fromhex(encoded)).decode("utf-8") == (
        "TruckPaint\r\npaint-line-a\r\npaint-line-b\r\n"
    )


def test_paste_preserves_the_trailing_empty_entry_of_legacy_split() -> None:
    copied = LegacyPaintClipboard.copy_from_part_data(["one", "two"])

    pasted = LegacyPaintClipboard.from_hex_payload(copied.to_hex_payload())

    assert pasted.part_data == ("one", "two", "")


def test_paste_ignores_a_final_unpaired_hex_character_like_legacy() -> None:
    copied = LegacyPaintClipboard.copy_from_part_data(["one"])

    pasted = LegacyPaintClipboard.from_hex_payload(copied.to_hex_payload() + "F")

    assert pasted.part_data == ("one", "")


def test_paste_accepts_incomplete_part_data_like_the_legacy_handler() -> None:
    encoded = gzip.compress(b"TruckPaint\r\n").hex().upper()

    pasted = LegacyPaintClipboard.from_hex_payload(encoded)

    assert pasted.part_data == ("",)


@pytest.mark.parametrize("payload", ["", "00", "GG", gzip.compress(b"Wrong\r\n").hex()])
def test_invalid_payload_is_typed_error(payload: str) -> None:
    with pytest.raises(LegacyPaintClipboardError):
        LegacyPaintClipboard.from_hex_payload(payload)


def test_copy_rejects_non_string_part_data_without_mutating_the_source() -> None:
    source: list[object] = ["valid", 1]

    with pytest.raises(LegacyPaintClipboardError):
        LegacyPaintClipboard.copy_from_part_data(source)  # type: ignore[arg-type]

    assert source == ["valid", 1]
