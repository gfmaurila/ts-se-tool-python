"""Shared visual adapter for pending editor changes."""

from __future__ import annotations

from typing import Protocol

from PySide6.QtWidgets import QMessageBox, QWidget

from tsse.application import PendingChangeDecision


class PendingEditor(Protocol):
    @property
    def dirty(self) -> bool: ...

    @property
    def write_allowed(self) -> bool: ...


class PendingChangesPrompt:
    """Ask only when dirty; options derive from the central compatibility result."""

    def decide(self, parent: QWidget, editor: PendingEditor) -> PendingChangeDecision | None:
        if not editor.dirty:
            return PendingChangeDecision.SAVE
        buttons = QMessageBox.StandardButton.Discard | QMessageBox.StandardButton.Cancel
        if editor.write_allowed:
            buttons |= QMessageBox.StandardButton.Save
        answer = QMessageBox.question(parent, "Unsaved changes", "Save pending changes?", buttons)
        if answer is QMessageBox.StandardButton.Save and editor.write_allowed:
            return PendingChangeDecision.SAVE
        if answer is QMessageBox.StandardButton.Discard:
            return PendingChangeDecision.DISCARD
        return PendingChangeDecision.CANCEL


class GarageSaleConfirmation:
    """Separate destructive-action confirmation; never infers a city."""

    def confirm(self, parent: QWidget, identifier: str) -> bool:
        answer = QMessageBox.question(
            parent,
            "Confirm garage sale",
            f'Sell garage "{identifier}"?',
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        return answer is QMessageBox.StandardButton.Yes
