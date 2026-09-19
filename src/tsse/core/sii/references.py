"""Immutable typed unit-reference and graph resolution for SiiN documents."""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import StrEnum

from tsse.core.sii.parser import SiiBlock, SiiDocument

_UNIT_ID = re.compile(r"^[A-Za-z0-9_.-]+$")


class ReferenceStatus(StrEnum):
    """The complete, side-effect-free outcome of inspecting a unit reference."""

    VALID = "valid"
    NULL = "null"
    MISSING_TARGET = "missing-target"
    WRONG_TARGET_TYPE = "wrong-target-type"
    MALFORMED = "malformed"


class ReferenceResolutionError(ValueError):
    """Base error raised when a typed reference cannot resolve safely."""


class MalformedReferenceError(ReferenceResolutionError):
    """A scalar is not legal unit-reference syntax."""


class MissingReferenceTargetError(ReferenceResolutionError):
    """A syntactically valid unit ID has no corresponding block."""


class WrongReferenceTypeError(ReferenceResolutionError):
    """A target exists but is not one of the caller's expected types."""


class DuplicateUnitIdentifierError(ReferenceResolutionError):
    """The document contains duplicate IDs, so resolution would be ambiguous."""


@dataclass(frozen=True, slots=True)
class TypedUnitReference:
    """Raw field value plus the target type constraint established by a caller."""

    raw: str
    expected_types: tuple[str, ...]

    @classmethod
    def create(
        cls, raw: str, expected_type: str | tuple[str, ...] | None = None
    ) -> TypedUnitReference:
        if expected_type is None:
            expected: tuple[str, ...] = ()
        elif isinstance(expected_type, tuple):
            expected = expected_type
        else:
            expected = (expected_type,)
        return cls(raw, expected)

    @property
    def target_id(self) -> str | None:
        """Return a valid target ID, or ``None`` for null/malformed scalars."""
        return self.raw if self.raw != "null" and _UNIT_ID.fullmatch(self.raw) else None


@dataclass(frozen=True, slots=True)
class ReferenceResolution:
    """A non-mutating inspection result; ``target`` exists only when valid."""

    reference: TypedUnitReference
    status: ReferenceStatus
    target: SiiBlock | None


class SiiGraph:
    """Read-only block index and typed resolver over one :class:`SiiDocument`."""

    def __init__(self, document: SiiDocument) -> None:
        self._document = document
        blocks: dict[str, SiiBlock] = {}
        duplicates: set[str] = set()
        for block in document.blocks:
            if block.identifier in blocks:
                duplicates.add(block.identifier)
            else:
                blocks[block.identifier] = block
        self._blocks = blocks
        self._duplicates = frozenset(duplicates)

    @property
    def document(self) -> SiiDocument:
        """Return the original immutable document without changing it."""
        return self._document

    def unit(self, identifier: str) -> SiiBlock:
        """Resolve one unique unit ID or raise a typed error."""
        if identifier in self._duplicates:
            raise DuplicateUnitIdentifierError(f"duplicate SII unit identifier: {identifier}")
        try:
            return self._blocks[identifier]
        except KeyError as error:
            raise MissingReferenceTargetError(f"missing SII unit: {identifier}") from error

    def inspect(self, reference: TypedUnitReference) -> ReferenceResolution:
        """Classify a reference without raising or mutating the AST."""
        if reference.raw == "null":
            return ReferenceResolution(reference, ReferenceStatus.NULL, None)
        target_id = reference.target_id
        if target_id is None:
            return ReferenceResolution(reference, ReferenceStatus.MALFORMED, None)
        if target_id in self._duplicates or target_id not in self._blocks:
            return ReferenceResolution(reference, ReferenceStatus.MISSING_TARGET, None)
        target = self._blocks[target_id]
        if reference.expected_types and target.type_name not in reference.expected_types:
            return ReferenceResolution(reference, ReferenceStatus.WRONG_TARGET_TYPE, target)
        return ReferenceResolution(reference, ReferenceStatus.VALID, target)

    def resolve(self, reference: TypedUnitReference) -> SiiBlock | None:
        """Resolve valid references, return ``None`` for null, else raise typed errors."""
        result = self.inspect(reference)
        if result.status is ReferenceStatus.VALID:
            return result.target
        if result.status is ReferenceStatus.NULL:
            return None
        if result.status is ReferenceStatus.MALFORMED:
            raise MalformedReferenceError(f"malformed SII unit reference: {reference.raw!r}")
        if result.status is ReferenceStatus.WRONG_TARGET_TYPE:
            expected = ", ".join(reference.expected_types)
            actual = result.target.type_name if result.target else "unknown"
            raise WrongReferenceTypeError(f"expected {expected}, found {actual}: {reference.raw}")
        raise MissingReferenceTargetError(f"missing SII unit reference: {reference.raw}")

    def field_reference(
        self, block: SiiBlock, field_name: str, expected_type: str | tuple[str, ...] | None = None
    ) -> TypedUnitReference:
        """Build a typed reference from one scalar field, rejecting ambiguity."""
        fields = [
            field
            for field in block.fields
            if field.name == field_name and field.array_index is None
        ]
        if len(fields) != 1:
            raise ReferenceResolutionError(
                f"expected exactly one scalar {block.identifier}.{field_name}, found {len(fields)}"
            )
        return TypedUnitReference.create(fields[0].value, expected_type)

    def indexed_references(
        self, block: SiiBlock, field_name: str, expected_type: str | tuple[str, ...] | None = None
    ) -> tuple[tuple[int, TypedUnitReference], ...]:
        """Return indexed references in numeric index order without compacting gaps."""
        fields = sorted(
            (
                field
                for field in block.fields
                if field.name == field_name and field.array_index is not None
            ),
            key=lambda field: field.array_index if field.array_index is not None else -1,
        )
        return tuple(
            (field.array_index or 0, TypedUnitReference.create(field.value, expected_type))
            for field in fields
        )

    def follow(
        self, start: SiiBlock, *relationships: tuple[str, str | tuple[str, ...] | None]
    ) -> tuple[SiiBlock, ...]:
        """Follow observed scalar relationships, stopping at an explicit null reference."""
        chain = [start]
        current = start
        for field_name, expected_type in relationships:
            target = self.resolve(self.field_reference(current, field_name, expected_type))
            if target is None:
                break
            chain.append(target)
            current = target
        return tuple(chain)
