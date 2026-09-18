# Task 02 — Profile Discovery

Status: complete on 2026-09-17.

- Added immutable `Game`, `GameInstallation`, `Profile`, and `SaveSlot` models.
- Implemented read-only ATS/ETS2 discovery for standard and Steam profiles,
  valid `game.sii` save slots, and explicit custom game-folder configuration.
- Installation paths are diagnostic configuration only; no registry or Steam
  library scanning is inferred.

Validation (Python 3.13.15):

- Ruff: PASS
- mypy: PASS
- pytest with coverage: 8 passed, 96.88% (threshold 80%): PASS
