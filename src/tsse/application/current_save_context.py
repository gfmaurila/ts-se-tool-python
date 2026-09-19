"""Authoritative loaded-save context shared by desktop feature editors."""

from __future__ import annotations

from dataclasses import dataclass

from tsse.application.compatibility import CompatibilityAssessment
from tsse.application.editor_service import EditorSaveState, EditorService, GarageEditorSession
from tsse.core.profiles import Game, Profile, SaveSlot


@dataclass(frozen=True, slots=True)
class CurrentSaveContext:
    game: Game
    profile: Profile
    save: SaveSlot
    assessment: CompatibilityAssessment
    editor: EditorService
    state: EditorSaveState

    def garage_session(self) -> GarageEditorSession:
        """Create a feature session from the authoritative loaded state."""
        return GarageEditorSession(self.state)
