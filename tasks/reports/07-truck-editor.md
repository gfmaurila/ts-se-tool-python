# Task 07 — Truck Editor

Status: complete on 2026-09-18.

- Added a `Truck` domain view independent of the SII AST.
- Added targeted in-memory condition editing for proven legacy `vehicle`
  fields: engine, transmission, cabin wear, and fuel ratio.
- Edits are scoped to the selected vehicle identifier and preserve unknown
  fields and other vehicle blocks; no save or fixture is written.
- This is format evidence from the supplied plaintext fixture and legacy
  source, not proof of ATS/ETS2 1.61 compatibility; Tasks 11/12 must validate
  real 1.61 fixtures after decoder support exists.

Validation (Python 3.13.15):

- Ruff: PASS
- mypy: PASS
- pytest with coverage: 23 passed, 90.05% (threshold 80%): PASS
