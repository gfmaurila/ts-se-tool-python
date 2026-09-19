# Task 11H.7 - Main / Player / Company / Garage / Market GUI

Timestamp: 2026-09-19T01:34:58-03:00

## Status: PARCIAL

## Recovery update (2026-09-19T01:34:58-03:00)

The aggregate classification is restored to the authoritative post-11H.6
baseline: **19 IMPLEMENTADO, 20 PARCIAL, 4 NÃO IMPLEMENTADO, 1 N/A**. The
`19/16/8/1` figure was a superseded 11F snapshot and was not a functional
downgrade. Matrix and parity-audit notes now make this explicit.

Configured roots are profile/save data roots under Documents, not game installation
roots. They expose no executable or official installation manifest. The previous fixture
investigation also found no reliable version source. `GameVersionResolver` was therefore
not implemented; deriving a version from successful decode/parse would violate 11H.5.
UNKNOWN remains WRITE BLOCKED.

`MainWindow` now has Player, Company, Garages, Cargo Market, Freight Market, Settings,
Backups, and Diagnostics tabs. Following successful diagnostics, the new tabs project
only existing parsed SII blocks read-only; absent structures are marked N/A. They do not
mutate an AST or write a save.

Ruff and mypy for `desktop/main.py`: PASS. A fresh workspace-local basetemp still
failed inside the sandbox during pytest cleanup, but the exact same focused command
outside the sandbox passed: **7 passed, 0 failed, 0 skipped**. Full regression was
not run.

Remaining work: service-backed mutations, dirty confirmations, reload/error flows,
offscreen tests, and final gates. Do not start 11H.8.

## Phase 1 implementation increment (2026-09-19T01:46:42-03:00)

Added GUI-neutral `EditorService`/`EditorSaveState`. It reloads a save through the
decoder/parser and delegates a supplied existing domain mutation to `SaveEditService`
with an explicit `CompatibilityAssessment`; it never writes itself. A VALIDATED ATS
1.61 temporary save test proves mutation, unique backup, and reload. UNKNOWN is proven
blocked before backup. Focused tests: 2 passed. Ruff and mypy pass for the new service.

The desktop widgets are not yet bound to this service, so no Player/Company/Garage/
Cargo/Freight write capability is claimed yet. This is a safe completed sub-unit; the
next sub-unit is Player widget binding and its focused tests.

## Phase 1B Player session increment

`PlayerEditorSession` now provides reusable pending XP/ADR/Gender state over
`EditorSaveState`: edits are dirty, discard restores persisted state without writing,
and save delegates the existing player backend (`set_experience`, `set_skill`,
`set_gender`) through `EditorService` and reloads from disk. Four focused temporary-save
tests pass, including unique backup and UNKNOWN blocking. Desktop control binding and
navigation Save/Discard/Cancel prompts remain pending, so Phase 1B is partial.

## Phase 1B.1 Player flow closure increment

Added `PendingChangeDecision` and `resolve_pending_change`, a reusable pure navigation
guard: Cancel retains dirty state, Discard performs no write, and Save only proceeds
through the session's compatibility policy. Explicit UNVALIDATED and UNSUPPORTED tests
prove no backup is created; error-injection tests prove dirty values survive save errors.
Nine focused tests pass. The visual QMessageBox binding remains pending.

## Phase 1C Company increment

Added `CompanyEditorSession` using only existing mutations for company name, bank money
and player HQ. It follows the same safe apply/reload/discard pattern. Cities, dealers,
recruitments and drivers remain readable projections only. Focused service tests: 10
passed; visual widget/prompt binding remains pending.

## Phase 1C.1 shared pending-changes dialog

Added `desktop.pending_changes.PendingChangesPrompt`, a shared PySide6 visual adapter
that consumes an editor's existing `dirty` and `write_allowed` properties and returns
the existing `PendingChangeDecision`. Clean editors show no dialog; VALIDATED offers
Save/Discard/Cancel; blocked states offer only Discard/Cancel. Eleven focused tests
cover Player/Company session regressions and dialog option policy. The dialog is not
yet wired into MainWindow selection signals, so navigation-level completion is pending.

## Phase 1D Garage increment

Added `GarageEditorSession`, a GUI-neutral adapter over existing `set_garage_status`
and `sell_garage` backends. It lists only actual garage identifiers and persists through
`EditorService`, reloading after success. No Garage widget, city inference, sale
confirmation, or focused garage-session test has been added yet; this increment is
partial and must not be treated as end-to-end GUI completion.

## Phase 1D.2 confirmation increment

Added separate `GarageSaleConfirmation`; it is independent of pending changes and
identifies only the stable garage identifier, never an inferred city. Focused Garage,
editor-session and dialog regression suite: 27 passed. MainWindow Garage widget binding,
sale orchestration and dirty-sale sequencing remain pending.

## Phase 1D.3 trace / safe stop

