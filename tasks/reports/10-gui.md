# Task 10 — GUI

Status: complete on 2026-09-18.

- Added a PySide6 entry point with ATS/ETS2, profile, and save selection.
- Clone requires explicit UI confirmation and delegates to the safe application
  use case; errors are surfaced in the window.
- Added offscreen widget smoke coverage. Save editors are intentionally not
  exposed until plaintext loading and atomic-write infrastructure are complete.

Validation (Python 3.13.15):

- Ruff: PASS
- mypy: PASS
- pytest with coverage: 26 passed, 84.64% (threshold 80%): PASS
- `git diff --check`: PASS
