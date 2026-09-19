# Continuation Report

## Task 11H.6 - Profile / Discovery / Settings / Backup GUI (2026-09-18T23:15:07-03:00)

- Status: **PARCIAL**. Implemented the service-backed PySide6 shell for game
  roots and switching, profile/save discovery, profile metadata, read-only
  diagnostics, profile rename/clone preview/actions, settings ZIP transfer, and
  TSSE backup listing/explicit restore. The UI delegates to existing application
  services and does not directly write game/profile files.
- GUI fixture tests: 5 passed. Ruff PASS; mypy PASS. The requested full suite
  collected 170 tests, but its current coverage report is **76%**, below the
  mandatory 80% gate; therefore no completion claim is valid yet. Add meaningful
  desktop dialog/error/busy/compatibility tests before rerunning the full suite.
- No production save/profile, TSSE QA profile, fixture source, ATS, ETS2, or
  Steam was modified or executed. Report:
  `tasks/reports/11H6-PROFILE-DISCOVERY-SETTINGS-BACKUP-GUI.md`.
- Next safe continuation: finish the 11H.6 coverage gate only. Do **not** start
  11H.7.

## Task 11H.5 - Final gate / closure (2026-09-18T23:15:00-03:00)

- Status: **CONCLUIDA**. Full regression evidence: 167 passed, 0 failed,
  0 skipped; coverage 81.31% (>=80%); Ruff PASS; mypy PASS.
- Registry remains exact: ATS/ETS2 1.61 VALIDATED; 1.62 and future versions
  UNVALIDATED. Automatic version detection is NOT AVAILABLE — no reliable
  source observed. UNKNOWN, UNVALIDATED and UNSUPPORTED writes are blocked
  before read, backup, staging or replacement; the unsafe override is explicit.
- No profile, QA profile, fixture source, save or game process was modified.
  Next task remains **11H.6 - Profile/Discovery/Settings/Backup GUI**, not
  started.

## Task 11H.5 - Game version compatibility and decoder diagnostics (2026-09-18T23:00:00-03:00)

- Added exact-version compatibility registry: ATS/ETS2 1.61 validated only;
  future and unknown versions are write-blocked by default. Added read-only
  decoder diagnostics/capabilities and an explicit unsafe backend override.
- `SaveEditService` guards before read/backup/staging when given an assessment.
  No real save/profile was modified. Report:
  `tasks/reports/11H5-GAME-VERSION-COMPATIBILITY.md`.

## Task 11H.4 - Company drivers and Convoy backend (2026-09-18T22:40:00-03:00)

- Status: **CONCLUIDA**. Added typed driver graph/view support and reused
  legacy-proven garage-slot relocation. Added the proven Convoy GPS
  current-position gzip/hex codec and `player.my_truck_placement` writer; no
  GUI or multi-save transfer.
- ATS/ETS driver reads pass; ATS garage driver placement is not observed. ETS
  driver relocation passed `SaveEditService` on a copied save. Convoy units are
  not observed in either fixture. No real/QA profile or save changed.
- Targeted regression and fixtures PASS; Ruff and mypy PASS. Matrix totals:
  44 total, 19 IMPLEMENTADO, 20 PARCIAL, 4 NAO IMPLEMENTADO, 1 N/A.
- Report: `tasks/reports/11H4-COMPANY-DRIVERS-CONVOY-BACKEND.md`. Recommended
  next task: **11H.5 - Game version compatibility and decoder diagnostics**.

## Task 11H.3 - Vehicle/trailer component parity (2026-09-18T22:15:00-03:00)

- Status: **CONCLUIDA**. Added typed, side-effect-free vehicle/trailer graph
  helpers and aligned individual trailer repair with the legacy slave-chain
  loop. Existing truck repair/refuel, component/accessory/plate/odometer views
  and `SaveEditService` were reused; no GUI was implemented.
- ATS fixture: repairable vehicle observed; trailer and both assigned references
  were null/not observed as applicable. ETS fixture: vehicle and trailer
  observed; assigned references null. Copied-save truck and ETS trailer
  mutations passed `SaveEditService` backup/staging/reparse checks. Sources and
  all real/QA profiles remained untouched.
- Regression: 150 tests passed (136 unit, 14 integration) in isolated short
  basetemps; consolidated coverage measured 83.08% and remains above 80%; Ruff
  and mypy PASS. Windows path length requires the task's short basetemp naming.
- Matrix/audit totals: 44 total, 19 IMPLEMENTADO, 18 PARCIAL, 6 NAO
  IMPLEMENTADO, 1 N/A. Vehicle/trailer backend moved to partial factual
  coverage; GUI and semantic paint writes remain deferred.
- Files changed: `vehicle_graph.py`, vehicle views, trailer editor, exports,
  unit/integration tests, matrix, parity audit and this report. Detailed report:
  `tasks/reports/11H3-VEHICLE-TRAILER-COMPONENT-PARITY.md`.
