"""Small GUI-neutral contract for the currently editable feature."""

from __future__ import annotations

from pathlib import Path
from typing import Protocol

from tsse.application.editor_service import EditorService
from tsse.application.save_edit_service import ProductionSaveWriteResult


class EditableFeatureSession(Protocol):
    @property
    def is_dirty(self) -> bool: ...

    @property
    def dirty(self) -> bool: ...

    @property
    def write_allowed(self) -> bool: ...

    def save(self) -> ProductionSaveWriteResult: ...

    def discard(self) -> None: ...


class SessionEditorAdapter:
    """Thin adapter over existing Player/Company sessions and their safe service."""

    def __init__(
        self,
        session: EditableFeatureSession,
        service: EditorService,
        game_sii: Path,
    ) -> None:
        self._session, self._service, self._game_sii = session, service, game_sii

    @property
    def is_dirty(self) -> bool:
        return self._session.dirty

    @property
    def dirty(self) -> bool:
        return self._session.dirty

    @property
    def write_allowed(self) -> bool:
        return self._session.write_allowed

    def save(self) -> ProductionSaveWriteResult:
        return self._session.save(self._service, self._game_sii)

    def discard(self) -> None:
        self._session.discard()

    def rebind(
        self,
        session: EditableFeatureSession,
        service: EditorService,
        game_sii: Path,
    ) -> None:
        self._session, self._service, self._game_sii = session, service, game_sii
