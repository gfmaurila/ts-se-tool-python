"""GUI-neutral orchestration for a selected save editor session."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path

from tsse.application.compatibility import CompatibilityAssessment
from tsse.application.garage_editor import set_garage_status
from tsse.application.garage_relocation import sell_garage
from tsse.application.player_editor import (
    set_company_name,
    set_experience,
    set_gender,
    set_hq_city,
    set_money,
    set_skill,
)
from tsse.application.save_edit_service import ProductionSaveWriteResult, SaveEditService
from tsse.core.sii import SiiDocument, parse_sii
from tsse.infrastructure.decoder import SiiDecoder

Mutation = Callable[[SiiDocument], SiiDocument]


class PendingChangeDecision(StrEnum):
    SAVE = "save"
    DISCARD = "discard"
    CANCEL = "cancel"


@dataclass(frozen=True, slots=True)
class EditorSaveState:
    """Persisted document and compatibility state returned after every reload."""

    document: SiiDocument
    compatibility: CompatibilityAssessment

    @property
    def write_allowed(self) -> bool:
        return self.compatibility.write_allowed


class EditorService:
    """Load/reload and safely apply an existing domain mutation to one save."""

    def __init__(
        self, editor: SaveEditService | None = None, decoder: SiiDecoder | None = None
    ) -> None:
        self._editor = editor or SaveEditService()
        self._decoder = decoder or SiiDecoder()

    def load(self, game_sii: Path, compatibility: CompatibilityAssessment) -> EditorSaveState:
        decoded = self._decoder.decode_file(game_sii)
        return EditorSaveState(parse_sii(decoded.data.decode("utf-8")), compatibility)

    def apply(
        self, game_sii: Path, compatibility: CompatibilityAssessment, mutation: Mutation
    ) -> tuple[ProductionSaveWriteResult, EditorSaveState]:
        result = self._editor.save(game_sii, mutation, compatibility=compatibility)
        return result, self.load(game_sii, compatibility)


class PlayerEditorSession:
    """Reusable pending Player edit state; persistence remains in EditorService."""

    def __init__(self, state: EditorSaveState) -> None:
        self._persisted = state
        self.experience = self._value("economy", "experience_points")
        self.adr = self._value("economy", "adr")
        self.male = self._value("user_profile", "male") == "true"
        self._initial = (self.experience, self.adr, self.male)

    def _value(self, block_type: str, key: str) -> str:
        block = next(
            block for block in self._persisted.document.blocks if block.type_name == block_type
        )
        return next(field.value for field in block.fields if field.key == key)

    @property
    def dirty(self) -> bool:
        return (self.experience, self.adr, self.male) != self._initial

    @property
    def write_allowed(self) -> bool:
        return self._persisted.write_allowed

    def discard(self) -> None:
        self.experience, self.adr, self.male = self._initial

    def save(self, service: EditorService, game_sii: Path) -> ProductionSaveWriteResult:
        if not self.dirty:
            raise ValueError("player editor has no pending changes")

        def mutation(document: SiiDocument) -> SiiDocument:
            edited = set_experience(document, int(self.experience))
            edited = set_skill(edited, "adr", int(self.adr))
            return set_gender(edited, self.male)

        result, reloaded = service.apply(game_sii, self._persisted.compatibility, mutation)
        self._persisted = reloaded
        self.experience = self._value("economy", "experience_points")
        self.adr = self._value("economy", "adr")
        self.male = self._value("user_profile", "male") == "true"
        self._initial = (self.experience, self.adr, self.male)
        return result


class CompanyEditorSession:
    """Pending mutable Company fields; collections and drivers remain read-only."""

    def __init__(self, state: EditorSaveState) -> None:
        self._persisted = state
        self.name = self._value("user_profile", "company_name").strip('"')
        self.money = self._value("bank", "money_account")
        self.hq_city = self._value("player", "hq_city")
        self._initial = (self.name, self.money, self.hq_city)

    def _value(self, block_type: str, key: str) -> str:
        block = next(
            block for block in self._persisted.document.blocks if block.type_name == block_type
        )
        return next(field.value for field in block.fields if field.key == key)

    @property
    def dirty(self) -> bool:
        return (self.name, self.money, self.hq_city) != self._initial

    @property
    def write_allowed(self) -> bool:
        return self._persisted.write_allowed

    def discard(self) -> None:
        self.name, self.money, self.hq_city = self._initial

    def save(self, service: EditorService, game_sii: Path) -> ProductionSaveWriteResult:
        def mutation(document: SiiDocument) -> SiiDocument:
            edited = set_company_name(document, self.name)
            edited = set_money(edited, int(self.money))
            return set_hq_city(edited, self.hq_city)

        result, self._persisted = service.apply(game_sii, self._persisted.compatibility, mutation)
        self.name = self._value("user_profile", "company_name").strip('"')
        self.money = self._value("bank", "money_account")
        self.hq_city = self._value("player", "hq_city")
        self._initial = (self.name, self.money, self.hq_city)
        return result


class GarageEditorSession:
    """List/read proven garage status and persist existing garage mutations."""

    def __init__(self, state: EditorSaveState) -> None:
        self._persisted = state
        self._initial_statuses = self._read_statuses()
        self._statuses = dict(self._initial_statuses)
        self.selected_identifier: str | None = None

    def _read_statuses(self) -> dict[str, int]:
        return {
            block.identifier: int(
                next(field.value for field in block.fields if field.key == "status")
            )
            for block in self._persisted.document.blocks
            if block.type_name == "garage"
        }

    @property
    def write_allowed(self) -> bool:
        return self._persisted.write_allowed

    @property
    def garages(self) -> tuple[str, ...]:
        return tuple(self._statuses)

    @property
    def dirty(self) -> bool:
        return self._statuses != self._initial_statuses

    @property
    def is_dirty(self) -> bool:
        return self.dirty

    def select(self, identifier: str | None) -> None:
        if identifier is not None and identifier not in self._statuses:
            raise ValueError(f"garage does not exist: {identifier}")
        self.selected_identifier = identifier

    def status(self, identifier: str | None = None) -> int:
        target = identifier if identifier is not None else self.selected_identifier
        if target is None:
            raise ValueError("garage is not selected")
        return self._statuses[target]

    @property
    def hq_identifier(self) -> str | None:
        player = next(
            (block for block in self._persisted.document.blocks if block.type_name == "player"),
            None,
        )
        if player is None:
            return None
        hq = next((field.value for field in player.fields if field.key == "hq_city"), None)
        return hq if hq in self._statuses else None

    def set_pending_status(self, identifier: str, status: int) -> None:
        if identifier not in self._statuses:
            raise ValueError(f"garage does not exist: {identifier}")
        if status < 0:
            raise ValueError("garage status must be non-negative")
        self._statuses[identifier] = status

    def discard(self) -> None:
        self._statuses = dict(self._initial_statuses)

    def save(self, service: EditorService, game_sii: Path) -> ProductionSaveWriteResult:
        if not self.dirty:
            raise ValueError("garage editor has no pending changes")

        def mutation(document: SiiDocument) -> SiiDocument:
            edited = document
            for identifier, status in self._statuses.items():
                if self._initial_statuses.get(identifier) != status:
                    edited = set_garage_status(edited, identifier, status)
            return edited

        result, self._persisted = service.apply(
            game_sii, self._persisted.compatibility, mutation
        )
        self._initial_statuses = self._read_statuses()
        self._statuses = dict(self._initial_statuses)
        return result

    def set_status(
        self, service: EditorService, game_sii: Path, identifier: str, status: int
    ) -> ProductionSaveWriteResult:
        result, self._persisted = service.apply(
            game_sii,
            self._persisted.compatibility,
            lambda document: set_garage_status(document, identifier, status),
        )
        self._initial_statuses = self._read_statuses()
        self._statuses = dict(self._initial_statuses)
        return result

    def sell(
        self, service: EditorService, game_sii: Path, identifier: str, hq_identifier: str
    ) -> ProductionSaveWriteResult:
        result, self._persisted = service.apply(
            game_sii,
            self._persisted.compatibility,
            lambda document: sell_garage(document, identifier, hq_identifier),
        )
        self._initial_statuses = self._read_statuses()
        self._statuses = dict(self._initial_statuses)
        return result


def resolve_pending_change(
    session: PlayerEditorSession,
    decision: PendingChangeDecision,
    service: EditorService,
    game_sii: Path,
) -> bool:
    """Return whether navigation may continue; Save follows the central policy."""
    if not session.dirty:
        return True
    if decision is PendingChangeDecision.CANCEL:
        return False
    if decision is PendingChangeDecision.DISCARD:
        session.discard()
        return True
    if not session.write_allowed:
        return False
    session.save(service, game_sii)
    return True