- Recommended next task: **11H.4 - Company drivers and convoy backend**. Do not
  begin it without an explicit request.

## Task 11H.2 - Profile and info.sii safe I/O (2026-09-18T21:03:49-03:00)

- Status: **CONCLUIDA**. Added `src/tsse/application/profile_info.py` with
  bounded `ProfileSiiModel`/`InfoSiiModel` and `ProfileInfoService`. It reads
  legacy-proven metadata without rebuilding unknown content and safely writes
  profile name and signed `info_money_account` through existing `SiiDecoder` +
  `SafeSaveWriter` staging/backup/concurrency/atomic infrastructure.
- Profile identity stays centralized in `profile_directory_identity`; UTF-8
  uppercase hex `Caf\u00e9 -> 436166C3A9`, directory rename, selective clone,
  clone rollback, settings ZIP export/import, and Zip Slip protections remain
  covered by regressions. Generic archive/automatic restore is not evidenced in
  legacy; only selected basename settings ZIP is established.
- ATS and ETS2 copied profile/info fixtures were decoded, parsed, safely mutated
  in temporary copies, serialized as SiiN, reparsed, and backed up exactly;
  source fixtures were unchanged. ATS info version observed 97; ETS2 observed
  102; both profile version 6 and info_version 1.
- Final gates: pytest **140 passed, 0 failed, 0 skipped** with
  `--basetemp=.pytest-tmp-11h2`; coverage **83.50%**; Ruff PASS; mypy PASS.
  No real profile/save/QA profile, game process, config, or save format setting
  was modified.
- Matrix totals stay 44: 19 IMPLEMENTADO, 16 PARCIAL, 8 NAO IMPLEMENTADO, 1
  N/A. Info/profile remains bounded rather than a complete legacy model; no
  status was promoted without full evidence. Recommended next task: **11H.3 -
  Vehicle/Trailer Component Parity**, not started. Report:
  `tasks/reports/11H2-PROFILE-INFO-SAFE-IO.md`.

## Task 11H.1 - SII grammar and typed-reference foundation (2026-09-18T20:38:00-03:00)

- Status: **CONCLUIDA**. Added immutable `SiiGraph` and typed-reference
  contracts in `src/tsse/core/sii/references.py`, exported through `core.sii`.
  It centralizes unit lookup, typed scalar/indexed references, status inspection,
  and read-only chain traversal. It reports valid/null/missing/wrong-type/
  malformed outcomes without mutating the AST.
- Parser audit: both decoded real 1.61 fixtures have zero unparsed block lines;
  current raw-value preservation already covers observed strings (including
  escaped), numbers, booleans, tokens, `null`, and indexed fields. No speculative
  grammar production was added. Unit tests cover unknown preservation,
  round-trip, reference errors, indexes, duplicates, and side-effect freedom.
- ATS copied fixture: 17,672 blocks; player/economy/company/garage/vehicle/
  driver_ai/job_offer_data observed; garage and job-offer graph relations pass;
  trailer/cargo/convoy unit blocks not observed. ETS2 copied fixture: 43,027
  blocks; same plus trailer observed; cargo/convoy unit blocks not observed.
  Both decrypt -> parse -> graph -> serialize/reparse validations passed and
  originals remained unchanged.
- Final gates: pytest **135 passed, 0 failed, 0 skipped** with
  `--basetemp=.pytest-tmp-11h1`; coverage **83.50%**; Ruff PASS; mypy PASS.
  No real profile, QA profile, save, Steam, ATS, or ETS2 was modified/launched.
- Matrix/audit totals stay 44: 19 IMPLEMENTADO, 16 PARCIAL, 8 NAO IMPLEMENTADO,
  1 N/A. Parser/typed graph remain partial by design: vector/color semantic
  types and the complete legacy relationship catalog are still not modeled.
- Recommended next task: **11H.2 - Profile and info.sii safe I/O**. Do not start
  it without explicit instruction. Report:
  `tasks/reports/11H1-SII-GRAMMAR-TYPED-REFERENCES.md`.

## Task 11H - Legacy parity gap review (2026-09-18T20:29:37-03:00)

- Status: **CONCLUIDA / AUDIT ONLY**. No production code, QA profile, real save,
  fixture, game process, or configuration was modified. Current-state gates:
  pytest 129 passed, 0 failed, 0 skipped; Ruff PASS; mypy PASS.
- Authoritative totals remain 44: 19 IMPLEMENTADO, 16 PARCIAL, 8 NAO
  IMPLEMENTADO, 1 N/A. Incomplete total is 24, classified from primary legacy
  evidence as 4 backend-missing, 5 GUI-only, 14 backend-plus-GUI, 1 validation-
  only, and 0 not-applicable. The historical matrix table predates 11D-11G;
  no status was changed without new implementation evidence.
