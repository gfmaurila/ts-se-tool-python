"""Transactional Cargo Market seed operations from the legacy UI."""

from __future__ import annotations

import random
import re
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from tsse.application.editor_service import EditorSaveState, EditorService
from tsse.application.save_edit_service import ProductionSaveWriteResult
from tsse.core.sii import SiiBlock, SiiDocument, parse_sii


class CargoMarketError(ValueError):
    """Raised for an invalid company, city, or seed collection."""


RandomSource = Callable[[int, int], int]


@dataclass(frozen=True)
class CompanyIdentity:
    identifier: str
    company_type: str
    city: str


@dataclass(frozen=True, slots=True)
class CargoMarketEntry:
    """Stable Cargo Market row identity and resolved seed state."""

    identifier: str
    company_type: str
    city: str
    seeds: tuple[str, ...]


def list_companies(document: SiiDocument) -> tuple[CargoMarketEntry, ...]:
    """Resolve Cargo Market companies using the existing legacy rules."""
    entries: list[CargoMarketEntry] = []
    for block in document.blocks:
        if block.type_name != "company":
            continue
        identity = company_identity(block.identifier)
        entries.append(
            CargoMarketEntry(
                identity.identifier, identity.company_type, identity.city, tuple(_seeds(block))
            )
        )
    return tuple(entries)


class CargoMarketEditorSession:
    """Pending Cargo Market operation backed by the existing mutation functions."""

    def __init__(self, state: EditorSaveState) -> None:
        self._persisted = state
        self.selected_identifier: str | None = None
        self._pending_operation: str | None = None

    @property
    def entries(self) -> tuple[CargoMarketEntry, ...]:
        return list_companies(self._persisted.document)

    @property
    def write_allowed(self) -> bool:
        return self._persisted.write_allowed

    @property
    def dirty(self) -> bool:
        return self._pending_operation is not None

    @property
    def is_dirty(self) -> bool:
        return self.dirty

    @property
    def pending_operation(self) -> str | None:
        return self._pending_operation

    def select(self, identifier: str | None) -> None:
        valid = {entry.identifier for entry in self.entries}
        if identifier is not None and identifier not in valid:
            raise CargoMarketError(f"company does not exist: {identifier}")
        self.selected_identifier = identifier

    def set_pending_operation(self, operation: str) -> None:
        if operation not in {"randomize", "reset"}:
            raise CargoMarketError(f"unsupported Cargo Market operation: {operation}")
        if self.selected_identifier is None:
            raise CargoMarketError("Cargo Market company is not selected")
        self._pending_operation = operation

    def selected_entry(self) -> CargoMarketEntry | None:
        return next(
            (entry for entry in self.entries if entry.identifier == self.selected_identifier), None
        )

    def discard(self) -> None:
        self._pending_operation = None

    def save(self, service: EditorService, game_sii: Path) -> ProductionSaveWriteResult:
        if not self.dirty or self.selected_identifier is None or self._pending_operation is None:
            raise ValueError("Cargo Market editor has no pending changes")
        identifier = self.selected_identifier
        operation = self._pending_operation

        def mutation(document: SiiDocument) -> SiiDocument:
            if operation == "reset":
                return reset_company(document, identifier)
            return randomize_company(document, identifier)

        result, reloaded = service.apply(game_sii, self._persisted.compatibility, mutation)
        self._persisted = reloaded
        self._pending_operation = None
        self.select(identifier if any(entry.identifier == identifier for entry in self.entries) else None)
        return result


def company_identity(identifier: str) -> CompanyIdentity:
    match = re.fullmatch(r"company\.volatile\.([^.]+)\.(.+)", identifier)
    if match is None:
        raise CargoMarketError(f"invalid volatile company identifier: {identifier}")
    return CompanyIdentity(identifier, match.group(1), match.group(2))


def resolve_company(document: SiiDocument, identifier: str) -> SiiBlock:
    company_identity(identifier)
    block = next((item for item in document.blocks if item.identifier == identifier), None)
    if block is None:
        raise CargoMarketError(f"company reference is missing: {identifier}")
    if block.type_name != "company":
        raise CargoMarketError(f"company has unexpected type: {block.type_name}")
    _seeds(block)
    return block


def randomize_company(
    document: SiiDocument,
    identifier: str,
    random_source: RandomSource = random.randrange,
) -> SiiDocument:
    block = resolve_company(document, identifier)
    _require_real_company(block)
    game_time = _game_time(document)
    values: list[str | int] = [game_time + _offset(random_source) for _ in _seeds(block)]
    return _replace_seed_collections(document, {identifier: values})


def reset_company(document: SiiDocument, identifier: str) -> SiiDocument:
    block = resolve_company(document, identifier)
    _require_real_company(block)
    return _replace_seed_collections(document, {identifier: []})


