"""PySide6 shell for safe, service-backed profile and save operations."""

from __future__ import annotations

import sys
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import cast

from PySide6.QtCore import QSignalBlocker, Qt
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QDialog,
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QTabWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from tsse.application import (
    CargoMarketEditorSession,
    CurrentSaveContext,
    EditorService,
    PendingChangeDecision,
    ProfileCloner,
    ProfileIdentityEditor,
    ProfileInfoService,
    ProfileSettingsZip,
    SaveEditService,
    profile_directory_identity,
    validate_profile_name,
)
from tsse.application.active_editor import EditableFeatureSession, SessionEditorAdapter
from tsse.application.compatibility import (
    CompatibilityRegistry,
    GameVersion,
    SaveDiagnostic,
    SaveDiagnosticService,
)
from tsse.application.editor_service import (
    CompanyEditorSession,
    GarageEditorSession,
    PlayerEditorSession,
)
from tsse.config import GameRootStore
from tsse.core.profiles import Game, Profile, SaveSlot
from tsse.core.sii import SiiDocument, parse_sii
from tsse.desktop.pending_changes import GarageSaleConfirmation, PendingChangesPrompt
from tsse.infrastructure.decoder import SiiDecoder
from tsse.infrastructure.filesystem import DiscoverySettings, ProfileDiscovery

_SETTINGS_FILES = ["config.cfg", "config_local.cfg", "controls.sii"]


