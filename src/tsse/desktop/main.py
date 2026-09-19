"""PySide6 shell for safe, service-backed profile and save operations."""

from __future__ import annotations

import sys
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from pathlib import Path
from typing import cast

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
    QDialog,
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from tsse.application import (
    ProfileCloner,
    ProfileIdentityEditor,
    ProfileInfoService,
    ProfileSettingsZip,
    SaveEditService,
    profile_directory_identity,
    validate_profile_name,
)
from tsse.application.compatibility import GameVersion, SaveDiagnostic, SaveDiagnosticService
from tsse.config import GameRootStore
from tsse.core.profiles import Game, Profile, SaveSlot
from tsse.infrastructure.filesystem import DiscoverySettings, ProfileDiscovery

_SETTINGS_FILES = ["config.cfg", "config_local.cfg", "controls.sii"]


class MainWindow(QMainWindow):
    """UI adapter: selections are immutable objects and writes use application services."""

    def __init__(
        self,
        discovery: ProfileDiscovery,
        settings_store: GameRootStore | None = None,
        *,
        diagnostics: SaveDiagnosticService | None = None,
        profile_info: ProfileInfoService | None = None,
        cloner: ProfileCloner | None = None,
        identity_editor: ProfileIdentityEditor | None = None,
        settings_zip: ProfileSettingsZip | None = None,
        save_editor: SaveEditService | None = None,
    ) -> None:
        super().__init__()
        self._discovery = discovery
        self._settings_store = settings_store or GameRootStore()
        self._diagnostics = diagnostics or SaveDiagnosticService()
        self._profile_info = profile_info or ProfileInfoService()
        self._cloner = cloner or ProfileCloner()
        self._identity_editor = identity_editor or ProfileIdentityEditor()
        self._settings_zip = settings_zip or ProfileSettingsZip()
        self._save_editor = save_editor or SaveEditService()
        for configured_game in Game:
            self._discovery.set_configured_root(
                configured_game, self._settings_store.get_root(configured_game)
            )
        self._profiles: tuple[Profile, ...] = ()
        self._busy = False
        self.setWindowTitle("TS SE Tool Python")
        self._build_ui()
        self.game.currentIndexChanged.connect(self.refresh_profiles)
        self.profile.currentIndexChanged.connect(self._on_profile_selected)
        self.save.currentIndexChanged.connect(self._on_save_selected)
        self.refresh_profiles()

    def _build_ui(self) -> None:
        self.game, self.profile, self.save, self.backup = (
            QComboBox(),
            QComboBox(),
            QComboBox(),
            QComboBox(),
        )
        self.refresh_profiles_button, self.refresh_saves_button = (
            QPushButton("Refresh profiles"),
            QPushButton("Refresh saves"),
        )
        self.root_settings_button = QPushButton("Game roots…")
        self.rename_button, self.clone_button = (
            QPushButton("Rename profile…"),
            QPushButton("Clone profile…"),
        )
        self.export_settings_button, self.import_settings_button = (
            QPushButton("Export settings…"),
            QPushButton("Import settings…"),
        )
        self.refresh_backups_button, self.restore_backup_button = (
            QPushButton("Refresh backups"),
            QPushButton("Restore selected backup…"),
        )
        self.profile_details, self.save_details = (
            QLabel("No profile selected."),
            QLabel("No save selected."),
        )
        self.compatibility_details, self.message = QLabel("UNKNOWN — WRITE BLOCKED"), QLabel()
        self.message.setWordWrap(True)
        for label in (self.profile_details, self.save_details, self.compatibility_details):
            label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        for game in Game:
            self.game.addItem(game.documents_folder_name, game)

        root, selector = QVBoxLayout(), QFormLayout()
        selector.addRow("Game", self._with_button(self.game, self.root_settings_button))
        selector.addRow("Profile", self._with_button(self.profile, self.refresh_profiles_button))
        selector.addRow("Save", self._with_button(self.save, self.refresh_saves_button))
        root.addLayout(selector)
        root.addWidget(QLabel("Compatibility / save diagnostics"))
        root.addWidget(self.compatibility_details)
        root.addWidget(self.save_details)
        tabs = QTabWidget()
        profile_tab, profile_layout = QWidget(), QVBoxLayout()
        profile_tab.setLayout(profile_layout)
        profile_layout.addWidget(QLabel("Profile information"))
        profile_layout.addWidget(self.profile_details)
        profile_layout.addWidget(self.rename_button)
        profile_layout.addWidget(self.clone_button)
        settings_tab, settings_layout = QWidget(), QVBoxLayout()
        settings_tab.setLayout(settings_layout)
        settings_layout.addWidget(self.export_settings_button)
        settings_layout.addWidget(self.import_settings_button)
        settings_layout.addStretch()
        backups_tab, backups_layout = QWidget(), QFormLayout()
        backups_tab.setLayout(backups_layout)
        backups_layout.addRow("TSSE backup", self.backup)
        backups_layout.addRow(self.refresh_backups_button)
        backups_layout.addRow(self.restore_backup_button)
        tabs.addTab(profile_tab, "Profile")
        tabs.addTab(settings_tab, "Settings")
        tabs.addTab(backups_tab, "Backups")
        root.addWidget(tabs)
        root.addWidget(self.message)
        container = QWidget()
        container.setLayout(root)
        self.setCentralWidget(container)
        self.setStatusBar(self.statusBar())
        self.refresh_profiles_button.clicked.connect(self.refresh_profiles)
        self.refresh_saves_button.clicked.connect(self.refresh_saves)
        self.root_settings_button.clicked.connect(self.open_settings)
        self.rename_button.clicked.connect(self.rename_selected_profile_dialog)
        self.clone_button.clicked.connect(self.clone_selected_profile_dialog)
        self.export_settings_button.clicked.connect(self.export_settings_dialog)
        self.import_settings_button.clicked.connect(self.import_settings_dialog)
        self.refresh_backups_button.clicked.connect(self.refresh_backups)
        self.restore_backup_button.clicked.connect(self.restore_selected_backup_dialog)

    @staticmethod
    def _with_button(widget: QWidget, button: QPushButton) -> QWidget:
        row, layout = QWidget(), QHBoxLayout()
        row.setLayout(layout)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(widget)
        layout.addWidget(button)
        return row

    @property
    def selected_game(self) -> Game:
        return Game(self.game.currentData())

    @property
    def selected_profile(self) -> Profile | None:
        return cast(Profile | None, self.profile.currentData())

    @property
    def selected_save(self) -> SaveSlot | None:
        return cast(SaveSlot | None, self.save.currentData())

    @contextmanager
    def _busy_operation(self) -> Iterator[bool]:
        if self._busy:
            yield False
            return
        self._busy = True
        QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
        try:
            yield True
        finally:
            QApplication.restoreOverrideCursor()
            self._busy = False

    def _status(self, text: str) -> None:
        self.message.setText(text)
        self.statusBar().showMessage(text)

    def refresh_profiles(self) -> None:
        """Reload profiles for the selected game, discarding old game objects."""
        with self._busy_operation() as active:
            if not active:
                return
            self._reload_profiles()

    def _reload_profiles(self) -> None:
        """Reload selection data when a completed profile operation changes it."""
        game = self.selected_game
        self._profiles = self._discovery.discover_profiles(game)
        self.profile.blockSignals(True)
        self.profile.clear()
        for item in self._profiles:
            self.profile.addItem(self._profile_display(item), item)
        self.profile.blockSignals(False)
        self.refresh_saves()
        root = self._discovery.root_for_game(game)
        self._status(
            f"{game.documents_folder_name}: {len(self._profiles)} profiles found in {root}"
        )

    def refresh_saves(self) -> None:
        """Refresh read-only save choices; no selected save is ever written here."""
        profile = self.selected_profile
        self.save.blockSignals(True)
        self.save.clear()
        self.save.blockSignals(False)
        self.backup.clear()
        if profile is None:
            self.profile_details.setText("No profile selected.")
            self.save_details.setText("No save selected.")
            self.compatibility_details.setText("UNKNOWN — WRITE BLOCKED")
            self._update_actions()
            return
        for slot in profile.save_slots:
            self.save.addItem(slot.name, slot)
        self._show_profile(profile)
        self._on_save_selected()
        self._status(f"{len(profile.save_slots)} saves found for {self._profile_display(profile)}")

    def _on_profile_selected(self) -> None:
        self.refresh_saves()

    def _on_save_selected(self) -> None:
        save = self.selected_save
        if save is None:
            self.save_details.setText("No save selected.")
            self.compatibility_details.setText("UNKNOWN — WRITE BLOCKED")
            self._update_actions()
            return
        try:
            diagnostic = self.inspect_selected_save()
        except (OSError, RuntimeError) as error:
            self.save_details.setText(f"Save diagnostic failed: {error}")
            self.compatibility_details.setText("UNKNOWN — WRITE BLOCKED")
            self._status(f"Save diagnostic failed: {error}")
        else:
            self._show_diagnostic(save, diagnostic)
            self.refresh_backups()
        self._update_actions()

    def inspect_selected_save(self, version: GameVersion | None = None) -> SaveDiagnostic:
        save = self._require_save()
        return self._diagnostics.inspect(self.selected_game, save.game_sii, version)

    def _show_profile(self, profile: Profile) -> None:
        try:
            info = self._profile_info.read_profile(profile.profile_sii)
            name, creation = info.profile_name, str(info.creation_time)
        except Exception as error:
            name, creation = profile.profile_id, f"Unavailable ({error})"
        source = "steam_profiles" if profile.is_steam else "profiles"
        details = [
            f"Profile name: {name}",
            f"Directory identity: {profile.profile_id}",
            f"Creation time: {creation}",
            f"Path: {profile.directory}",
            f"Game: {profile.game.documents_folder_name}",
            f"Source: {source}",
        ]
        self.profile_details.setText("\n".join(details))

    @staticmethod
    def _profile_display(profile: Profile) -> str:
        return profile.profile_id + (" (Steam)" if profile.is_steam else "")

    def _show_diagnostic(self, save: SaveSlot, diagnostic: SaveDiagnostic) -> None:
        version = diagnostic.version.value if diagnostic.version else "UNKNOWN"
        permission = "WRITE ALLOWED" if diagnostic.write_allowed else "WRITE BLOCKED"
        self.compatibility_details.setText(
            f"Version: {version} / {diagnostic.compatibility.value.upper()} — {permission}"
        )
        messages = "; ".join(diagnostic.diagnostics) or "OK"
        details = [
            f"Save path: {save.directory}",
            f"Format: {diagnostic.detected_format.value}",
            f"Decoder: {'available' if diagnostic.decoder_available else 'unavailable'}",
            f"Decode: {'PASS' if diagnostic.decode_ok else 'FAIL'}",
            f"Parse: {'PASS' if diagnostic.parse_ok else 'FAIL'}",
            "Block count: "
            f"{diagnostic.block_count if diagnostic.block_count is not None else 'n/a'}",
            f"Diagnostics: {messages}",
        ]
        self.save_details.setText("\n".join(details))
        self._status("Save parsed successfully." if diagnostic.parse_ok else messages)

    def _update_actions(self) -> None:
        profile, save = self.selected_profile is not None, self.selected_save is not None
        for button in (
            self.rename_button,
            self.clone_button,
            self.export_settings_button,
            self.import_settings_button,
        ):
            button.setEnabled(profile and not self._busy)
        self.refresh_backups_button.setEnabled(save and not self._busy)
        self.restore_backup_button.setEnabled(
            save and self.backup.currentData() is not None and not self._busy
        )

    def rename_preview(self, name: str) -> tuple[str, str]:
        normalized = validate_profile_name(name)
        return normalized, profile_directory_identity(normalized)

    def clone_preview(self, name: str) -> tuple[str, str]:
        return self.rename_preview(name)

    def rename_selected_profile(self, name: str) -> None:
        self._identity_editor.rename_directory(self._require_profile().profile_sii, name)
        self._reload_profiles()
        self._status("Profile renamed safely.")

    def clone_selected_profile(self, name: str) -> None:
        self._cloner.clone_named(self._require_profile(), name)
        self._reload_profiles()
        self._status("Profile cloned safely.")

    def rename_selected_profile_dialog(self) -> None:
        self._name_operation_dialog("Rename profile", self.rename_selected_profile)

    def clone_selected_profile_dialog(self) -> None:
        self._name_operation_dialog("Clone profile", self.clone_selected_profile)

    def _name_operation_dialog(self, title: str, action: Callable[[str], None]) -> None:
        if self.selected_profile is None:
            self._status("Select a profile first.")
            return
        dialog, form, name, preview = (
            QDialog(self),
            None,
            QLineEdit(),
            QLabel("Directory identity: —"),
        )
        dialog.setWindowTitle(title)
        form = QFormLayout(dialog)
        form.addRow("New profile name", name)
        form.addRow(preview)
        confirm, cancel, buttons = QPushButton("Confirm"), QPushButton("Cancel"), QHBoxLayout()
        buttons.addWidget(confirm)
        buttons.addWidget(cancel)
        form.addRow(buttons)

        def update(value: str) -> None:
            try:
                display, identity = self.rename_preview(value)
                preview.setText(f"Display name: {display}\nDirectory identity: {identity}")
                confirm.setEnabled(True)
            except ValueError as error:
                preview.setText(str(error))
                confirm.setEnabled(False)

        def perform() -> None:
            display, identity = self.rename_preview(name.text())
            if (
                QMessageBox.question(
                    dialog, "Confirm", f"Use '{display}' with directory identity {identity}?"
                )
                is not QMessageBox.StandardButton.Yes
            ):
                return
            try:
                with self._busy_operation() as active:
                    if active:
                        action(display)
            except (OSError, RuntimeError, ValueError) as error:
                self._show_error(title, error)
                return
            dialog.accept()

        name.textChanged.connect(update)
        confirm.clicked.connect(perform)
        cancel.clicked.connect(dialog.reject)
        update("")
        dialog.exec()

    def export_settings(self, destination: Path, names: list[str] | None = None) -> Path:
        return self._settings_zip.export(
            self._require_profile().directory, destination, names or _SETTINGS_FILES
        )

    def import_settings(self, archive: Path, names: list[str] | None = None) -> tuple[Path, ...]:
        return self._settings_zip.import_(
            archive, self._require_profile().directory, names or _SETTINGS_FILES
        )

    def export_settings_dialog(self) -> None:
        if self.selected_profile is None:
            self._status("Select a profile first.")
            return
        filename, _ = QFileDialog.getSaveFileName(
            self, "Export settings", "settings.zip", "ZIP (*.zip)"
        )
        if not filename:
            return
        try:
            with self._busy_operation() as active:
                if active:
                    self.export_settings(Path(filename))
            self._status("Settings exported safely.")
        except (OSError, RuntimeError) as error:
            self._show_error("Settings export failed", error)

    def import_settings_dialog(self) -> None:
        if self.selected_profile is None:
            self._status("Select a profile first.")
            return
        filename, _ = QFileDialog.getOpenFileName(self, "Import settings", "", "ZIP (*.zip)")
        if (
            not filename
            or QMessageBox.question(self, "Confirm import", "Replace selected profile settings?")
            is not QMessageBox.StandardButton.Yes
        ):
            return
        try:
            with self._busy_operation() as active:
                if active:
                    self.import_settings(Path(filename))
            self._status("Settings imported safely.")
        except (OSError, RuntimeError) as error:
            self._show_error("Settings import failed", error)

    def refresh_backups(self) -> None:
        self.backup.clear()
        save = self.selected_save
        if save is not None:
            for backup in self._save_editor.discover_backups(save.game_sii):
                self.backup.addItem(
                    f"{backup.name} ({backup.stat().st_size} bytes; {backup.stat().st_mtime_ns})",
                    backup,
                )
        self._update_actions()

    def restore_selected_backup(self) -> None:
        backup = self.backup.currentData()
        if not isinstance(backup, Path):
            raise RuntimeError("TSSE backup not selected")
        self._save_editor.restore(self._require_save().game_sii, backup)
        self.refresh_backups()
        self._on_save_selected()
        self._status("Backup restored successfully.")

    def restore_selected_backup_dialog(self) -> None:
        backup = self.backup.currentData()
        if not isinstance(backup, Path):
            self._status("Select a TSSE backup first.")
            return
        if (
            QMessageBox.question(
                self,
                "Confirm restore",
                f"Restore {backup.name}? The current save will be backed up.",
            )
            is not QMessageBox.StandardButton.Yes
        ):
            return
        try:
            with self._busy_operation() as active:
                if active:
                    self.restore_selected_backup()
        except (OSError, RuntimeError) as error:
            self._show_error("Restore failed", error)

    def open_settings(self) -> None:
        """Edit only QSettings-backed roots after profile-collection validation."""
        dialog, form, fields = QDialog(self), None, {}
        dialog.setWindowTitle("Game data directories")
        form = QFormLayout(dialog)
        for game in Game:
            row, field, browse = QHBoxLayout(), QLineEdit(), QPushButton("Browse…")
            current = self._settings_store.get_root(game)
            field.setText(str(current) if current else "")
            browse.clicked.connect(
                lambda _checked=False, target=field: target.setText(
                    QFileDialog.getExistingDirectory(dialog, "Select game data directory")
                    or target.text()
                )
            )
            row.addWidget(field)
            row.addWidget(browse)
            form.addRow(game.documents_folder_name, row)
            fields[game] = field
        save_button, automatic_button, buttons = (
            QPushButton("Save"),
            QPushButton("Reset / automatic"),
            QHBoxLayout(),
        )
        buttons.addWidget(save_button)
        buttons.addWidget(automatic_button)
        form.addRow(buttons)

        def save_roots() -> None:
            for game, field in fields.items():
                text = field.text().strip()
                if not text:
                    self._settings_store.clear_root(game)
                    self._discovery.set_configured_root(game, None)
                    continue
                root = Path(text)
                if not self._discovery.root_has_profile_collections(root):
                    QMessageBox.warning(
                        dialog, "No profiles", f"{root} has no profiles or steam_profiles."
                    )
                    return
                self._settings_store.set_root(game, root)
                self._discovery.set_configured_root(game, root)
            dialog.accept()
            self.refresh_profiles()

        def automatic() -> None:
            for game in Game:
                self._settings_store.clear_root(game)
                self._discovery.set_configured_root(game, None)
            dialog.accept()
            self.refresh_profiles()

        save_button.clicked.connect(save_roots)
        automatic_button.clicked.connect(automatic)
        dialog.exec()

    @staticmethod
    def _show_error(title: str, error: Exception) -> None:
        QMessageBox.warning(None, title, str(error))

    def _require_profile(self) -> Profile:
        if self.selected_profile is None:
            raise RuntimeError("profile not selected")
        return self.selected_profile

    def _require_save(self) -> SaveSlot:
        if self.selected_save is None:
            raise RuntimeError("save not selected")
        return self.selected_save


def create_window(
    documents_directory: Path, settings_store: GameRootStore | None = None
) -> MainWindow:
    """Build a window using explicit Documents configuration."""
    return MainWindow(
        ProfileDiscovery(DiscoverySettings.with_defaults(documents_directory)), settings_store
    )


def main() -> int:
    application = QApplication(sys.argv)
    window = create_window(Path.home() / "Documents")
    window.show()
    return application.exec()


if __name__ == "__main__":
    raise SystemExit(main())
