# Task 06 — Player Editor

Status: complete on 2026-09-17.

- Added conservative in-memory edits for proven `economy.experience_points`,
  `bank.money_account`, and the legacy skills `adr`, `long_distance`, `heavy`,
  `fragile`, `urgent`, and `mechanical` (0–6).
- Each edit reparses the result and retains non-target fields verbatim. No
  filesystem write path or fixture mutation was introduced.
- Internal level-to-XP conversion remains deferred: the legacy defines
  game-specific level tables, and no 1.61 evidence is yet available to claim
  those tables remain compatible.

Validation (Python 3.13.15):

- Ruff: PASS
- mypy: PASS
- pytest with coverage: 22 passed, 91.78% (threshold 80%): PASS
- `git diff --check`: PASS