def randomize_city(
    document: SiiDocument,
    city: str,
    random_source: RandomSource = random.randrange,
) -> SiiDocument:
    targets = _real_companies_for_city(document, city)
    if not targets:
        raise CargoMarketError(f"city has no non-excluded companies: {city}")
    game_time = _game_time(document)
    values: dict[str, list[str | int]] = {
        block.identifier: [game_time + _offset(random_source) for _ in _seeds(block)]
        for block in targets
    }
    return _replace_seed_collections(document, values)


def reset_city(document: SiiDocument, city: str) -> SiiDocument:
    targets = _real_companies_for_city(document, city)
    if not targets:
        raise CargoMarketError(f"city has no non-excluded companies: {city}")
    return _replace_seed_collections(document, {block.identifier: [] for block in targets})


def _offset(random_source: RandomSource) -> int:
    value = random_source(180, 1800)
    if not isinstance(value, int) or not 180 <= value < 1800:
        raise CargoMarketError("random source returned an invalid legacy offset")
    return value


def _game_time(document: SiiDocument) -> int:
    economy = next((block for block in document.blocks if block.type_name == "economy"), None)
    if economy is None:
        raise CargoMarketError("economy block is missing")
    field = next((item for item in economy.fields if item.key == "game_time"), None)
    if field is None:
        raise CargoMarketError("economy.game_time is missing")
    try:
        return int(field.value)
    except ValueError as error:
        raise CargoMarketError("economy.game_time is not an integer") from error


def _seeds(block: SiiBlock) -> list[str]:
    count_field = next((field for field in block.fields if field.key == "cargo_offer_seeds"), None)
    if count_field is None:
        raise CargoMarketError(f"missing cargo_offer_seeds: {block.identifier}")
    try:
        count = int(count_field.value)
    except ValueError as error:
        raise CargoMarketError(f"invalid cargo_offer_seeds count: {block.identifier}") from error
    values = {
        field.array_index: field.value
        for field in block.fields
        if field.name == "cargo_offer_seeds" and field.array_index is not None
    }
    if count < 0 or sorted(values) != list(range(count)):
        raise CargoMarketError(f"inconsistent cargo_offer_seeds: {block.identifier}")
    for value in values.values():
        try:
            if int(value) < 0:
                raise ValueError
        except ValueError as error:
            raise CargoMarketError(f"invalid cargo seed: {block.identifier}") from error
    return [values[index] for index in range(count)]


def _require_real_company(block: SiiBlock) -> None:
    if not _collection_count(block, "job_offer"):
        raise CargoMarketError(f"company is excluded by legacy city model: {block.identifier}")


def _real_companies_for_city(document: SiiDocument, city: str) -> list[SiiBlock]:
    companies = []
    for block in document.blocks:
        if block.type_name != "company":
            continue
        identity = company_identity(block.identifier)
        if identity.city == city and _collection_count(block, "job_offer"):
            _seeds(block)
            companies.append(block)
    if not any(
        block.type_name == "company" and company_identity(block.identifier).city == city
        for block in document.blocks
    ):
        raise CargoMarketError(f"city is not present: {city}")
    return companies


def _collection_count(block: SiiBlock, name: str) -> int:
    field = next((item for item in block.fields if item.key == name), None)
    if field is None:
        return 0
    try:
        count = int(field.value)
    except ValueError as error:
        raise CargoMarketError(f"invalid {name} count: {block.identifier}") from error
    values = [item for item in block.fields if item.name == name and item.array_index is not None]
    indices = [item.array_index for item in values]
    if count < 0 or sorted(index for index in indices if index is not None) != list(range(count)):
        raise CargoMarketError(f"inconsistent {name}: {block.identifier}")
    return count


def _replace_seed_collections(
    document: SiiDocument, changes: dict[str, list[str | int]]
) -> SiiDocument:
    blocks = {block.identifier: block for block in document.blocks}
    for identifier, _values in changes.items():
        block = blocks.get(identifier)
        if block is None or block.type_name != "company":
            raise CargoMarketError(f"company is missing during mutation: {identifier}")
        _seeds(block)
    source = document.source
    for identifier, values in sorted(changes.items(), reverse=True):
        block = blocks[identifier]
        header = re.escape(f"company : {identifier} {{")
        match = re.search(rf"(?s)({header})(?P<body>.*?)(^}})", source, re.MULTILINE)
        if match is None:
            raise CargoMarketError(f"could not locate company source: {identifier}")
        replacement = "\n cargo_offer_seeds: " + str(len(values)) + "\n" + "".join(
            f" cargo_offer_seeds[{index}]: {value}\n" for index, value in enumerate(values)
        )
        body, count = re.subn(
            r"(?m)^[ \t]*cargo_offer_seeds:.*\n(?:[ \t]*cargo_offer_seeds\[\d+\]:.*\n)*",
            replacement,
            match.group("body"),
            count=1,
        )
        if count != 1:
            raise CargoMarketError(f"could not update cargo_offer_seeds: {identifier}")
        source = source[: match.start("body")] + body + source[match.end("body") :]
    return parse_sii(source)
