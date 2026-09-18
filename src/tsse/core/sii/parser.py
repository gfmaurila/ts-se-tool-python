"""Conservative, lossless parser for plaintext SII documents."""

from __future__ import annotations

import re
from dataclasses import dataclass


class SiiParseError(ValueError):
    """Raised when data cannot be represented as a plaintext SII document."""


_BLOCK = re.compile(r"^\s*(?P<type>[^\s:]+)\s*:\s*(?P<identifier>[^\s{]+)\s*\{\s*$")
_FIELD = re.compile(r"^\s*(?P<key>[^\s:]+)\s*:\s*(?P<value>.*?)(?:\r?\n)?$")
_LIST_KEY = re.compile(r"^(?P<name>.+)\[(?P<index>\d+)]$")


@dataclass(frozen=True, slots=True)
class SiiField:
    """An ordered field whose value is retained verbatim except line ending."""

    key: str
    value: str
    array_index: int | None

    @property
    def name(self) -> str:
        """Return the unindexed field name."""
        match = _LIST_KEY.match(self.key)
        return match.group("name") if match else self.key


@dataclass(frozen=True, slots=True)
class SiiBlock:
    """A named SII block with ordered fields and retained unparsed lines."""

    type_name: str
    identifier: str
    fields: tuple[SiiField, ...]
    unparsed_lines: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class SiiDocument:
    """Parsed SII structure plus source needed for exact unedited serialization."""

    source: str
    blocks: tuple[SiiBlock, ...]

    def serialize(self) -> str:
        """Return original source exactly; mutation APIs are introduced later."""
        return self.source


def parse_sii(source: str) -> SiiDocument:
    """Parse plaintext SII blocks without normalizing unknown content or ordering."""
    lines = source.splitlines(keepends=True)
    if not lines or lines[0].lstrip("\ufeff").rstrip("\r\n") != "SiiNunit":
        raise SiiParseError("expected SiiNunit plaintext header")

    blocks: list[SiiBlock] = []
    active_type: str | None = None
    active_identifier: str | None = None
    fields: list[SiiField] = []
    unparsed: list[str] = []
    outer_open = False
    saw_outer_braces = False

    for line in lines[1:]:
        stripped = line.strip()
        if active_type is None:
            if not stripped:
                continue
            if stripped == "{":
                outer_open = True
                saw_outer_braces = True
                continue
            if stripped == "}":
                outer_open = False
                continue
            match = _BLOCK.match(line)
            if match:
                active_type = match.group("type")
                active_identifier = match.group("identifier")
                fields = []
                unparsed = []
                continue
            raise SiiParseError(f"unexpected document line: {stripped!r}")

        if stripped == "}":
            blocks.append(
                SiiBlock(active_type, active_identifier or "", tuple(fields), tuple(unparsed))
            )
            active_type = None
            active_identifier = None
            continue
        match = _FIELD.match(line)
        if not match:
            unparsed.append(line)
            continue
        key = match.group("key")
        indexed = _LIST_KEY.match(key)
        fields.append(
            SiiField(key, match.group("value"), int(indexed.group("index")) if indexed else None)
        )

    if active_type is not None:
        raise SiiParseError("unterminated SII block")
    if not saw_outer_braces or outer_open:
        raise SiiParseError("missing SII document braces")
    return SiiDocument(source, tuple(blocks))
