# 11H.6 — Profile / Discovery / Settings / Backup GUI

Status: **PARCIAL** (coverage gate not yet met).

## Delivered GUI connection

`desktop.main.MainWindow` is now a service-backed PySide6 shell. It has ATS/ETS2
selection; QSettings game roots with browse/save/reset; profile and save refresh;
profile metadata; read-only save diagnostics; profile rename/clone previews;
settings ZIP import/export; TSSE-backup discovery and explicit restore.

The UI holds immutable `Profile`/`SaveSlot` discovery results and delegates all
filesystem mutation to `ProfileIdentityEditor`, `ProfileCloner`,
`ProfileSettingsZip`, and `SaveEditService`. It never copies or replaces a save
itself. Restore retains the chosen backup and uses the existing staged writer.

Save diagnostics call `SaveDiagnosticService` with no supplied version, so they
show `UNKNOWN — WRITE BLOCKED`; the UI does not infer 1.61. Profile operations are
not coupled to the game-save compatibility guard. Status-bar messages, typed-error
presentation, confirmation dialogs, and a cursor-based busy guard are present.

## Tests and safety

Five offscreen GUI tests pass against temporary fixtures: game-root switch,
profile/save diagnostics and unknown write block, Unicode `Café` identity preview,
named clone, settings ZIP export/import, TSSE backup discovery, and restore.
No production save, profile, QA profile, game, Steam process, or fixture source
was modified.

Ruff and mypy pass. A complete suite command was started with the requested
basetemp and collected 170 tests, but the coverage data presently reports **76%**
because the new 377-statement desktop adapter has insufficient branch coverage.
The project gate is 80%, so this task cannot be marked complete. The next work is
to add useful automated coverage for root-settings dialogs, confirmations/error
paths, busy-state reentry, validated/unvalidated compatibility display, and
disabled restore/write actions; do not weaken or change the coverage gate.

## Limitations

No Player, Company, Garage, Market, Truck, Trailer, Driver, or Convoy editor UI
was added. Automatic game-version detection remains unavailable by design; version
must be supplied by a future caller to obtain a validated state.