- Proposed task order: 11H.1 SII grammar/typed graph; 11H.2 profile+info safe
  I/O; 11H.3 vehicle/trailer components; 11H.4 company drivers+convoy backend;
  11H.5 game-version compatibility+decoder diagnostics; 11H.6 profile/settings
  GUI; 11H.7 main/player/company/market GUI; 11H.8 vehicle/trailer/convoy GUI;
  11H.9 colors/previews/localization/help-update.
- Immediate recommendation: **11H.1**, because typed graph/grammar evidence is
  the dependency shared by profile/info, vehicles, drivers, and convoy work.
  Do not start it without explicit user instruction. Detailed audit:
  `tasks/reports/11H-LEGACY-PARITY-GAP-PLAN.md`.

## Task 11G.3 - Production Save Write Pipeline (2026-09-18T20:23:40-03:00)

- Status: **CONCLUIDA**. Added GUI-independent `SaveEditService`: recognized
  ScsC/BSII/3nK inputs follow `SiiDecoder`/`LegacySiiDecryptAdapter`; SiiN
  bypasses decrypt. It accepts caller-owned AST mutation/validation and writes
  SiiN through `SafeSaveWriter` only.
- `SafeSaveWriter` now records original/backup/written SHA-256 values, validates
  staged content, verifies exact backup bytes, detects source changes from the
  initial read through replacement, uses fsynced sibling staging and atomic
  replace, and returns typed backup/replace errors. Explicit restore safely
  stages/validates a selected TSSE backup while retaining it and backing up the
  current target; backup discovery lists only matching TSSE backups newest first.
- Validation: full pytest **129 passed, 0 failed, 0 skipped** with
  `--basetemp=.pytest-tmp-11g3`; coverage **83.03%** (>=80%); Ruff PASS; mypy
  PASS. ATS and ETS2 1.61 integration uses copies of the supplied fixtures and
  passed decrypt -> ADR mutation -> production SiiN write -> reparse; originals
  remained unchanged.
- Architectural decision: plaintext SiiN is the official output. Task 11G.2
  game loads proved this for ATS/ETS2 1.61, so a BSII/ScsC encoder is NOT
  REQUIRED. No real QA profile, real game save, Steam, or game executable was
  accessed in this task.
- Matrix/audit were updated. Totals remain 44: 19 IMPLEMENTADO, 16 PARCIAL, 8
  NÃO IMPLEMENTADO, 1 N/A. GUI remains out of scope.
- Next task: user must explicitly select a next task after reviewing the matrix;
  do not start GUI or any successor automatically. Detailed report:
  `tasks/reports/11G3-PRODUCTION-SAVE-WRITE.md`.

## Task 11G.2 - FINAL (2026-09-18T20:16:09-03:00)

- **CONCLUIDA. ARCHITECTURAL DECISION: PLAINTEXT SiiN WRITE SUPPORTED FOR ATS
  1.61 AND ETS2 1.61.** A BSII/ScsC encoder is **NOT required** for the
  proven plaintext write pipeline.
- ATS: manual game load PASS for QA-only `TSSE_TEST_ATS` / `autosave_job`;
  post-game read-only verification confirms SiiN plaintext and
  `economy.adr = 1`.
- ETS2: manual game load PASS for QA-only `TSSE_TEST_ETS2` / `autosave_job`;
  post-game read-only verification confirms SiiN plaintext and
  `economy.adr = 1`; final SHA-256 is
  `179aa0ca9992ea8959b5a3b21a57e656df1dce3c71c2027fb397aeb0f9f90fa8`.
- Retained ATS backup:
  `D:\Work\American Truck Simulator\profiles\545353455F544553545F415453\save\autosave_job\game.sii.tsse-backup-cdefb4f22fd74f5b8d3a6fe3cac95aa7`.
  Retained ETS2 backup:
  `D:\Work\Euro Truck Simulator 2\profiles\545353455F544553545F45545332\save\autosave_job\game.sii.tsse-backup-144afd8f54b24be587aaa46458ce2a3e`.
  No restoration was authorized.
- No original/non-QA profile was touched. No other save was touched. No game
  executable or Steam process was launched by Codex. Detailed evidence and
  original/backup/modified hashes are in
  `tasks/reports/11G2-PLAINTEXT-WRITE-VALIDATION.md`.
- Next task is 11G.3 - Production Save Write Pipeline, but it is **NOT
  STARTED** and must not be started without a new explicit user instruction.

## Task 11G.2 - ETS2 controlled plaintext write (2026-09-18T20:13:03-03:00)

- ATS is **PLAINTEXT SiiN WRITE SUPPORTED**: user reported a successful ATS
  1.61 load of QA profile `TSSE_TEST_ATS` / `autosave_job`, and the post-game
  read-only verification confirmed SiiN plaintext and `economy.adr = 1`.
  Its backup is retained; no restoration was authorized.
