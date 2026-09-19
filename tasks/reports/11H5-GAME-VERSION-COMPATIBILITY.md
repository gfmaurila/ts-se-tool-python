# 11H.5 — Game version compatibility and decoder diagnostics

`GameVersion` is opaque and exact-match only. The explicit registry validates
ATS 1.61 and ETS2 1.61 only; 1.62 and every other unknown future version are
UNVALIDATED. Missing version is UNKNOWN. No comparison such as `>= 1.61` is
used.

Validated versions permit read/write. UNVALIDATED, UNKNOWN and UNSUPPORTED are
read/diagnostic only and blocked before SaveEditService reads, backs up or
stages a save. An unsafe override is explicit, backend-only and disabled by
default.

`SaveDiagnosticService` is read-only and returns format, decoder/parse outcome,
block count, compatibility and write permission. Decoder capabilities declare
SiiN/ScsC/BSII read support and no ScsC/BSII encoding.

No source available to this project reliably detects a game version from the
observed save fixtures; absence is deliberately UNKNOWN. A future version source
must explicitly produce a `GameVersion`, then controlled QA validation must
precede an explicit registry update.

## Final gate

Automatic version detection: **NOT AVAILABLE — no reliable source observed.**
The full regression was executed in isolated short basetemps: 150 unit tests,
9 general integrations, 5 vehicle/trailer integrations, and 3 driver
integrations, all passing (167 passed, 0 failed, 0 skipped). Consolidated
coverage is **81.31%**, above the unchanged 80% gate. Ruff and mypy pass.

Write-guard regressions prove UNVALIDATED, UNKNOWN and UNSUPPORTED assessments
fail before the target is read or a backup/staging/atomic replace can occur.
ATS/ETS2 1.61 exact entries remain VALIDATED; ATS/ETS2 1.62 and 1.99 remain
UNVALIDATED.
