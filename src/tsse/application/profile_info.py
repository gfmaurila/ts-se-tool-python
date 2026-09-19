"""Evidence-bounded profile.sii and info.sii models with safe persistence."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from tsse.application.profile_identity import replace_profile_name
from tsse.core.sii import SaveFormat, SiiBlock, SiiDocument, SiiParseError, parse_sii
from tsse.infrastructure.decoder import SiiDecoder
from tsse.infrastructure.filesystem import SafeSaveWriter, SaveWriteResult


class ProfileInfoError(ValueError):
    """A profile/info document lacks a legacy-proven structure or field."""


@dataclass(frozen=True, slots=True)
class ProfileSiiModel:
    """Read-only view of profile metadata printed by legacy SaveFileProfileData."""

    document: SiiDocument
    profile_name: str
    creation_time: int
    save_time: int


@dataclass(frozen=True, slots=True)
class InfoSiiModel:
    """Read-only view of save metadata printed by legacy SaveFileInfoData."""

    document: SiiDocument
    name: str
    time: int
    file_time: int
    version: int
    info_version: int | None
    players_experience: int | None
    money_account: int | None
    explored_ratio: str | None


@dataclass(frozen=True, slots=True)
class ProfileInfoWriteResult:
    """Safe-write evidence plus the container format observed before decoding."""

    original_format: SaveFormat
    write: SaveWriteResult


def parse_profile_sii(source: str) -> ProfileSiiModel:
    document = _document(source, "profile")
    block = _one_block(document, "user_profile", "profile")
    return ProfileSiiModel(
        document=document,
        profile_name=_display_string(_scalar(block, "profile_name", "profile")),
        creation_time=_integer(_scalar(block, "creation_time", "profile"), "creation_time"),
        save_time=_integer(_scalar(block, "save_time", "profile"), "save_time"),
    )


def parse_info_sii(source: str) -> InfoSiiModel:
    document = _document(source, "info")
    block = _one_block(document, "save_container", "info")
    return InfoSiiModel(
        document=document,
        name=_display_string(_scalar(block, "name", "info")),
        time=_integer(_scalar(block, "time", "info"), "time"),
        file_time=_integer(_scalar(block, "file_time", "info"), "file_time"),
        version=_integer(_scalar(block, "version", "info"), "version"),
        info_version=_optional_integer(block, "info_version"),
        players_experience=_optional_integer(block, "info_players_experience"),
        money_account=_optional_integer(block, "info_money_account"),
        explored_ratio=_optional_scalar(block, "info_explored_ratio"),
    )


def set_info_money_account(document: SiiDocument, money_account: int) -> SiiDocument:
    """Replace the legacy ``info_money_account`` scalar without rebuilding info.sii."""
    if not isinstance(money_account, int):
        raise ProfileInfoError("info_money_account must be an integer")
    block = _one_block(document, "save_container", "info")
    _scalar(block, "info_money_account", "info")
    return parse_sii(_replace_scalar(document, block, "info_money_account", str(money_account)))


class ProfileInfoService:
    """Decode/read and safely persist only legacy-proven profile/info mutations."""

    def __init__(
        self, decoder: SiiDecoder | None = None, writer: SafeSaveWriter | None = None
    ) -> None:
        self._decoder = decoder or SiiDecoder()
        self._writer = writer or SafeSaveWriter()

    def read_profile(self, path: Path) -> ProfileSiiModel:
        return parse_profile_sii(self._decode(path)[0])

    def read_info(self, path: Path) -> InfoSiiModel:
        return parse_info_sii(self._decode(path)[0])

    def rename_profile(self, path: Path, name: str) -> ProfileInfoWriteResult:
        source, original, source_format = self._decoded_source(path, "profile.sii")
        candidate = replace_profile_name(source, name)
        model = parse_profile_sii(candidate)
        if model.profile_name != name.strip(" "):
            raise ProfileInfoError("profile name did not persist in candidate")
        return ProfileInfoWriteResult(
            source_format,
            self._writer.write_text(
                path, candidate, expected_original=original, validator=parse_profile_sii
            ),
        )

    def set_info_money(self, path: Path, money_account: int) -> ProfileInfoWriteResult:
        source, original, source_format = self._decoded_source(path, "info.sii")
        document = parse_info_sii(source).document
        candidate = set_info_money_account(document, money_account).serialize()
        model = parse_info_sii(candidate)
        if model.money_account != money_account:
            raise ProfileInfoError("info money did not persist in candidate")
        return ProfileInfoWriteResult(
            source_format,
            self._writer.write_text(
                path, candidate, expected_original=original, validator=parse_info_sii
            ),
        )

    def _decode(self, path: Path) -> tuple[str, SaveFormat]:
        decoded = self._decoder.decode_file(path)
        try:
            return decoded.data.decode("utf-8"), decoded.source_format
        except UnicodeDecodeError as error:
            raise ProfileInfoError(f"decoded SII is not UTF-8: {path}") from error

    def _decoded_source(self, path: Path, expected_name: str) -> tuple[str, bytes, SaveFormat]:
        if path.name != expected_name:
            raise ProfileInfoError(f"expected {expected_name}: {path}")
        source, source_format = self._decode(path)
        return source, path.read_bytes(), source_format


def _document(source: str, kind: str) -> SiiDocument:
    try:
        return parse_sii(source)
    except SiiParseError as error:
        raise ProfileInfoError(f"{kind}.sii is not valid SiiN") from error


def _one_block(document: SiiDocument, type_name: str, kind: str) -> SiiBlock:
    blocks = [block for block in document.blocks if block.type_name == type_name]
    if len(blocks) != 1:
        raise ProfileInfoError(f"{kind}.sii requires exactly one {type_name} block")
    return blocks[0]


def _scalar(block: SiiBlock, name: str, kind: str) -> str:
    fields = [
        field.value for field in block.fields if field.name == name and field.array_index is None
    ]
    if len(fields) != 1:
        raise ProfileInfoError(f"{kind}.sii requires exactly one {name}")
    return fields[0]


def _optional_scalar(block: SiiBlock, name: str) -> str | None:
    values = [
        field.value for field in block.fields if field.name == name and field.array_index is None
    ]
    if len(values) > 1:
        raise ProfileInfoError(f"info.sii has duplicate {name}")
    return values[0] if values else None


def _integer(value: str, name: str) -> int:
    try:
        return int(value)
    except ValueError as error:
        raise ProfileInfoError(f"{name} must be an integer") from error


def _optional_integer(block: SiiBlock, name: str) -> int | None:
    value = _optional_scalar(block, name)
    return None if value is None else _integer(value, name)


def _display_string(value: str) -> str:
    if len(value) >= 2 and value.startswith('"') and value.endswith('"'):
        return value[1:-1]
    return value


def _replace_scalar(document: SiiDocument, block: SiiBlock, name: str, value: str) -> str:
    header = (
        rf"(?m)^(?P<head>\s*{re.escape(block.type_name)}\s*:\s*"
        rf"{re.escape(block.identifier)}\s*\{{\s*\n)"
    )
    match = re.search(rf"(?s){header}(?P<body>.*?)(?P<end>^\}})", document.source)
    if match is None:
        raise ProfileInfoError(f"could not locate {block.type_name} block for {name}")
    body, count = re.subn(
        rf"(?m)^(?P<prefix>\s*{re.escape(name)}\s*:\s*)[^\r\n]*(?P<ending>\r?\n|$)",
        rf"\g<prefix>{value}\g<ending>",
        match.group("body"),
        count=1,
    )
    if count != 1:
        raise ProfileInfoError(f"could not replace {name}")
    return document.source[: match.start("body")] + body + document.source[match.end("body") :]