- State: **READY FOR MANUAL GAME TEST** for ETS2. Only
  `D:\Work\Euro Truck Simulator 2\profiles\545353455F544553545F45545332\save\autosave_job\game.sii` was modified. Its other save, `info.sii`,
  `profile.sii`, all other profiles, and all ATS files were not modified in
  this ETS2 unit.
- Original format was ScsC. `LegacySiiDecryptAdapter -> parser -> AST`
  produced 17,460 blocks. Controlled field: `economy.adr: 0 -> 1`.
  SiiN serialization, reparse, domain/block-count validation, concurrent
  change detection, fsynced sibling staging, and atomic replace all passed.
- Backup: `game.sii.tsse-backup-144afd8f54b24be587aaa46458ce2a3e`; original
  and backup SHA-256: `5b2935d1cc56c66adae0dc719355f2d1d581f571df397ac2c4d865a6d2fe9496`.
  Modified SHA-256: `179aa0ca9992ea8959b5a3b21a57e656df1dce3c71c2027fb397aeb0f9f90fa8`.
- Pre-write regression test gate: 32 passed with `--basetemp=.pytest-tmp-11g2`.
  The current source has no changes since Ruff PASS/mypy PASS in the ATS unit.
- Next exact step: user manually opens ETS2, selects only `TSSE_TEST_ETS2`,
  loads `autosave_job`, verifies no error and ADR=1, closes the game, and
  replies PASS or FAIL. Do not launch the game or restore backups without
  authorization. Detailed report: `tasks/reports/11G2-PLAINTEXT-WRITE-VALIDATION.md`.

## Task 11G.2 - ATS controlled plaintext write (2026-09-18T20:05:56-03:00)

- State: **READY FOR MANUAL GAME TEST**. The two authorized profiles were found. Only ATS `TSSE_TEST_ATS` was modified; ETS2 `TSSE_TEST_ETS2` is untouched and still requires its independent validation.
- ATS selected only `D:\Work\American Truck Simulator\profiles\545353455F544553545F415453\save\autosave_job\game.sii` (available saves: `autosave`, `autosave_job`). `info.sii`, `profile.sii`, all other saves, and all non-QA profiles were not modified.
- The original was `ScsC`; `LegacySiiDecryptAdapter -> parser -> AST` produced 16,996 blocks. The controlled, reversible field change is `economy.adr: 0 -> 1`. It was serialized to SiiN plaintext, reparse/domain validated, and written by `SafeSaveWriter` with sibling fsynced staging, source-change verification, unique backup, and atomic replacement.
- Backup: `game.sii.tsse-backup-cdefb4f22fd74f5b8d3a6fe3cac95aa7`; original and backup SHA-256: `be26263b18ced6e634c639e79df637f8f8cdcdebcfc0a5aa925e65c23483fa61`. Modified SHA-256: `0eb293778fe5e7350faf94de1e910fa15c0e7fdae0fe1ea5391d58d26c940415`.
- Quality gates before writing: targeted tests 32 passed with `--basetemp=.pytest-tmp-11g2`; Ruff PASS; mypy PASS. The first sandboxed test attempt had only temp-directory cleanup permission errors; the escalated rerun passed.
- Risk/next step: do not launch Steam/game automatically and do not make any further write. User must load ATS profile `TSSE_TEST_ATS`, save `autosave_job`, confirm successful load and the ADR skill changed 0 -> 1, close the game, then reply PASS or FAIL. Preserve evidence; restore the backup only with explicit user authorization. Then record ATS decision and separately begin ETS2 validation if instructed.
- Detailed report: `tasks/reports/11G2-PLAINTEXT-WRITE-VALIDATION.md`.

## Task 11E -- CONCLUIDA (2026-09-18T15:30:28-03:00)

- Implemented and validated truck refuel plus total/individual repair, trailer
  total/individual repair and slave traversal, and lossless read-only views
  for license plate, odometer, wheels, accessories, and paint accessories.
- Legacy paint clipboard is PASS: immutable `PartData` snapshot, `TruckPaint`
  header, GZip, uppercase hexadecimal, and paste to `PartData`. `PartData ->
  vehicle_paint_job_accessory` write-back is NOT ESTABLISHED and was not invented.
- ATS vehicle, ETS2 vehicle, and ETS2 trailer temporary SiiN validation passed.
  ATS trailer is NOT OBSERVED. Fixture hashes: ATS game
  `036AC1DD775B4E7E1B0DC11C29E7E039D97950CE7AAB8140DD6F6D59DF2E09CC`; ETS2
  game `DEBE167F2210C69E81588110C93D24A860E400A5C212EA80359A617C6E07868D`;
  ATS profile `BD12E40BC0B2B8AF84CE18F0176813519C2C2E890D3AD2EE2C80E798D174D9CE`;
  ETS2 profile `2C11F43AC85E9A803AFBBCA9FAC3818C38C410D44D8B822CA336D02712D29BE6`.
