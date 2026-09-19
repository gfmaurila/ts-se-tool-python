# Task 11G.3 - Production Save Write Pipeline

Timestamp: 2026-09-18T20:23:40-03:00

## Status

**CONCLUIDA.** `SaveEditService` is a GUI-independent application service for
one `game.sii` write. It coordinates decoder -> parser/AST -> caller-owned
mutation -> SiiN serialization -> validation -> backup -> atomic replace.
Domain editors continue to own player, vehicle, trailer, garage, cargo, and
freight rules; the service contains none of those rules.

## Formats and decrypt behavior

- SiiN plaintext bypasses the legacy decoder and parses directly.
- Recognized opaque ScsC, BSII, and 3nK inputs use `SiiDecoder`, which delegates
  to `LegacySiiDecryptAdapter` when decode is required.
- Unknown headers are rejected with `UnsupportedSaveFormatError` before any
  external decoder is run.
- Writes intentionally serialize SiiN plaintext. An ScsC/BSII encoder is not
  required: Task 11G.2 proved ATS 1.61 and ETS2 1.61 game acceptance.

## Persistence guarantees

- Candidate output must be non-empty `SiiNunit`, parse successfully, contain a
  basic non-empty AST, and pass an optional caller validation after staging
  reparse.
- `SafeSaveWriter` writes sibling staging, flushes and fsyncs it, then checks
  the original bytes both before staging and immediately before replacement.
- A unique `game.sii.tsse-backup-<nonce>` is copied before replace. Backup
  bytes and SHA-256 are checked against the original; prior backups are never
  overwritten.
- Replacement uses `os.replace` in the target directory. Before replacement
  failures leave the original intact; a replace failure retains the backup and
  returns an explicit typed error. No silent restore occurs.
- `info.sii`, `profile.sii`, sibling saves, and profile files are outside the
  service target and are not changed.

## Restore and discovery

`restore(game_sii, backup)` is explicit. It accepts only non-empty TSSE backup
siblings belonging to that `game.sii`, stages and validates the backup format,
creates a fresh backup of the current target, and atomically replaces it. The
selected backup is never removed. `discover_backups(game_sii)` returns only
matching TSSE backups, newest first.

## Result object and errors

`ProductionSaveWriteResult` returns `game_sii_path`, `backup_path`, original
format, and original/backup/written SHA-256 values. Typed persistence errors
are `SafeSaveWriteError`, `SaveChangedError`, `SaveValidationError`,
`BackupCreationError`, and `AtomicReplaceError`; service structure errors are
`SaveEditError` and `SaveStructureError`.

## Tests and validation

- Unit coverage: SiiN write, fake ScsC adapter, exact backup hash, unique
  backups, staging cleanup/reparse, atomic replacement, caller validation,
  unknown-field preservation, unrelated files/saves, serialization failure,
  concurrency abort, backup failure, replace failure, malformed input, empty
  output, restore, invalid restore, and backup discovery.
- ATS integration: copied real 1.61 fixture -> decrypt -> ADR mutation ->
  production write -> SiiN reparse: PASS; source fixture unchanged.
- ETS2 integration: same copied-fixture flow: PASS; source fixture unchanged.
- Full gate: 129 passed, 0 failed, 0 skipped; coverage 83.03%; Ruff PASS;
  mypy PASS.

## Known limitations

The service intentionally does not provide GUI integration, an ScsC/BSII
encoder, or automatic backup restoration. Decoder support remains bounded by
the existing adapter and available format fixtures.
