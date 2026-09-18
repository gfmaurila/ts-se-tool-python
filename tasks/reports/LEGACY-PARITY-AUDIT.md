# TS SE Tool 0.3.11.0 parity audit

Completed on 2026-09-18. The primary C# reference was audited by forms,
tabs, profile editor, save models, decoder, utilities, and entry points.

- 44 relevant capabilities identified: 4 implemented, 18 partial, 21 not
  implemented, 1 not applicable.
- Major gaps: legal ScsC/BSII decoding; safe atomic write; profile/info IO;
  profile rename/import/export; player/company identity and unlocks; vehicle
  and trailer components; garage relocation; freight/cargo; convoy/settings,
  colors, localization and resource/update features.
- Full traceability is in `docs/LEGACY-FEATURE-MATRIX.md`.
- No fixtures or application functionality were changed in this audit.

Validation: Ruff PASS; mypy PASS; pytest PASS (26 passed, 84.64% coverage);
`git diff --check` PASS.