- Final gates: 96 passed; coverage 85.03% (>=80% PASS); Ruff PASS; mypy PASS;
  pytest PASS. `git diff --check`: INDISPONIVEL -- Git nao encontrado.
- Decisions: truck wheels repair clears `wheels_wear[]`; trailer total repair
  traverses its slave chain; individual repair changes only the selected trailer;
  plate/odometer remain read-only; paint data is transient `PartData`.
- Next: Task 11F is ready but NOT STARTED.

## Task 11D — CONCLUÍDA (2026-09-18T14:38:50-03:00)

- Finalized: Level/XP, gender, company, HQ, visited cities/count, dealers,
  recruitments, polymorphic driver resolver (`driver_player`/`driver_ai`),
  readiness relationship, quit-warned preservation, and ATS/ETS2 game/profile
  structural validation. Fixture originals are intact.
- Final gates: 63 passed; coverage 82.38% (>=80% PASS); Ruff PASS; mypy PASS;
  pytest PASS. `git diff --check`: INDISPONÍVEL — Git não encontrado.
- HQ derives from owned garages rather than visited cities. Visited arrays are
  parallel; driver readiness is index-paired; quit-warned has no equal-length
  invariant. Do not start Task 11E without explicit user instruction.

## Task 11D update (2026-09-18T13:20:00-03:00)

- Located the authoritative `Globals.PlayerLevelUps` initialization in `TS SE Tool/FormMethods.cs:324-325` (ETS2) and `:333-334` (ATS): each has 30 steps. `Economy.cs:1372-1422` proves level calculation and the 0..150 clamp. Added tested `level_to_experience` / `experience_to_level` using those exact per-game arrays; level 0 is 199 XP, level 1 is 699 XP, and ATS level 150 is 986999 XP.
- C# matrix: profile/company identity = `SaveFileProfileData` (`company_name`, `male`); HQ = `Player.hq_city` + `FormMethodsCompanyTab`; visited/dealer/recruitment arrays = `Economy` + `DataManipulation`; drivers = `Player.drivers`, `Driver_AI`, `DataManipulation`. All except level/XP remain unimplemented because their reference and current-fixture relationship mapping is incomplete.
- Targeted checks: Ruff PASS, mypy PASS, player-editor pytest has not yet been rerun after correcting the level-150 expected regression. Task 11D remains PARTIAL. Do not start 11E.

## Task 11C completion (2026-09-18T13:00:00-03:00)

- Validated directory identity/rename and selective single/full/multi clone flows with project-local pytest bases. Staging names were shortened after a Windows path-length regression. `Café -> 436166C3A9` is covered.
- Added `ProfileSettingsZip`, mirroring legacy `FormProfileEditorSettingsImportExport` and `ZipDataUtilities`: selected `config.cfg`, `config_local.cfg`, `controls.sii`, and `gearbox_*.sii` use root-level basename entries. Python adds staging, traversal/absolute/drive/UNC rejection, resolved containment, archive limits, and rollback.
- Full gates: Ruff PASS, mypy PASS, pytest 53 PASS, coverage 82.75%. Git unavailable. Task 11C is CONCLUÍDA; do not start Task 11D without a new user instruction.

## Task 11C update (2026-09-18T12:30:00-03:00)

- C# was re-read before implementation: `TextUtilities.FromStringToHex` proves UTF-8 uppercase hexadecimal directory IDs. `FormProfileEditorRenameClone` proves rename changes only `profile_name`; clone changes `profile_name` and `creation_time`, selectively copies profile assets and allowed save assets, and does not touch `info.sii`.
- Added staged transactional directory rename and selective named/full/multi clone APIs plus targeted regressions. The initial quality check reported formatting/import errors and they were fixed. Pytest then could not create `C:\\Users\\gfmau\\AppData\\Local\\Temp\\pytest-of-gfmau` under the sandbox (WinError 5); run it outside sandbox or with a project-local `--basetemp` before considering this code validated.
- Task 11C is PARTIAL. ZIP import/export staging, traversal protection, and transactional restore remain unimplemented. Do not start Task 11D.

## Task 11C profile identity and transfer (2026-09-18T12:00:00-03:00)

- Mapped legacy `SaveFileProfileData`, `SaveFileInfoData`,
  `FormProfileEditorRenameClone`, and settings import/export. Implemented the
  safe plaintext core: `ProfileIdentityEditor` replaces only `profile_name`
  through `SafeSaveWriter`, retaining unrelated fields/text. It follows the
  legacy UI's trim-space, 1–30-character, and `\\`/`|` forbidden-character
  constraints.
- Added regressions for normal edit, unknown field preservation, missing field,
  invalid limits/characters, backup, and reparse. Directory rename (hex path),
  full/multi clone identity mutation, and ZIP import/export remain pending;
  they require a profile transfer model and should not silently replace the
  safe clone behavior. Task 11C is PARTIAL; do not start Task 11D.

