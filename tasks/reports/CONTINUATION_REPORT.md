# Continuation Report

- Last updated: 2026-09-18T01:00:54-03:00
- Last completed task: Task 10 — GUI
- Current task: Task 11A — Decoder parity
- State: Task 11A in progress; ScsC envelope decoder implemented, but both
  copied real 1.61 fixtures reveal BSII v3 and require a lossless BSII/3nK
  decoder before this task can be completed.
- Usage/credit indicator: not informed by the platform; session context is near
  its practical limit. This handoff stops before the substantial BSII port.

## Completed functionality

- Tasks 00–10 are complete and individually validated. Task reports contain
  their scoped decisions and quality-gate results.
- Foundation, read-only discovery, decoder boundary, lossless plaintext parser,
  safe profile cloning, and in-memory player/truck/trailer edits exist.

## Pending work

- Review the parity matrix and then implement Task 11A. ATS/ETS2 1.61
  compatibility is not proven: real saves
  begin with opaque `ScsC` and require a separately licensed decoder.

## Modified files

- New source, tests, docs, and task reports under `src/`, `tests/`, `docs/`,
  and `tasks/reports/` through Task 10.
- Existing edited files: `.gitignore`, `docs/LEGACY-MAPPING.md`,
  `docs/SAVE-FORMAT.md`, `scripts/build.ps1`, and `scripts/run-tests.ps1`.
- Preserve all existing uncommitted work; it includes prior Task 00 changes.

## Latest validation

- Python: 3.13.15 via `py -3.13`; `python` still resolves to the Microsoft
  Store alias, so use `.venv\\Scripts\\python.exe` or the project scripts.
- Task 10: Ruff PASS; mypy PASS; pytest PASS (26 passed, 84.64% coverage);
  `git diff --check` PASS.

## Decisions and risks

- No fixture is modified. Player, truck, and trailer edits are in-memory only.
- Plaintext AST keeps original source for unedited exact round trips.
- The `ScsC` container is detected but cannot be decoded without an external,
  separately licensed implementation. Do not mask this in Tasks 11/12.
- Investigation results are in `docs/SCSC-DECODER-INVESTIGATION.md`; ATS
  report is `tasks/reports/ATS-1.61.md` and Task 11 remains incomplete.
- Audit: 44 capabilities; 4 IMPLEMENTADO, 18 PARCIAL, 21 NÃO IMPLEMENTADO,
  1 NÃO APLICÁVEL. New tasks: 11A through 11G, documented in PROJECT.md.

## Exact resume instruction

Read `AGENTS.md`, `PROJECT.md`, and this report. Confirm with `rtk git status
--short`, then await review or inspect Task 11A and only the needed source and real ATS fixture paths. Keep
one task at a time, run `rtk powershell -NoProfile -ExecutionPolicy Bypass
-File scripts\\run-tests.ps1` plus `rtk git diff --check` before recording Task
11A complete only after copied-fixture decoder tests pass.

## Task 11A partial implementation (2026-09-18)

- Added declared dependency `cryptography>=43`, installed only in `.venv`
  (50.0.1), and an independent `ScsContainerDecoder` implementing ScsC
  AES-256-CBC, PKCS#7 unpadding, and zlib inflate. No DLL, executable, or
  third-party decoder source was incorporated.
- The MIT-licensed `liam-dong/SII-Decrypt-cpp` source was inspected only to
  cross-check the envelope layout/key and BSII behavior. Its license permits
  redistribution, but this project does not distribute that source or binary.
- Added `SaveFormat.BINARY` and two regression cases that copy real ATS and
  ETS 1.61 ScsC `game.sii` fixtures to pytest storage. Both copies decrypt;
  each inner payload is `BSII\\x03\\x00\\x00\\x00`, not `SiiN`. The fixture
  originals are byte-for-byte unchanged.
- Updated `docs/SCSC-DECODER-INVESTIGATION.md` and the matrix ScsC row to
  `PARCIAL`. BSII and 3nK remain unimplemented; do not advance tasks.

### Files modified in this unit

`pyproject.toml`, `src/tsse/core/sii/decoder.py`,
`src/tsse/core/sii/__init__.py`, `tests/unit/test_sii_decoder.py`,
`docs/SCSC-DECODER-INVESTIGATION.md`, and
`docs/LEGACY-FEATURE-MATRIX.md`.

### Validation in this unit

- `pytest tests\\unit\\test_sii_decoder.py -q`: PASS — 7 passed (run outside
  the sandbox because its temp directory cannot be accessed in-sandbox).
- `ruff check src tests`: PASS.
- `mypy src`: PASS.
- `git diff --check`: PASS.
- Full pytest/coverage: not run because Task 11A is incomplete.

### Exact next step

Continue only Task 11A: implement a lossless BSII v3-to-SiiN decoder, preserve
unknown values or raise a typed error, then implement 3nK. Decode temporary
copies of both real fixtures through ScsC → BSII → SiiN and parse them with the
conservative parser before any task can be marked complete.

## BSII investigation update (2026-09-18T01:10:57-03:00)

- Added a preliminary, GUI-independent `BinarySiiDecoder` with bounded stream
  reads and typed failures. It is deliberately **not wired into the production
  ScsC pipeline** and must not be treated as a completed decoder.
- Real ATS/ETS BSII v3 inputs exposed a structure-layout divergence before the
  first data block: the audited public C++ reference's ordinal-field layout
  does not align with the supplied 1.61 payload. No SiiN output was produced,
  so no parser, editor, or matrix status was advanced.
- The legacy `SII_Decrypt.exe` v1.4.2 was run only on a copy under
  `.decoder-probe`; it failed with `Error setting output file` and supplied no
  usable comparison output. It was not incorporated, and no original fixture
  was modified.
- Ruff, mypy, and `git diff --check` pass after the investigation. Full pytest
  and coverage remain pending because Task 11A is still incomplete.

Continue only with verified BSII v3 format evidence (or a legally reviewed,
fixture-proven compatible decoder); do not guess the remaining structure
layout, and do not start Task 11B.
