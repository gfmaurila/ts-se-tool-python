"""Binary SII (BSII) version 3 decoder.

BSII has no editable textual source to round-trip.  This module therefore
converts every supported binary field into SiiN text and rejects an unknown
value type instead of silently losing it.  The generated text can then use the
normal conservative SII parser and editors.
"""

from __future__ import annotations

import struct
from collections.abc import Callable
from dataclasses import dataclass
from typing import cast

from tsse.core.sii.decoder import DecodeError

_MAX_COLLECTION = 1_000_000
_NAMELESS = 0xFF


class BinarySiiDecodeError(DecodeError):
    """Raised when a BSII stream is malformed or uses an unsupported value."""


class _Stream:
    def __init__(self, data: bytes) -> None:
        self._data = data
        self._position = 0

    @property
    def at_end(self) -> bool:
        return self._position == len(self._data)

    @property
    def position(self) -> int:
        return self._position

    def read(self, size: int) -> bytes:
        if size < 0 or self._position + size > len(self._data):
            raise BinarySiiDecodeError("truncated BSII stream")
        result = self._data[self._position : self._position + size]
        self._position += size
        return result

    def u8(self) -> int:
        return self.read(1)[0]

    def u16(self) -> int:
        return cast(int, struct.unpack("<H", self.read(2))[0])

    def u32(self) -> int:
        return cast(int, struct.unpack("<I", self.read(4))[0])

    def i32(self) -> int:
        return cast(int, struct.unpack("<i", self.read(4))[0])

    def u64(self) -> int:
        return cast(int, struct.unpack("<Q", self.read(8))[0])

    def i64(self) -> int:
        return cast(int, struct.unpack("<q", self.read(8))[0])

    def f32(self) -> float:
        return cast(float, struct.unpack("<f", self.read(4))[0])

    def text(self) -> str:
        size = self.u32()
        if size > _MAX_COLLECTION:
            raise BinarySiiDecodeError(
                f"BSII string at offset {self._position - 4} exceeds decoder limit"
            )
        try:
            return self.read(size).decode("utf-8")
        except UnicodeDecodeError as error:
            raise BinarySiiDecodeError("BSII string is not valid UTF-8") from error


@dataclass(frozen=True, slots=True)
class _Field:
    kind: int
    name: str
    ordinal_values: dict[int, str]


_BASE38 = "0123456789abcdefghijklmnopqrstuvwxyz_"


def _decode_id(value: int) -> str:
    value &= ~(1 << 63)
    result = ""
    while value:
        value, digit = divmod(value, 38)
        if not 1 <= digit <= len(_BASE38):
            raise BinarySiiDecodeError("invalid BSII base-38 identifier")
        result += _BASE38[digit - 1]
    return result


def _identifier(stream: _Stream, *, old_hex_style: bool = False) -> str:
    length = stream.u8()
    if length == 0:
        return "null"
    values = [stream.u64() for _ in range(1 if length == _NAMELESS else length)]
    if length == _NAMELESS:
        value = values[0]
        if old_hex_style and value >> 32 == 0:
            return f"_nameless.{value >> 16 & 0xFFFF:04X}.{value & 0xFFFF:04X}"
        return f"_nameless.{value:x}"
    return ".".join(_decode_id(value) for value in values)


def _number(value: float) -> str:
    if value != value:
        return f"&{struct.unpack('<I', struct.pack('<f', value))[0]:08x}"
    if value.is_integer() and abs(value) < 1e7:
        return str(int(value))
    return f"&{struct.unpack('<I', struct.pack('<f', value))[0]:08x}"


def _quoted(value: str) -> str:
    return '"' + value.replace("\\", "\\\\").replace('"', '\\"') + '"'