## Task 11B safe save I/O (2026-09-18T11:40:00-03:00)

- Implemented `SafeSaveWriter` in infrastructure for `game.sii`, `info.sii`, and `profile.sii`: candidate validation, fsynced sibling staging, reparse, source-change check, unique backup, and atomic replacement.
- Regression tests cover backup, unknown-field preservation, re-open parsing, temp cleanup, and invalid rollback. No fixture or real save is written; encrypted-output encoding remains outside this task.

### Completion (2026-09-18T11:50:00-03:00)

- Task 11B complete. Full gates: Ruff PASS, mypy PASS, pytest 36 PASS,
  coverage 84.28%. Git is still unavailable, so `git diff --check` could not
  execute. ATS/ETS fixtures remain read-only; their decoder/parser validation
  remains recorded under Task 11A. Do not start Task 11C automatically.

## Task 11A adapter decision update (2026-09-18T10:00:00-03:00)

- `SiiDecoder` is now an infrastructure file-level boundary: SiiN passes directly and opaque inputs are copied into a private temporary directory for `LegacySiiDecryptAdapter`.
- One canonical executable is at `src/tsse/infrastructure/decoder/resources/SII_Decrypt.exe`; SHA-256 `c3af317386353c7b22ea6d91acf66f054b0ff1fd7e5192274ee1ff89476146f7`.
- Supplied ATS and ETS copies remain byte-for-byte preserved. This executable returns `-1` / `Input file not set` for copied relative inputs; ATS/ETS parser validation is FAIL. Do not start Task 11B.
- Upstream MPL-2.0 was identified, but the supplied binary provenance is not independently matched; PyInstaller embedding is blocked. Unit decoder tests: 11 passed. Full suite: 32 passed, coverage 83.98%; Ruff and mypy passed. `git diff --check` could not run because git is absent from PATH in this environment.

## Upstream build attempt (2026-09-18T10:10:00-03:00)

- Inspected retained `TLExpress/SII_Decrypt` `v1.4.2-rc0` archive. The official Lazarus `.lpi` has Release i386/win32 and x86_64/win64 targets, optimization 3, smart-linking, and requires FPC/Lazarus LazUtils.
- `fpc`, `lazbuild`, and `msbuild` are absent; no global tool was installed. The archive's included Lazarus Release x64 executable (SHA-256 `edbb848803d75a7208a98b38d43deddefb31a19a42d7f58d7ef21833738b34db`) was run only through a temporary-copy adapter on ATS 1.61. It fails identically: exit `-1`, stdout `Input file not set`, empty stderr, no output.
- Task 11A is BLOCKED/PARCIAL. ATS and ETS end-to-end parser validation remains FAIL, PyInstaller remains blocked, and Task 11B must not begin. Resume only with an approved FPC/Lazarus environment to reproduce a tagged upstream Release, or a verified upstream fix compatible with 1.61 fixtures.

## CLI root cause update (2026-09-18T10:25:00-03:00)

- The previous `Input file not set` was an invocation-wrapper issue. Direct `cmd.exe` execution of the upstream Release x64 with documented `-i game.sii -o output.sii` receives the input. The adapter now copies its executable to the same private temporary working directory as the save before launching it.
- ATS and ETS copied fixtures both reach BSII parsing and fail identically: `TSIIBin_Decoder.LoadLayoutBlockLocal: Unsupported value type (0x00000007)`, exit `-1`, stdout only, no output. Upstream v1.4.2's own changelog says type 0x07 support appeared in v1.5.2. This is the verified compatibility boundary, not a Python quoting or path error.
- Toolchain status: FPC ABSENT; Lazarus/lazbuild ABSENT. `winget` and Chocolatey are present, but no installation was requested or performed. Build status is NOT EXECUTED, not FAIL. Git was not found by `where.exe` or standard Program Files locations.

## Current upstream candidate (2026-09-18T10:35:00-03:00)

- Official `TheLazyTomcat/SII_Decrypt` documentation identifies v1.5.2 as its latest release, MPL-2.0, with ATS/ETS, ScsC, BSII, 3nK, and non-interactive `-i/-o` CLI support. Its changelog explicitly adds value types 0x2F and 0x07.
- The project is discontinued and distributes binaries from its official `bin` branch. No candidate was downloaded because authorization is required. If authorized, download only that official tagged/bin x64 artifact, record its URL/hash, and test ATS then ETS strictly through temporary copies and the Python parser.

## Task 11A completion (2026-09-18T11:32:57-03:00)

