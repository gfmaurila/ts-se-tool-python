# Task 11G.2 - Controlled plaintext SiiN write validation

Timestamp: 2026-09-18T20:05:56-03:00

## QA profile discovery

| Game | Authorized QA profile | Location | Status |
| --- | --- | --- | --- |
| ATS | `TSSE_TEST_ATS` | `D:\Work\American Truck Simulator\profiles\545353455F544553545F415453` | Found |
| ETS2 | `TSSE_TEST_ETS2` | `D:\Work\Euro Truck Simulator 2\profiles\545353455F544553545F45545332` | Found; untouched |

ATS save slots found: `autosave`, `autosave_job`. The only non-default alternative available was selected: `autosave_job`.

## ATS controlled write - awaiting manual game test

| Item | Result |
| --- | --- |
| Profile | `TSSE_TEST_ATS` |
| Save directory | `...\save\autosave_job` |
| Files selected | `game.sii`, `info.sii` (read-only) |
| Original format | `ScsC` (`scs-container`) |
| Decode/parse | `LegacySiiDecryptAdapter -> parser -> AST`: PASS; 16,996 blocks |
| Changed field | `economy.adr` |
| Before -> after | `0 -> 1` |
| Serialization | SiiN plaintext: PASS |
| Staging | SafeSaveWriter sibling staging, fsync, reparse, then removed after replacement |
| Domain validation | `economy.adr == 1` and unchanged block count: PASS |
| Concurrent modification check | PASS |
| Atomic replace | PASS |
| Backup | `D:\Work\American Truck Simulator\profiles\545353455F544553545F415453\save\autosave_job\game.sii.tsse-backup-cdefb4f22fd74f5b8d3a6fe3cac95aa7` |
| Original SHA-256 | `be26263b18ced6e634c639e79df637f8f8cdcdebcfc0a5aa925e65c23483fa61` |
| Backup SHA-256 | `be26263b18ced6e634c639e79df637f8f8cdcdebcfc0a5aa925e65c23483fa61` |
| Modified SHA-256 | `0eb293778fe5e7350faf94de1e910fa15c0e7fdae0fe1ea5391d58d26c940415` |
| Post-write SiiN/reparse | PASS |
| Manual game load/field verification | PASS; post-game `economy.adr == 1` |
| Final decision | PLAINTEXT SiiN WRITE SUPPORTED for ATS 1.61 |

## ETS2

| Item | Result |
| --- | --- |
| Profile | `TSSE_TEST_ETS2` |
| Save directory | `...\\save\\autosave_job` |
| Files selected | `game.sii`, `info.sii` (read-only) |
| Original format | `ScsC` (`scs-container`) |
| Decode/parse | `LegacySiiDecryptAdapter -> parser -> AST`: PASS; 17,460 blocks |
| Changed field | `economy.adr` |
| Before -> after | `0 -> 1` |
| Serialization | SiiN plaintext: PASS |
| Staging | SafeSaveWriter sibling staging, fsync, reparse, then removed after replacement |
| Domain validation | `economy.adr == 1` and unchanged block count: PASS |
| Concurrent modification check | PASS |
| Atomic replace | PASS |
| Backup | `D:\\Work\\Euro Truck Simulator 2\\profiles\\545353455F544553545F45545332\\save\\autosave_job\\game.sii.tsse-backup-144afd8f54b24be587aaa46458ce2a3e` |
| Original SHA-256 | `5b2935d1cc56c66adae0dc719355f2d1d581f571df397ac2c4d865a6d2fe9496` |
| Backup SHA-256 | `5b2935d1cc56c66adae0dc719355f2d1d581f571df397ac2c4d865a6d2fe9496` |
| Modified SHA-256 | `179aa0ca9992ea8959b5a3b21a57e656df1dce3c71c2027fb397aeb0f9f90fa8` |
| Post-write SiiN/reparse | PASS |
| Manual game load/field verification | PASS; post-game `economy.adr == 1` |
| Final decision | PLAINTEXT SiiN WRITE SUPPORTED for ETS2 1.61 |

## Automated pre-write checks

- Targeted SafeSaveWriter/parser/player/profile tests: PASS, 32 passed (`--basetemp=.pytest-tmp-11g2`).
- Ruff: PASS.
- mypy: PASS.

## Stop condition

ATS and ETS2 manual loads were PASS. Post-game read-only verification confirms
that both files remain SiiN plaintext with `economy.adr == 1`.

**ARCHITECTURAL DECISION: PLAINTEXT SiiN WRITE SUPPORTED FOR ATS 1.61 AND
ETS2 1.61.** A BSII/ScsC encoder is not required for this pipeline. Both QA
backups remain preserved; restoration was not authorized. No game executable
or Steam process was launched by Codex. Task 11G.2 is **CONCLUIDA**; do not
start 11G.3 without explicit instruction.
