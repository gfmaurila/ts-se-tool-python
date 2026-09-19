import os
from dataclasses import dataclass

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication, QMessageBox, QWidget

from tsse.application import PendingChangeDecision
from tsse.desktop.pending_changes import GarageSaleConfirmation, PendingChangesPrompt


@dataclass
class Editor:
    dirty: bool
    write_allowed: bool


def test_prompt_skips_clean_and_offers_save_only_when_allowed(monkeypatch) -> None:
    app = QApplication.instance() or QApplication([])
    prompt, parent = PendingChangesPrompt(), QWidget()
    assert prompt.decide(parent, Editor(False, False)) is PendingChangeDecision.SAVE
    seen = []

    def question(*args):
        seen.append(args[3])
        return QMessageBox.StandardButton.Save

    monkeypatch.setattr(QMessageBox, "question", question)
    assert prompt.decide(parent, Editor(True, True)) is PendingChangeDecision.SAVE
    assert seen[-1] & QMessageBox.StandardButton.Save
    assert prompt.decide(parent, Editor(True, False)) is PendingChangeDecision.CANCEL
    assert not seen[-1] & QMessageBox.StandardButton.Save
    parent.close()
    assert app is not None


def test_garage_sale_confirmation_uses_stable_identifier(monkeypatch) -> None:
    app = QApplication.instance() or QApplication([])
    parent, seen = QWidget(), []
    monkeypatch.setattr(
        QMessageBox,
        "question",
        lambda *args: seen.append(args) or QMessageBox.StandardButton.No,
    )
    assert not GarageSaleConfirmation().confirm(parent, "garage.stable")
    assert '"garage.stable"' in seen[0][2]
    parent.close()
    assert app is not None