- With authorization, downloaded the official `TheLazyTomcat/SII_Decrypt` `bin` archive. It identifies version 1.5.3, MPL-2.0, and includes the console Lazarus Release x64 artifact. The canonical project copy is `src/tsse/infrastructure/decoder/resources/SII_Decrypt.exe`, SHA-256 `3ad9389b328ac47bd2d069068a94abdb816adae26a777c33b627554882fea45f`; the verbatim MPL text is alongside it under `resources/licenses/`.
- The official 1.5.3 changelog supports BSII type 0x07 (1.5.2) and BSII format v3 (1.5.3). Through `cmd.exe /d /s /c .\\SII_Decrypt.exe -i game.sii -o game.sii.decoded` in the adapter-owned temporary directory: ATS decoded to 5,952,903-byte SiiN and parser produced 17,672 blocks; ETS2 decoded to 13,200,677-byte SiiN and parser produced 43,027 blocks. Originals are unchanged.
- `scripts/build.ps1` now prepares PyInstaller one-file resource inclusion. Matrix updated for ScsC/BSII IMPLEMENTADO. Full gate: Ruff PASS, mypy PASS, pytest 32 PASS, coverage 84.74%. Git still absent, so `git diff --check` cannot run. Task 11A is complete; STOP and do not start Task 11B.

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

## Task 11F.3 validation update (2026-09-18T16:07:32.1078404-03:00)

Task 11F.3 garage-sale implementation is validated and complete. The decoder
was run through `LegacySiiDecryptAdapter(temp_root=.tmp-11f3-validation)` on
temporary copies only. ATS `garage.sacramento` and ETS2 `garage.kiel` both
completed decrypt, parse, sale, SiiN serialize/reparse, with original fixture
SHA-256 unchanged.

Targeted regression: `tests/unit/test_garage_relocation.py` — 12 passed.
Ruff and mypy pass for the changed decoder, sale implementation, and tests.

The next task is 11F.4; it has not been started.

## Task 11F.4 update (2026-09-18T16:13:11.7892674-03:00)

Task 11F.4 Cargo Market is complete. Added `cargo_market.py` with typed
company/city resolution and transactional randomize/reset operations matching
the legacy handlers: ten values based on `economy.game_time +
Random.Next(180,1800)` and reset to an empty seed collection. Excluded
companies (zero job offers) are not modified; job offers and unknown fields
are preserved.

Tests: four Cargo Market tests plus garage relocation/sale regression — 16
passed. Ruff and mypy pass for changed files. ATS and ETS2 real temporary-copy
decrypt/parse/randomize/reset/serialize/reparse validations passed.

Original fixture hashes remained unchanged:
ATS `036AC1DD775B4E7E1B0DC11C29E7E039D97950CE7AAB8140DD6F6D59DF2E09CC`;
ETS2 `DEBE167F2210C69E81588110C93D24A860E400A5C212EA80359A617C6E07868D`.

Next task: 11F.5 — not started.

## Task 11F.5 update (2026-09-18T16:21:41.3792622-03:00)

Task 11F.5 Freight Market is complete within the proven legacy scope. Added
`freight_market.py`: typed resolver and transactional writer for existing
`company.job_offer[] -> job_offer_data` references, exact AddCargo expiration
formula, field formatting/preservation, and transient `ClearJobData` semantics.
The legacy does not allocate new job blocks/IDs or persist deletion; no such
behavior was invented.

Tests: 3 Freight tests; Freight/Cargo/garage subset — 19 passed. Ruff and
mypy pass. ATS and ETS2 temporary-copy resolve/edit/serialize/reparse passed;
original fixture hashes remain unchanged (ATS
`036AC1DD775B4E7E1B0DC11C29E7E039D97950CE7AAB8140DD6F6D59DF2E09CC`, ETS2
`DEBE167F2210C69E81588110C93D24A860E400A5C212EA80359A617C6E07868D`).

Next: 11F final gates — not started.

## Configurable game roots (2026-09-18T16:25:48.3493105-03:00)

Added `GameRootStore` backed by QSettings, runtime manual-root updates in
`ProfileDiscovery`, and a Settings/Configurações dialog in the PySide6 main
window. Manual roots have priority; clearing them restores automatic
Documents discovery. Validation accepts either `profiles` or
`steam_profiles`, without creating directories or touching saves.

Synthetic configuration/discovery/GUI tests: 10 passed. Ruff and mypy pass.
Read-only validation found one profile in each `profiles` and
`steam_profiles` collection under both configured `D:\Work` roots. No save
files were modified.

## Task 11F.5 update (2026-09-18T16:19:24.6772102-03:00)

Task 11F.5 Freight Market is complete within the legacy writer scope. The
implementation resolves existing indexed `job_offer_data` blocks, writes the
fields used by `PrepareCompaniesJobWrite`, reproduces the expiration formula,
updates matching `economy_event` time entries by `unit_link`/`param`, and keeps
`ClearJobData` transient. It intentionally does not allocate new IDs/blocks or
delete persistent offers because the legacy handlers do not do so.

