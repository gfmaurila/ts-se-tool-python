# Task 04 — Save Parser

Status: complete on 2026-09-17.

- Added a conservative plaintext SII AST for ordered blocks, identifiers,
  fields, indexed lists, and retained unknown block lines.
- Kept complete original source in `SiiDocument`, making an unedited
  parse/serialize round-trip byte-for-byte stable for the supplied UTF-8
  decrypted ETS fixture.
- Added unit, malformed-input, and golden round-trip tests.

Validation (Python 3.13.15):

- Ruff: PASS
- mypy: PASS
- pytest with coverage: 18 passed, 95.79% (threshold 80%): PASS
- `git diff --check`: PASS
