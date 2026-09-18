# Task 03 — SII Decoder

Status: complete on 2026-09-17.

- Added core decoder contract, header detection, typed decoding errors, and a
  plaintext decoder that preserves source bytes unchanged.
- Added an infrastructure-only adapter for an independently licensed opaque
  decoder; no legacy DLL, executable, subprocess, or license claim was used.
- Recorded observed `ScsC` and `SiiNunit` fixture headers in `SAVE-FORMAT.md`.
- Corrected `scripts/run-tests.ps1` to stop immediately when Ruff, mypy, or
  pytest fails.

Validation (Python 3.13.15):

- Ruff: PASS
- mypy: PASS
- pytest with coverage: 13 passed, 97.31% (threshold 80%): PASS
- `git diff --check`: PASS
