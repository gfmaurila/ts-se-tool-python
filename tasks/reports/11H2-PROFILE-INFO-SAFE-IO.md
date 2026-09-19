# Task 11H.2 - Profile and info.sii safe I/O

Timestamp: 2026-09-18T21:03:49-03:00

## Legacy evidence and scope

`SaveFileProfileData.cs:476-588,619-663` reads and prints `profile_name`,
`creation_time`, and `save_time` within `user_profile`. `SaveFileInfoData.cs`
reads and prints `save_container` metadata: `name`, `time`, `file_time`,
`version`, `info_version`, info counters, `info_money_account`, and
`info_explored_ratio`; `info_money_account` is a signed `long`.
`ZipDataUtilitiescs.cs:86-145` creates ZIP entries by basename and extracts
selected entries. Profile rename/clone behavior is in the profile-editor forms
and is already represented by `ProfileIdentityEditor`/`ProfileCloner`.

## Implementation

Added `ProfileSiiModel`, `InfoSiiModel`, and `ProfileInfoService`. Models read
only proven metadata while retaining their original `SiiDocument`; no file is
rebuilt. The service decodes SiiN directly or opaque files through `SiiDecoder`,
then uses the existing `SafeSaveWriter` for staged SiiN output, unique exact-byte
backup, source-byte concurrency check, reparse validation, fsync, and atomic
replace. It supports the explicit, legacy-proven mutations:

- profile name via the existing 1-30 character profile identity contract;
- `info_money_account` as a signed integer.

Candidate validation reparses the respective model and verifies the modified
field. Failures before replacement retain the original; a replace failure
retains the backup and is not silently restored.

## Identity, rename, clone, archive, settings ZIP

`profile_directory_identity` remains the central UTF-8 uppercase hexadecimal
mapping. Regression coverage retains `Caf\u00e9 -> 436166C3A9`; directory rename
uses the requested identity, not `_clone`. Existing selective clone keeps the
legacy-approved profile/settings files and autosave by default, expands to
allowed save assets only with `full=True`, changes profile name plus creation
time, and batch clone rolls back completed destinations on failure.

The evidence establishes settings ZIP, not a generic profile archive policy.
The legacy ZIP utility stores selected file basenames; no broader archive or
automatic restore policy was located, so it is **NOT IMPLEMENTED IN LEGACY**.
`ProfileSettingsZip` preserves the proven selected root files: `config.cfg`,
`config_local.cfg`, `controls.sii`, and selected `gearbox_*.sii`; export/import
staging, traversal containment, and Zip Slip rejection remain covered.

## Fixture validation

ATS copied fixtures: `profile.sii` has `user_profile` metadata version 6;
`profile_name`, `creation_time`, and `save_time` parse. `info.sii` has
`save_container`, version 97, `info_version=1`, and all modelled fields. Safe
temporary profile rename and info money mutation write SiiN, reparse, and retain
exact backups; originals remain unchanged.

ETS2 copied fixtures: same profile structure; `info.sii` version 102 and
`info_version=1`. The same safe mutation/reparse/backup flow passes and source
fixtures remain unchanged.

## Quality and limitations

- Full pytest: **140 passed, 0 failed, 0 skipped** with
  `--basetemp=.pytest-tmp-11h2`.
- Coverage: **83.50%**. Ruff PASS. mypy PASS.
- No profile, QA profile, real save, Steam, ATS, ETS2, `config.cfg`, or
  `g_save_format` was modified.

`InfoSiiModel` intentionally does not yet expose every legacy counter or
dependency record, and no proof supports automatically synchronizing info with
profile/game edits. Therefore feature-matrix totals remain conservative:
**44 total; 19 IMPLEMENTADO, 16 PARCIAL, 8 NAO IMPLEMENTADO, 1 N/A**. No status
was promoted merely for this bounded foundation.