Freight/Cargo/garage regression subset: 19 passed. Ruff and mypy pass. ATS
and ETS2 temporary-copy resolve/edit/serialize/reparse passed; original hashes
remain unchanged. Report: `tasks/reports/11F5-FREIGHT-MARKET.md`.

## Task 11F — final gates and consolidation (2026-09-18T16:38:00-03:00)

Task 11F is **CONCLUÍDA**. Subtasks 11F.1 (garage/market structural
inspection), 11F.2 (garage relocation), 11F.3 (garage sale), 11F.4 (Cargo
Market), and 11F.5 (Freight Market) are implemented within the behavior
established by the legacy C# and covered by regression tests.

Final gates:

- Full pytest: **119 passed, 0 failed, 0 skipped** (`--basetemp=.pytest-tmp-11f-global`).
- Coverage: **82.94%**.
- Ruff: **PASS**.
- mypy: **PASS** (44 source files).

Real 1.61 integration on local temporary copies passed for both games:

- ATS: SII_Decrypt decrypt, parse, garage resolve, Cargo Market company
  resolve, Freight Market job resolve, SiiN serialize/reparse; 17,672 blocks.
- ETS2: the same pipeline; 43,027 blocks.

Fixture SHA-256 remained unchanged before/after validation:

- ATS: `036AC1DD775B4E7E1B0DC11C29E7E039D97950CE7AAB8140DD6F6D59DF2E09CC`
- ETS2: `DEBE167F2210C69E81588110C93D24A860E400A5C212EA80359A617C6E07868D`

The feature matrix and parity audit were updated. Consolidated counts are 44
identified capabilities: 19 IMPLEMENTADO, 16 PARCIAL, 8 NÃO IMPLEMENTADO, and
1 N/A. Remaining gaps are documented by area in the audit; no new behavior
was added during final gates.

Binary boundary: ScsC/BSII decrypt/read, AST editing, and safe temporary SiiN
serialization are supported; ScsC/BSII binary write-back remains
**NÃO IMPLEMENTADO**. The PySide6 GUI opens and is functional as an initial
shell, but does not expose the complete backend. Configurable ATS/ETS2 roots
are implemented and documented.

No original game/profile fixture was modified. No commit or push was
performed. Recommended next task: address the highest-priority remaining
documented gap (GUI integration or the safe ScsC/BSII write pipeline) after an
explicit scope decision. Task 12 was not started.

## Task 11G.1 — save write pipeline investigation (2026-09-18)

Status: **CONCLUÍDA / INVESTIGAÇÃO**. No source code, configuration, fixture,
profile, or save was modified.

Findings:

- Legacy `buttonWriteSave_Click` (`Forms/FormMainControlsMethods.cs`) creates
  `game_backup.sii` with `File.Copy(..., true)` and calls
  `MethodsReadWrite.NewWrireSaveFile`.
- `NewWrireSaveFile` checks `LastModifiedTimestamp`, prepares the model, then
  writes `SiiNunitData.PrintOut(0)` directly with `StreamWriter` to `game.sii`.
- No legacy encrypt/encode/ScsC/BSII write step or external encoder was found.
- Checked-in SII_Decrypt source exposes decrypt/decode and combined
  decrypt-and-decode operations, not reverse encryption/BSII/ScsC encoding.
- Plaintext `game.sii` acceptance by an ATS/ETS2 1.61 game was not proven by a
  controlled game launch; numeric `g_save_format` values 0/1/2 are also not
  established by the checked-in evidence.

Architectural decision: **NOT ESTABLISHED — further controlled game test
required**. No encoder was attempted. The proposed future writer is backup →
decode/parse → edit → staged SiiN serialize → reparse/domain validation →
concurrent-modification check → fsync → atomic replace, with unique backups
and rollback preserving the original.

Report: `tasks/reports/11G1-SAVE-WRITE-INVESTIGATION.md`.

Recommended next step: 11G.2, a controlled QA-profile game-load test using
dedicated `TSSE_TEST_ATS`/`TSSE_TEST_ETS2` profiles. Do not use primary saves.

## Task 11G.2 — controlled plaintext write validation (2026-09-18T16:49:37-03:00)

Status: **QA PROFILE REQUIRED**. Read-only discovery checked only
`D:\Work\American Truck Simulator` and `D:\Work\Euro Truck Simulator 2`,
under both `profiles` and `steam_profiles`. Neither authorized profile was
found: `TSSE_TEST_ATS` and `TSSE_TEST_ETS2`.

No profile was selected, no save was changed, no backup was created, and no
decoder/parser/writer operation was executed. The temporary locator script was
removed. The controlled write validation must resume only after the user
creates/provides both explicitly named QA profiles; normal profiles must not be
cloned or selected automatically.

**Final status correction:** any earlier historical “Next: 11F final gates —
not started” note in this continuation log is superseded by this section;
Task 11F is now CONCLUÍDA and the next task has not been started.

Next: 11F final gates — not started.
