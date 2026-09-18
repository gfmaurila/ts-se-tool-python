"""PySide6 desktop entry point for safe profile selection."""

from __future__ import annotations

import sys
from pathlib import Path

from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
    QFormLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from tsse.application import ProfileCloner
from tsse.core.profiles import Game, Profile
from tsse.infrastructure.filesystem import DiscoverySettings, ProfileDiscovery


class MainWindow(QMainWindow):
    """Minimal UI that delegates profile operations to application/core services."""

    def __init__(self, discovery: ProfileDiscovery) -> None:
        super().__init__()
        self._discovery = discovery
        self._profiles: tuple[Profile, ...] = ()
        self.setWindowTitle("TS SE Tool Python")
        self.game = QComboBox()
        self.profile = QComboBox()
        self.save = QComboBox()
        self.message = QLabel()
        self.clone_button = QPushButton("Clone selected profile")
        layout = QVBoxLayout()
        form = QFormLayout()
        form.addRow("Game", self.game)
        form.addRow("Profile", self.profile)
        form.addRow("Save", self.save)
        layout.addLayout(form)
        layout.addWidget(self.clone_button)
        layout.addWidget(self.message)
        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)
        for game in Game:
            self.game.addItem(game.documents_folder_name, game)
        self.game.currentIndexChanged.connect(self.refresh_profiles)
        self.profile.currentIndexChanged.connect(self.refresh_saves)
        self.clone_button.clicked.connect(self.clone_selected_profile)
        self.refresh_profiles()

    def refresh_profiles(self) -> None:
        """Refresh profiles for the chosen game without reading save contents."""
        game = Game(self.game.currentData())
        self._profiles = self._discovery.discover_profiles(game)
        self.profile.blockSignals(True)
        self.profile.clear()
        for profile in self._profiles:
            self.profile.addItem(profile.profile_id, profile)
        self.profile.blockSignals(False)
        self.refresh_saves()
        self.message.setText(f"{len(self._profiles)} profiles found")

    def refresh_saves(self) -> None:
        """Refresh valid save slots for the selected profile."""
        profile = self.profile.currentData()
        self.save.clear()
        if profile is None:
            return
        for slot in profile.save_slots:
            self.save.addItem(slot.name, slot)

    def clone_selected_profile(self) -> None:
        """Request explicit confirmation before creating a new profile directory."""
        profile = self.profile.currentData()
        if profile is None:
            self.message.setText("Select a profile before cloning.")
            return
        destination = profile.directory.with_name(f"{profile.directory.name}_clone")
        answer = QMessageBox.question(self, "Confirm clone", f"Create {destination.name}?")
        if answer is not QMessageBox.StandardButton.Yes:
            return
        try:
            ProfileCloner().clone(profile, destination)
        except RuntimeError as error:
            self.message.setText(str(error))
            return
        self.refresh_profiles()
        self.message.setText("Profile cloned safely.")


def create_window(documents_directory: Path) -> MainWindow:
    """Build a window using explicit Documents configuration."""
    return MainWindow(ProfileDiscovery(DiscoverySettings.with_defaults(documents_directory)))


def main() -> int:
    """Start the desktop application with the conventional Documents root."""
    application = QApplication(sys.argv)
    window = create_window(Path.home() / "Documents")
    window.show()
    return application.exec()


if __name__ == "__main__":
    raise SystemExit(main())
