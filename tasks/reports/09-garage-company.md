# Task 09 — Garage/Company

Status: complete on 2026-09-18.

- Added a `Garage` domain view and targeted in-memory `garage.status` editing,
  supported by legacy code and the plaintext ETS fixture.
- Selected garage updates preserve unknown fields and all other blocks.
- Company and market regeneration is deliberately deferred: the available
  evidence does not establish a safe 1.61-compatible write contract.

Validation (Python 3.13.15):

- Ruff: PASS
- mypy: PASS
- pytest with coverage: 25 passed, 88.19% (threshold 80%): PASS
- `git diff --check`: PASS