@dataclass(frozen=True, slots=True)
class _SaveReloadCandidate:
    context: CurrentSaveContext
    player: PlayerEditorSession | None
    company: CompanyEditorSession | None
    garage: GarageEditorSession
    cargo: CargoMarketEditorSession


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
        editor_service: EditorService | None = None,
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
        self._editor_service = editor_service or EditorService(self._save_editor)
        self.current_save_context: CurrentSaveContext | None = None
        self._active_editor: EditableFeatureSession | None = None
        self._player_session: PlayerEditorSession | None = None
        self._company_session: CompanyEditorSession | None = None
        self._garage_session: GarageEditorSession | None = None
        self._cargo_session: CargoMarketEditorSession | None = None
        self._selected_garage_id: str | None = None
        self._committed_game: Game | None = None
        self._committed_profile: Profile | None = None
        self._committed_save: SaveSlot | None = None
        self._coordinating_context_switch = False
        self._decoder = SiiDecoder()
        for configured_game in Game:
            self._discovery.set_configured_root(
                configured_game, self._settings_store.get_root(configured_game)
            )
        self._profiles: tuple[Profile, ...] = ()
        self._garage_statuses: dict[str, str] = {}
        self._busy = False
        self.setWindowTitle("TS SE Tool Python")
        self._build_ui()
        self.game.currentIndexChanged.connect(self._on_game_combo_changed)
        self.profile.currentIndexChanged.connect(self._on_profile_combo_changed)
        self.save.currentIndexChanged.connect(self._on_save_combo_changed)
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
        self.editor_tabs = tabs
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
        self.player_view = self._player_page()
        self.company_view = self._company_page()
        self.garages_view = self._garage_page()
        self.cargo_market_view = self._cargo_market_page()
        self.freight_market_view = self._readonly_page()
        tabs.addTab(self.player_view, "Player")
        tabs.addTab(self.company_view, "Company")
        tabs.addTab(self.garages_view, "Garages")
        tabs.addTab(self.cargo_market_view, "Cargo Market")
        tabs.addTab(self.freight_market_view, "Freight Market")
        tabs.addTab(settings_tab, "Settings")
        tabs.addTab(backups_tab, "Backups")
        diagnostics_tab, diagnostics_layout = QWidget(), QVBoxLayout()
        diagnostics_tab.setLayout(diagnostics_layout)
        diagnostics_layout.addWidget(QLabel("Save diagnostics"))
        diagnostics_layout.addWidget(self.save_details)
        tabs.addTab(diagnostics_tab, "Diagnostics")
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
        self.editor_tabs.currentChanged.connect(self._on_editor_tab_changed)

    def _on_editor_tab_changed(self, index: int) -> None:
        if self.current_save_context is None:
            self._active_editor = None
            if self.editor_tabs.tabText(index) == "Garages":
                self._update_garage_controls()
            elif self.editor_tabs.tabText(index) == "Cargo Market":
                self._update_cargo_controls()
            return
        tab_name = self.editor_tabs.tabText(index)
        if tab_name == "Player":
            session: EditableFeatureSession | None = self._player_session
        elif tab_name == "Company":
            session = self._company_session
        elif tab_name == "Garages":
            session = self._garage_session
        elif tab_name == "Cargo Market":
            session = self._cargo_session
        else:
            self._active_editor = None
            return
        if session is None:
            self._active_editor = None
            return
        self._active_editor = SessionEditorAdapter(
            session,
            self.current_save_context.editor,
            self.current_save_context.save.game_sii,
        )
        if tab_name == "Garages":
            self._update_garage_controls()
        elif tab_name == "Cargo Market":
            self._update_cargo_controls()

    @staticmethod
    def _readonly_page() -> QWidget:
        page, layout, view = QWidget(), QVBoxLayout(), QTextEdit()
        page.setLayout(layout)
        view.setReadOnly(True)
        view.setPlainText("Select a parsed save.")
        layout.addWidget(QLabel("Read-only while WRITE BLOCKED."))
        layout.addWidget(view)
        return page

    def _cargo_market_page(self) -> QWidget:
        page, layout = QWidget(), QHBoxLayout()
        page.setLayout(layout)
        self.cargo_list = QListWidget()
        self.cargo_list.setObjectName("cargoMarketList")
        detail, form = QWidget(), QFormLayout()
        detail.setLayout(form)
        self.cargo_identifier = QLineEdit()
        self.cargo_identifier.setObjectName("cargoMarketIdentifier")
        self.cargo_identifier.setReadOnly(True)
        self.cargo_city = QLineEdit()
        self.cargo_city.setObjectName("cargoMarketCity")
        self.cargo_city.setReadOnly(True)
        self.cargo_seeds = QLineEdit()
        self.cargo_seeds.setObjectName("cargoMarketSeeds")
        self.cargo_seeds.setReadOnly(True)
        self.cargo_randomize_button = QPushButton("Randomize offers")
        self.cargo_reset_button = QPushButton("Reset offers")
        self.cargo_save_button = QPushButton("Save Changes")
        self.cargo_discard_button = QPushButton("Discard")
        for widget, name in (
            (self.cargo_randomize_button, "cargoMarketRandomizeButton"),
            (self.cargo_reset_button, "cargoMarketResetButton"),
            (self.cargo_save_button, "cargoMarketSaveButton"),
            (self.cargo_discard_button, "cargoMarketDiscardButton"),
        ):
            widget.setObjectName(name)
            widget.setEnabled(False)
        form.addRow("Company", self.cargo_identifier)
        form.addRow("City", self.cargo_city)
        form.addRow("Offer seeds", self.cargo_seeds)
        form.addRow(self.cargo_randomize_button)
        form.addRow(self.cargo_reset_button)
        form.addRow(self.cargo_save_button)
        form.addRow(self.cargo_discard_button)
        layout.addWidget(self.cargo_list)
        layout.addWidget(detail)
        self.cargo_list.currentItemChanged.connect(self._on_cargo_selected)
        self.cargo_randomize_button.clicked.connect(self._cargo_randomize)
        self.cargo_reset_button.clicked.connect(self._cargo_reset)
        self.cargo_save_button.clicked.connect(self._save_cargo)
        self.cargo_discard_button.clicked.connect(self._discard_cargo)
        return page

    def _on_cargo_selected(
        self, item: QListWidgetItem | None, _previous: QListWidgetItem | None = None
    ) -> None:
        identifier = item.data(Qt.ItemDataRole.UserRole) if item is not None else None
        self._cargo_session.select(str(identifier) if identifier is not None else None) if self._cargo_session else None
        self._project_cargo_selection()

    def _project_cargo_selection(self) -> None:
        session = self._cargo_session
        entry = session.selected_entry() if session is not None else None
        for widget, value in (
            (self.cargo_identifier, entry.identifier if entry else ""),
            (self.cargo_city, entry.city if entry else ""),
            (self.cargo_seeds, ", ".join(entry.seeds) if entry else ""),
        ):
            blocker = QSignalBlocker(widget)
            widget.setText(value)
            del blocker
        self._update_cargo_controls()

    def _populate_cargo_market(self) -> None:
        session = self._cargo_session
        selected = session.selected_identifier if session is not None else None
        blocker = QSignalBlocker(self.cargo_list)
        self.cargo_list.clear()
        if session is not None:
            for entry in session.entries:
                item = QListWidgetItem(f"{entry.company_type} / {entry.city}")
                item.setData(Qt.ItemDataRole.UserRole, entry.identifier)
                self.cargo_list.addItem(item)
                if entry.identifier == selected:
                    self.cargo_list.setCurrentItem(item)
        del blocker
        self._project_cargo_selection()

    def _cargo_operation(self, operation: str) -> None:
        session = self._cargo_session
        if session is None or not session.write_allowed:
            return
        session.set_pending_operation(operation)
        self._update_cargo_controls()

    def _cargo_randomize(self) -> None:
        self._cargo_operation("randomize")

    def _cargo_reset(self) -> None:
        self._cargo_operation("reset")

    def _update_cargo_controls(self) -> None:
        session = self._cargo_session
        editable = session is not None and session.write_allowed and session.selected_identifier is not None
        self.cargo_randomize_button.setEnabled(editable)
        self.cargo_reset_button.setEnabled(editable)
        self.cargo_save_button.setEnabled(bool(editable and session and session.dirty))
        self.cargo_discard_button.setEnabled(bool(session and session.dirty))

    def _save_cargo(self) -> None:
        previous = self.current_save_context
        self._save_active_editor()
        if not self.reload_current_save() and previous is not None:
            self._restore_context_snapshot(previous)

    def _discard_cargo(self) -> None:
        previous = self.current_save_context
        self._discard_active_editor()
        if not self.reload_current_save() and previous is not None:
            self._restore_context_snapshot(previous)

    def _player_page(self) -> QWidget:
        page, form = QWidget(), QFormLayout()
        page.setLayout(form)
        self.player_xp_spin, self.player_adr_spin = QSpinBox(), QSpinBox()
        self.player_male_check = QCheckBox("Male")
        self.player_save_button, self.player_discard_button = (
            QPushButton("Save Changes"), QPushButton("Discard")
        )
        self.player_xp_spin.setObjectName("playerXpSpin")
        self.player_adr_spin.setObjectName("playerAdrSpin")
        self.player_male_check.setObjectName("playerMaleCheck")
        self.player_save_button.setObjectName("playerSaveButton")
        self.player_discard_button.setObjectName("playerDiscardButton")
        self.player_xp_spin.setRange(0, 2_147_483_647)
        self.player_adr_spin.setRange(0, 6)
        for widget in (self.player_xp_spin, self.player_adr_spin, self.player_male_check):
            widget.setEnabled(False)
        self.player_save_button.setEnabled(False)
        self.player_discard_button.setEnabled(False)
        form.addRow("XP", self.player_xp_spin)
        form.addRow("ADR", self.player_adr_spin)
        form.addRow("Gender", self.player_male_check)
        form.addRow(self.player_save_button)
        form.addRow(self.player_discard_button)
        self.player_xp_spin.valueChanged.connect(self._player_changed)
        self.player_adr_spin.valueChanged.connect(self._player_changed)
        self.player_male_check.toggled.connect(self._player_changed)
        self.player_save_button.clicked.connect(self._save_player)
        self.player_discard_button.clicked.connect(self._discard_player)
        return page

    def _player_changed(self, _value: object) -> None:
        if self._player_session is None:
            return
        self._player_session.experience = str(self.player_xp_spin.value())
        self._player_session.adr = str(self.player_adr_spin.value())
        self._player_session.male = self.player_male_check.isChecked()
        self.player_save_button.setEnabled(
            self._player_session.write_allowed and self._player_session.dirty
        )
        self.player_discard_button.setEnabled(self._player_session.dirty)

    def _load_player_widgets(self) -> None:
        session = self._player_session
        enabled = session is not None and session.write_allowed
        for widget in (self.player_xp_spin, self.player_adr_spin, self.player_male_check):
            widget.setEnabled(enabled)
        self.player_save_button.setEnabled(False)
        self.player_discard_button.setEnabled(False)
        if session is None:
            return
        for widget in (self.player_xp_spin, self.player_adr_spin, self.player_male_check):
            blocker = QSignalBlocker(widget)
            if widget is self.player_xp_spin:
                widget.setValue(int(session.experience))
            elif widget is self.player_adr_spin:
                widget.setValue(int(session.adr))
            else:
                self.player_male_check.setChecked(session.male)
            del blocker

    def _save_player(self) -> None:
        previous = self.current_save_context
        self._save_active_editor()
        if not self.reload_current_save() and previous is not None:
            self._restore_context_snapshot(previous)

    def _discard_player(self) -> None:
        previous = self.current_save_context
        self._discard_active_editor()
        if not self.reload_current_save() and previous is not None:
            self._restore_context_snapshot(previous)

    def _company_page(self) -> QWidget:
        page, form = QWidget(), QFormLayout()
        page.setLayout(form)
        self.company_name_edit, self.company_money_edit, self.company_hq_city_edit = (
            QLineEdit(),
            QLineEdit(),
            QLineEdit(),
        )
        self.company_save_button, self.company_discard_button = (
            QPushButton("Save Changes"),
            QPushButton("Discard"),
        )
        self.company_readonly_view = QTextEdit()
        self.company_name_edit.setObjectName("companyNameEdit")
        self.company_money_edit.setObjectName("companyMoneyEdit")
        self.company_hq_city_edit.setObjectName("companyHqCityEdit")
        self.company_save_button.setObjectName("companySaveButton")
        self.company_discard_button.setObjectName("companyDiscardButton")
        self.company_readonly_view.setObjectName("companyReadonlyView")
        self.company_readonly_view.setReadOnly(True)
        self.company_readonly_view.setPlainText("Select a parsed save.")
        for widget in (
            self.company_name_edit,
            self.company_money_edit,
            self.company_hq_city_edit,
            self.company_save_button,
            self.company_discard_button,
        ):
            widget.setEnabled(False)
        form.addRow("Company Name", self.company_name_edit)
        form.addRow("Money", self.company_money_edit)
        form.addRow("HQ City", self.company_hq_city_edit)
        form.addRow(self.company_save_button)
        form.addRow(self.company_discard_button)
        form.addRow("Visited cities, dealers, recruitments, drivers", self.company_readonly_view)
        self.company_name_edit.textChanged.connect(self._company_changed)
        self.company_money_edit.textChanged.connect(self._company_changed)
        self.company_hq_city_edit.textChanged.connect(self._company_changed)
        self.company_save_button.clicked.connect(self._save_company)
        self.company_discard_button.clicked.connect(self._discard_company)
        return page

    def _company_changed(self, _value: str) -> None:
        if self._company_session is None:
            return
        self._company_session.name = self.company_name_edit.text()
        self._company_session.money = self.company_money_edit.text()
        self._company_session.hq_city = self.company_hq_city_edit.text()
        self.company_save_button.setEnabled(
            self._company_session.write_allowed and self._company_session.dirty
        )
        self.company_discard_button.setEnabled(self._company_session.dirty)

    def _load_company_widgets(self) -> None:
        session = self._company_session
        enabled = session is not None and session.write_allowed
        for widget in (
            self.company_name_edit,
            self.company_money_edit,
            self.company_hq_city_edit,
        ):
            widget.setEnabled(enabled)
        self.company_save_button.setEnabled(False)
        self.company_discard_button.setEnabled(False)
        if session is None:
            for widget in (
                self.company_name_edit,
                self.company_money_edit,
                self.company_hq_city_edit,
            ):
                blocker = QSignalBlocker(widget)
                widget.clear()
                del blocker
            return
        for widget, value in (
            (self.company_name_edit, session.name),
            (self.company_money_edit, session.money),
            (self.company_hq_city_edit, session.hq_city),
        ):
            blocker = QSignalBlocker(widget)
            widget.setText(value)
            del blocker

    def _save_company(self) -> None:
        previous = self.current_save_context
        self._save_active_editor()
        if not self.reload_current_save() and previous is not None:
            self._restore_context_snapshot(previous)

    def _discard_company(self) -> None:
        previous = self.current_save_context
        self._discard_active_editor()
        if not self.reload_current_save() and previous is not None:
            self._restore_context_snapshot(previous)

    def _garage_page(self) -> QWidget:
        page, layout = QWidget(), QHBoxLayout()
        page.setLayout(layout)
        self.garage_list = QListWidget()
        self.garage_list.setObjectName("garageList")
        detail, form = QWidget(), QFormLayout()
        detail.setLayout(form)
        self.garage_identifier, self.garage_status = QLineEdit(), QSpinBox()
        self.garage_identifier.setObjectName("garageIdentifier")
        self.garage_status.setObjectName("garageStatus")
        self.garage_identifier.setReadOnly(True)
        self.garage_status.setRange(0, 2_147_483_647)
        self.garage_save_button, self.garage_discard_button, self.garage_sell_button = (
            QPushButton("Save Changes"), QPushButton("Discard"), QPushButton("Sell Garage")
        )
        self.garage_save_button.setObjectName("garageSaveButton")
        self.garage_discard_button.setObjectName("garageDiscardButton")
        self.garage_sell_button.setObjectName("garageSellButton")
        self.garage_save_button.setEnabled(False)
        self.garage_discard_button.setEnabled(False)
        self.garage_sell_button.setEnabled(False)
        form.addRow("Identifier", self.garage_identifier)
        form.addRow("Status", self.garage_status)
        form.addRow(self.garage_save_button)
        form.addRow(self.garage_discard_button)
        form.addRow(self.garage_sell_button)
        layout.addWidget(self.garage_list)
        layout.addWidget(detail)
        self.garage_list.currentItemChanged.connect(self._on_garage_selected)
        self.garage_status.valueChanged.connect(self._garage_status_changed)
        self.garage_save_button.clicked.connect(self._save_garage)
        self.garage_discard_button.clicked.connect(self._discard_garage)
        self.garage_sell_button.clicked.connect(self._sell_garage)
        return page

    def _on_garage_selected(self, item: QListWidgetItem | None) -> None:
        identifier = item.data(Qt.ItemDataRole.UserRole) if item is not None else None
        self._selected_garage_id = str(identifier) if identifier is not None else None
        if self._garage_session is not None:
            self._garage_session.select(self._selected_garage_id)
        self.garage_identifier.setText(str(identifier or ""))
        blocker = QSignalBlocker(self.garage_status)
        self.garage_status.setValue(
            self._garage_session.status(self._selected_garage_id)
            if self._garage_session is not None and self._selected_garage_id is not None
            else 0
        )
        del blocker
        self._update_garage_controls()

    def _garage_status_changed(self, status: int) -> None:
        if self._garage_session is None or self._selected_garage_id is None:
            return
        self._garage_session.set_pending_status(self._selected_garage_id, status)
        self._update_garage_controls()

    def _update_garage_controls(self) -> None:
        session = self._garage_session
        editable = (
            session is not None
            and session.write_allowed
            and self._selected_garage_id is not None
        )
        self.garage_status.setEnabled(editable)
        self.garage_save_button.setEnabled(editable and session.dirty if session else False)
        self.garage_discard_button.setEnabled(session.dirty if session else False)
        self.garage_sell_button.setEnabled(
            editable and session.hq_identifier is not None if session else False
        )

    def _save_garage(self) -> None:
        previous = self.current_save_context
        self._save_active_editor()
        if not self.reload_current_save() and previous is not None:
            self._restore_context_snapshot(previous)

    def _discard_garage(self) -> None:
        previous = self.current_save_context
        self._discard_active_editor()
        if not self.reload_current_save() and previous is not None:
            self._restore_context_snapshot(previous)

    def _sell_garage(self) -> None:
        session = self._garage_session
        identifier = self._selected_garage_id
        context = self.current_save_context
        if (
            session is None
            or identifier is None
            or context is None
            or not session.write_allowed
            or session.hq_identifier is None
        ):
            return
        if session.dirty:
            decision = PendingChangesPrompt().decide(self, session)
            if decision is PendingChangeDecision.CANCEL or decision is None:
                return
            if decision is PendingChangeDecision.DISCARD:
                session.discard()
                self._populate_garages()
            else:
                self._save_garage()
        if not GarageSaleConfirmation().confirm(self, identifier):
            return
        session.sell(
            context.editor,
            context.save.game_sii,
            identifier,
            session.hq_identifier,
        )
        if not self.reload_current_save():
            self._restore_context_snapshot(context)

    @staticmethod
    def _set_page_text(page: QWidget, text: str) -> None:
        view = page.findChild(QTextEdit)
        if view is not None:
            view.setPlainText(text)

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

    def _has_pending_changes(self) -> bool:
        return self._active_editor is not None and self._active_editor.is_dirty

    def _save_active_editor(self) -> object | None:
        return None if self._active_editor is None else self._active_editor.save()

    def _discard_active_editor(self) -> None:
        if self._active_editor is not None:
            self._active_editor.discard()

    def _on_game_combo_changed(self, _index: int) -> None:
        target = self.selected_game
        if self._coordinating_context_switch or target == self._committed_game:
            return
        self._coordinate_context_switch(self.refresh_profiles, self._restore_game_selection)

    def _on_profile_combo_changed(self, _index: int) -> None:
        target = self.selected_profile
        if self._coordinating_context_switch or target == self._committed_profile:
            return
        self._coordinate_context_switch(self._on_profile_selected, self._restore_profile_selection)

    def _on_save_combo_changed(self, _index: int) -> None:
        target = self.selected_save
        if self._coordinating_context_switch or target == self._committed_save:
            return
        self._coordinate_context_switch(self._on_save_selected, self._restore_save_selection)

    def _coordinate_context_switch(
        self, perform_switch: Callable[[], None], restore_selection: Callable[[], None]
    ) -> bool:
        """Resolve one pending editor decision before any selector changes context."""
        if self._has_pending_changes():
            editor = self._active_editor
            if editor is None:
                return False
            decision = PendingChangesPrompt().decide(self, editor)
            if decision is PendingChangeDecision.CANCEL or decision is None:
                restore_selection()
                return False
            if decision is PendingChangeDecision.SAVE:
                try:
                    self._save_active_editor()
                except (OSError, RuntimeError, ValueError) as error:
                    self._status(f"Save failed: {error}")
                    restore_selection()
                    return False
            else:
                self._discard_active_editor()
        self._coordinating_context_switch = True
        try:
            perform_switch()
        finally:
            self._coordinating_context_switch = False
        return True

    @staticmethod
    def _restore_combo_data(combo: QComboBox, previous: object | None) -> None:
        if previous is None:
            return
        def identity(value: object) -> object:
            if isinstance(value, Profile):
                return value.directory
            if isinstance(value, SaveSlot):
                return value.directory
            return value

        target = identity(previous)
        index = next(
            (item for item in range(combo.count()) if identity(combo.itemData(item)) == target),
            -1,
        )
        if index == -1:
            return
        blocker = QSignalBlocker(combo)
        combo.setCurrentIndex(index)
        del blocker

    def _restore_game_selection(self) -> None:
        self._restore_combo_data(self.game, self._committed_game)

    def _restore_profile_selection(self) -> None:
        self._restore_combo_data(self.profile, self._committed_profile)

    def _restore_save_selection(self) -> None:
        self._restore_combo_data(self.save, self._committed_save)

    def _commit_current_context_selection(self) -> None:
        context = self.current_save_context
        if context is None:
            return
        self._committed_game = context.game
        self._committed_profile = context.profile
        self._committed_save = context.save

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
            self.current_save_context = None
            self._player_session = None
            self._company_session = None
            self._garage_session = None
            self._cargo_session = None
            self._selected_garage_id = None
            self._load_player_widgets()
            self._load_company_widgets()
            self._populate_garages()
            self._populate_cargo_market()
            self.save_details.setText("No save selected.")
            self.compatibility_details.setText("UNKNOWN — WRITE BLOCKED")
            self._clear_editor_views()
            self._update_actions()
            return
        try:
            diagnostic = self.inspect_selected_save()
        except (OSError, RuntimeError) as error:
            self.current_save_context = None
            self._player_session = None
            self._company_session = None
            self._garage_session = None
            self._cargo_session = None
            self._selected_garage_id = None
            self._load_player_widgets()
            self._load_company_widgets()
            self._populate_garages()
            self._populate_cargo_market()
            self.save_details.setText(f"Save diagnostic failed: {error}")
            self.compatibility_details.setText("UNKNOWN — WRITE BLOCKED")
            self._status(f"Save diagnostic failed: {error}")
            self._clear_editor_views("Save diagnostic failed.")
        else:
            self._show_diagnostic(save, diagnostic)
            if diagnostic.parse_ok:
                self._load_current_context(save)
                self._load_editor_views(save)
            else:
                self._clear_editor_views("Save could not be parsed.")
            self.refresh_backups()
        self._update_actions()

    def inspect_selected_save(self, version: GameVersion | None = None) -> SaveDiagnostic:
        save = self._require_save()
        return self._diagnostics.inspect(self.selected_game, save.game_sii, version)

    def _build_save_reload_candidate(
        self,
        save: SaveSlot,
        version: GameVersion | None = None,
        editor: EditorService | None = None,
    ) -> _SaveReloadCandidate:
        game = self.selected_game
        profile = self._require_profile()
        assessment = CompatibilityRegistry().assess(game, version)
        candidate_editor = editor or EditorService(self._save_editor)
        state = candidate_editor.load(save.game_sii, assessment)
        context = CurrentSaveContext(game, profile, save, assessment, candidate_editor, state)
        try:
            player = PlayerEditorSession(state)
        except StopIteration:
            player = None
        try:
            company = CompanyEditorSession(state)
        except StopIteration:
            company = None
        garage = GarageEditorSession(state)
        cargo = CargoMarketEditorSession(state)
        return _SaveReloadCandidate(context, player, company, garage, cargo)

    def _commit_save_reload_candidate(self, candidate: _SaveReloadCandidate) -> None:
        selected_garage = self._selected_garage_id
        selected_cargo = (
            self._cargo_session.selected_identifier
            if self._cargo_session is not None
            else None
        )
        active_tab = self.editor_tabs.tabText(self.editor_tabs.currentIndex())
        previous_active = self._active_editor
        self.current_save_context = candidate.context
        self._player_session = candidate.player
        self._company_session = candidate.company
        self._garage_session = candidate.garage
        self._cargo_session = candidate.cargo
        self._selected_garage_id = (
            selected_garage if selected_garage in candidate.garage.garages else None
        )
        candidate.garage.select(self._selected_garage_id)
        if selected_cargo in {entry.identifier for entry in candidate.cargo.entries}:
            candidate.cargo.select(selected_cargo)
        self._load_player_widgets()
        self._load_company_widgets()
        self._populate_garages()
        self._populate_cargo_market()
        self._commit_current_context_selection()
        replacement = {
            "Player": candidate.player,
            "Company": candidate.company,
            "Garages": candidate.garage,
            "Cargo Market": candidate.cargo,
        }.get(active_tab)
        if isinstance(previous_active, SessionEditorAdapter) and replacement is not None:
            previous_active.rebind(
                replacement, candidate.context.editor, candidate.context.save.game_sii
            )
            self._active_editor = previous_active
        else:
            self._on_editor_tab_changed(self.editor_tabs.currentIndex())

    def _restore_context_snapshot(self, context: CurrentSaveContext) -> None:
        """Restore a coherent in-memory projection when disk reload fails."""
        try:
            player = PlayerEditorSession(context.state)
        except StopIteration:
            player = None
        try:
            company = CompanyEditorSession(context.state)
        except StopIteration:
            company = None
        candidate = _SaveReloadCandidate(
            context,
            player,
            company,
            GarageEditorSession(context.state),
            CargoMarketEditorSession(context.state),
        )
        self._commit_save_reload_candidate(candidate)

    def _load_current_context(self, save: SaveSlot, version: GameVersion | None = None) -> None:
        candidate = self._build_save_reload_candidate(save, version, self._editor_service)
        self._commit_save_reload_candidate(candidate)

    def reload_current_save(self) -> bool:
        """Atomically rebuild the current save context and all feature sessions."""
        context = self.current_save_context
        if context is None:
            return False
        try:
            candidate = self._build_save_reload_candidate(
                context.save, context.assessment.version
            )
        except (OSError, RuntimeError, StopIteration, ValueError) as error:
            self._status(f"Reload failed: {error}")
            return False
        self._commit_save_reload_candidate(candidate)
        return True

    def _clear_editor_views(self, message: str = "Select a parsed save.") -> None:
        for page in (self.player_view, self.company_view, self.garages_view, self.freight_market_view):
            self._set_page_text(page, message)

    def _load_editor_views(self, save: SaveSlot) -> None:
        """Project existing, parsed units without introducing GUI domain logic."""
        try:
            text = self._decoder.decode_file(save.game_sii).data.decode("utf-8")
            document = parse_sii(text)
        except Exception as error:
            self._clear_editor_views(f"Read-only load failed: {error}")
            return

        def display(types: set[str]) -> str:
            blocks = [block for block in document.blocks if block.type_name in types]
            if not blocks:
                return "N/A: structure is absent from this save."
            return "\n\n".join(
                f"{block.type_name} : {block.identifier}\n" + "\n".join(
                    f"{field.key}: {field.value}" for field in block.fields
                ) for block in blocks
            )

        self._set_page_text(
            self.company_view,
            display({"visited_city", "unlocked_dealer", "unlocked_recruitment", "driver"}),
        )
        self._populate_garages(document)
        self._set_page_text(self.freight_market_view, display({"company", "job_offer_data"}))

    def _populate_garages(self, document: SiiDocument | None = None) -> None:
        selected = self._selected_garage_id
        self.garage_list.clear()
        self._garage_statuses = {}
        self._on_garage_selected(None)
        blocks = (
            document.blocks
            if document is not None
            else (
                self.current_save_context.state.document.blocks
                if self.current_save_context is not None
                else ()
            )
        )
        for block in blocks:
            if block.type_name != "garage":
                continue
            status = next((field.value for field in block.fields if field.key == "status"), "")
            self._garage_statuses[block.identifier] = status
            item = QListWidgetItem(block.identifier)
            item.setData(Qt.ItemDataRole.UserRole, block.identifier)
            self.garage_list.addItem(item)
            if block.identifier == selected:
                self.garage_list.setCurrentItem(item)

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
