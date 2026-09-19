# 11H.6 — Profile / Discovery / Settings / Backup GUI

Status: **CONCLUÍDA**.

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

Seven offscreen GUI tests pass against temporary fixtures: game-root switch,
profile/save diagnostics and unknown write block, Unicode `Café` identity preview,
named clone, settings ZIP export/import, TSSE backup discovery, and restore.
No production save, profile, QA profile, game, Steam process, or fixture source
was modified.

Ruff and mypy pass. The complete suite collected and passed **172 tests** with
0 failures and 0 skips. Final measured coverage is **83.59%** (the terminal
coverage summary rounds the overall report to 84%), above the mandatory 80%
gate. Added coverage exercises root-settings/dialog construction, confirmation
and error paths, busy-state reentry, validated/unknown diagnostics, and disabled
restore actions; the coverage gate was not changed.

## Limitations

No Player, Company, Garage, Market, Truck, Trailer, Driver, or Convoy editor UI
was added. Automatic game-version detection remains unavailable by design; version
must be supplied by a future caller to obtain a validated state.