class BinarySiiDecoder:
    """Convert BSII versions 1–3 to UTF-8 SiiN text without field filtering."""

    def decode(self, data: bytes) -> bytes:
        stream = _Stream(data)
        if stream.read(4) != b"BSII":
            raise BinarySiiDecodeError("not a BSII stream")
        version = stream.u32()
        if version not in {1, 2, 3}:
            raise BinarySiiDecodeError(f"unsupported BSII version {version}")
        structures: dict[int, tuple[str, tuple[_Field, ...]]] = {}
        blocks: list[str] = []
        while not stream.at_end:
            structure_id = stream.u32()
            if structure_id == 0:
                if stream.u8() == 0:
                    break
                identifier = stream.u32()
                if identifier == 0 or identifier in structures:
                    raise BinarySiiDecodeError("invalid or duplicate BSII structure id")
                name = stream.text()
                fields: list[_Field] = []
                while (kind := stream.u32()) != 0:
                    try:
                        field_name = stream.text()
                    except BinarySiiDecodeError as error:
                        raise BinarySiiDecodeError(
                            f"invalid field definition 0x{kind:x} in {name}: {error}"
                        ) from error
                    # Current 1.61 BSII v3 fixtures store ordinal values in
                    # the data block.  There is no per-structure table here.
                    fields.append(_Field(kind, field_name, {}))
                structures[identifier] = (name, tuple(fields))
                continue
            try:
                name, defined_fields = structures[structure_id]
            except KeyError as error:
                raise BinarySiiDecodeError(f"unknown BSII structure id {structure_id}") from error
            block_id = _identifier(stream, old_hex_style=version < 2)
            lines = [f"{name} : {block_id} {{"]
            for field in defined_fields:
                lines.extend(self._field_lines(stream, version, field))
            lines.append("}")
            blocks.append("\r\n".join(lines))
        if not stream.at_end:
            raise BinarySiiDecodeError("unexpected data after BSII terminator")
        return ("SiiNunit\r\n{\r\n" + "\r\n\r\n".join(blocks) + "\r\n}\r\n").encode()

    def _field_lines(self, stream: _Stream, version: int, field: _Field) -> list[str]:
        value = self._value(stream, version, field)
        if isinstance(value, list):
            return [f" {field.name}: {len(value)}"] + [
                f" {field.name}[{index}]: {item}" for index, item in enumerate(value)
            ]
        return [f" {field.name}: {value}"]

    def _value(self, stream: _Stream, version: int, field: _Field) -> str | list[str]:
        kind = field.kind
        if kind == 0x01:
            return _quoted(stream.text())
        if kind == 0x03:
            return _quoted(_decode_id(stream.u64()))
        if kind == 0x05:
            return _number(stream.f32())
        if kind == 0x07:
            return f"({_number(stream.f32())}, {_number(stream.f32())})"
        if kind == 0x09:
            return f"({_number(stream.f32())}, {_number(stream.f32())}, {_number(stream.f32())})"
        if kind == 0x11:
            return f"({stream.i32()}, {stream.i32()}, {stream.i32()})"
        if kind == 0x17:
            return self._vec8(stream, version)
        if kind == 0x25:
            return str(stream.i32())
        if kind in {0x27, 0x2F}:
            return str(stream.u32())
        if kind == 0x2B:
            return str(stream.u16())
        if kind == 0x31:
            return str(stream.i64())
        if kind == 0x33:
            return str(stream.u64())
        if kind == 0x35:
            return "true" if stream.u8() else "false"
        if kind == 0x37:
            value = stream.u32()
            if value in field.ordinal_values:
                return _quoted(field.ordinal_values[value])
            return str(value)
        if kind in {0x39, 0x3B, 0x3D}:
            return _identifier(stream, old_hex_style=version < 2)
        if kind == 0x41:
            return f"({stream.i32()}, {stream.i32()})"
        array_scalars: dict[int, Callable[[], str]] = {
            0x02: lambda: _quoted(stream.text()),
            0x04: lambda: _quoted(_decode_id(stream.u64())),
            0x06: lambda: _number(stream.f32()),
            0x0A: lambda: (
                f"({_number(stream.f32())}, {_number(stream.f32())}, {_number(stream.f32())})"
            ),
            0x12: lambda: f"({stream.i32()}, {stream.i32()}, {stream.i32()})",
            0x18: lambda: self._vec8(stream, version),
            0x26: lambda: str(stream.i32()),
            0x28: lambda: str(stream.u32()),
            0x2C: lambda: str(stream.u16()),
            0x32: lambda: str(stream.i64()),
            0x34: lambda: str(stream.u64()),
            0x36: lambda: "true" if stream.u8() else "false",
            0x3A: lambda: _identifier(stream, old_hex_style=version < 2),
            0x3C: lambda: _identifier(stream, old_hex_style=version < 2),
            0x3E: lambda: _identifier(stream, old_hex_style=version < 2),
        }
        try:
            reader = array_scalars[kind]
        except KeyError as error:
            raise BinarySiiDecodeError(
                f"unsupported BSII value type 0x{kind:x} ({field.name})"
            ) from error
        count = stream.u32()
        if count > _MAX_COLLECTION:
            raise BinarySiiDecodeError("BSII array exceeds decoder limit")
        return [reader() for _ in range(count)]

    @staticmethod
    def _vec8(stream: _Stream, version: int) -> str:
        values = [stream.f32() for _ in range(7 if version == 1 else 8)]
        if version == 1:
            values.insert(3, 0.0)
        else:
            bias = int(values[3])
            values[0] += ((bias & 0xFFF) - 2048) << 9
            values[2] += (((bias >> 12) & 0xFFF) - 2048) << 9
        return (
            f"({_number(values[0])}, {_number(values[1])}, {_number(values[2])}) "
            f"({_number(values[4])}; {_number(values[5])}, {_number(values[6])}, "
            f"{_number(values[7])})"
        )