Tracing `MainWindow` found no existing Garage list, selection state, status control or
Sell button: the Garage tab is still a read-only `QTextEdit` projection. Therefore this
is not a missing signal connection; it needs a coherent widget implementation plus
offscreen integration tests. No partial MainWindow binding was added in this unit.

## Phase 1D.6 MainWindow editor-session foundation

Added immutable `CurrentSaveContext` containing selected game/profile/save,
CompatibilityAssessment, EditorService and parsed EditorSaveState. MainWindow creates it
only after successful load and clears it on no-save/load failure. Focused desktop tests:
7 passed. Switch navigation and Garage session binding remain pending.

## Phase 1D.4 real Garage GUI increment

The Garage QTextEdit projection has been replaced with a QListWidget carrying stable
identifiers in UserRole, read-only identifier/status detail controls, and disabled Save/
Sell controls. Reloaded parsed garage blocks repopulate the list and selection updates
details. Status persistence, dirty state and sale orchestration are not connected yet.

## Phase 1D.1 Garage flow increment

Focused temporary-save coverage now proves stable garage identifiers, validated status
write/reload, and UNKNOWN blocking before a backup. The editor-service focused suite is
12 passed. Sale confirmation, sale integration and widget list/selection/details remain
unimplemented, so this phase remains partial.

## Phase 1D.6.2D.1 Company UI + session foundation

Replaced the Company QTextEdit-only primary surface with persistent MainWindow-bound
CompanyEditorSession widgets for company name, money and HQ city. Widget projection
uses QSignalBlocker and widget edits update the existing session; the active-editor
adapter binds that same session when the Company tab is selected. UNKNOWN, UNVALIDATED
and UNSUPPORTED contexts disable mutation controls, while the existing read-only
Company groups remain displayed separately. Save/Discard behavior is deliberately not
connected in this microphase. Offscreen Company tests: 11 passed; Player desktop: 9
passed; active-editor: 1 passed; MainWindow foundation: 7 passed; Ruff/mypy PASS.

## Phase 1D.6.2D.2 Company Save/Discard closure

Company Save and Discard now reuse the existing active-editor delegation: the persistent
CompanyEditorSession calls EditorService and SaveEditService, while the MainWindow only
reprojects widgets after a successful save or after discard. A write-boundary failure
propagates before reprojection, preserving the same Company session, active adapter,
CurrentSaveContext, dirty state and pending widget value. Offscreen Company suite: 14
passed; Company domain: 13 passed; focused Company EditorService: 1 passed; Player
desktop: 9 passed; active-editor: 1 passed; MainWindow foundation: 7 passed; Ruff/mypy
PASS. Player and Company desktop editor closures are complete; Garage remains pending.

## Phase 1D.6.2E Garage active-editor/binding

Garage now has a persistent pending-status session derived from CurrentSaveContext,
while retaining its existing immediate status/sale methods for backend compatibility.
The real list retains stable identifiers, selection projects status with signal
blocking, and the same session powers dirty state, SessionEditorAdapter, safe Save,
failure preservation and Discard. The existing sale backend is bound through its
separate stable-identifier confirmation; a dirty-sale Cancel is proven to leave the
pending status untouched. Desktop Garage: 13 passed; existing Garage backend/dialog
suite: 27 passed; Player desktop: 9 passed; Company desktop: 14 passed; active-editor:
1 passed; MainWindow foundation: 7 passed; Ruff/mypy PASS.

## Phase 1D.6.3A context switch coordinator

MainWindow now coordinates Game, Profile and Save combo changes through one
dirty-aware guard. It uses the existing active editor and PendingChangesPrompt, then
performs Save/Discard only when authorized. Stable Game, Profile-directory and
Save-directory identities restore visual combos through QSignalBlocker after Cancel or
save failure, so a denied target never leaves UI/context mismatched. The offscreen
matrix covers all clean, Save success, Save failure, Discard and Cancel outcomes for
all three selectors, reentrancy, and a Company active-editor case: 17 passed. Player
desktop 9, Company desktop 14, Garage desktop 13, Garage backend 27, active-editor 1,
and MainWindow foundation 7 all pass; Ruff/mypy PASS. Atomic reload is intentionally
not part of this phase.

## Phase 1D.6.3B atomic reload

Implemented one shared `reload_current_save()` pipeline using build-candidate-first
and atomic commit semantics. The candidate rebuilds the parsed document,
CurrentSaveContext, EditorService, CompatibilityAssessment, Player/Company/Garage
sessions and rebinds the existing ActiveEditor adapter to the new session. Garage
selection is restored by stable identity and widgets are reprojected with signal
blocking. Candidate parse, service and validation failures leave the previously
coherent in-memory state installed. A write-success/reload-failure test documents
that the disk write remains successful while the UI preserves its last coherent
state.

Atomic reload: 11 passed, 0 failed. Combined desktop context/editor suite: 64
passed, 0 failed. Garage/backend, EditorService, active-editor and MainWindow smoke
regressions: 35 passed, 0 failed. Ruff and mypy PASS. No production or QA saves or
profiles were modified.
