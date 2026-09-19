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

## Post-11F consolidated classification (2026-09-18)

The baseline table above was produced before Tasks 11D–11F. The current
classification below is the authoritative consolidation after those tasks;
the total remains 44 identified legacy capabilities.

- **IMPLEMENTADO:** 19
- **PARCIAL:** 16
- **NÃO IMPLEMENTADO:** 8
- **N/A:** 1

The 11F capabilities are implemented and tested: garage resolution,
transactional driver/vehicle relocation, garage-sale preparation, Cargo Market
seed randomize/reset, and Freight Market resolution/writing/clear semantics.
ATS and ETS2 1.61 integration pipelines passed on temporary decoded copies.

Remaining partial areas include broader GUI/application parity, profile/save
surface breadth, lossless typed-graph coverage, backup/clone policy, and
vehicle/trailer selection/component surfaces. Remaining unimplemented areas
include info/profile settings import-export, convoy tools, shared colors,
rendering, localization, update/help features, and other UI-only capabilities.

The binary boundary is unchanged: ScsC/BSII decrypt/read, AST editing, and
temporary SiiN serialization are supported; ScsC/BSII binary write-back is not
implemented. GUI parity is therefore distinct from backend parity.

## Post-11G.3 production write update (2026-09-18)

The classification totals remain unchanged: **44 total; 19 IMPLEMENTADO, 16
PARCIAL, 8 NÃO IMPLEMENTADO, 1 N/A**. The existing safe staged write
capability is now a production service (`SaveEditService`) with structured
evidence, exact-byte unique backups, source-change detection, atomic restore,
and backup discovery. ATS/ETS2 1.61 copied-fixture integrations pass; Task
11G.2 independently established game acceptance of SiiN plaintext for both
games. Therefore an ScsC/BSII encoder is not required for the intended write
pipeline. GUI work remains out of scope and is not reclassified.

## Post-11H.3 vehicle/trailer backend update (2026-09-18)

The authoritative classification is now **44 total; 19 IMPLEMENTADO, 18
PARCIAL, 6 NÃƒO IMPLEMENTADO, 1 N/A**. The reclassification is factual, not a
GUI claim: the legacy-proven truck/trailer condition writes, component and
accessory projections, typed component graph resolution, and copied-fixture
validation are now covered. `FormMethodsTrailerTab.buttonTrailerElRepair_Click`
was also aligned with its actual slave-chain loop, so individual trailer repair
now repairs each chained unit. The remaining scope in these rows is GUI wiring,
selection switching, and the deliberately deferred semantic paint/color work.

## Post-11H.4 driver and Convoy backend update (2026-09-18)

The authoritative totals are **44 total; 19 IMPLEMENTADO, 20 PARCIAL, 4 NÃƒO
IMPLEMENTADO, 1 N/A**. Company-driver and Convoy rows moved to partial based on
typed driver read/garage relocation and the legacy-proven GPS clipboard/current
placement mutation. GUI, multi-save Convoy transfer, and unsupported driver
rating/income/skill setters remain out of scope.
