# Task 11H - Legacy parity gap review and implementation plan

Timestamp: 2026-09-18T20:29:37-03:00

## Audit basis and status

Primary evidence was read from `reference/TS.SE.Tool.vs.0.3.11.0`; the current
classification is the authoritative post-11F/11G consolidation in
`tasks/reports/LEGACY-PARITY-AUDIT.md`: **44 total; 19 IMPLEMENTADO; 16
PARCIAL; 8 NAO IMPLEMENTADO; 1 N/A**. The large table in
`docs/LEGACY-FEATURE-MATRIX.md` explicitly predates 11D-11G, so its historical
cells were not reclassified in this audit. No factual status correction was
needed to the authoritative totals.

Gap types: **A** backend missing; **B** GUI integration only; **C** backend
partial plus GUI; **D** legacy feature not applicable; **E** requires game
1.61 validation. Counts: A=4, B=5, C=14, D=0, E=1.

| ID | Feature | Current | Legacy evidence | Python backend / GUI | Gap type | Missing work | Proposed task | Dependency |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| P01 | Application bootstrap / exception UI | PARCIAL | `Program.cs`, `FormMain.cs` startup and splash/error flow | `desktop.main.main`; minimal window only | B | startup exception/status/splash parity | 11H.7 | stable GUI shell |
| P02 | ATS/ETS game selection | PARCIAL | `Forms/FormMainControlsMethods.cs:211-303`, `ToggleGame` | game combo in `desktop.main` | B | refresh/error/state transitions | 11H.7 | discovery |
| P03 | Documents/custom folder discovery | PARCIAL | `Forms/FormAddCustomFolder.cs`, add/edit/save custom paths | `DiscoverySettings`, `GameRootStore`, basic settings dialog | C | legacy custom-path collection semantics and richer UI | 11H.6 | discovery models |
| P04 | Steam profile discovery | PARCIAL | `FormMethods` profile refresh flow | `ProfileDiscovery` supports `steam_profiles`; GUI lists IDs | B | display decoded name, refresh/status actions | 11H.6 | P03 |
| P05 | Profile/save selection | PARCIAL | `FormMainControlsMethods.cs:258-303,593-972` | `ProfileDiscovery`, profile/save combos | B | selected-save load state, errors, commands | 11H.6 | SaveEditService |
| P06 | 3nK decode | PARCIAL | `MethodsDecodeSave.NewDecodeFile` handles opaque formats | adapter path can receive 3nK; no local fixture | E | legal fixture and controlled decode/parse validation | 11H.5 | SiiDecoder |
| P07 | Decoder error/result handling | PARCIAL | `NewDecodeFile` maps result failures to UI status | typed decoder errors; no GUI presentation | C | normalized application diagnostics and GUI error mapping | 11H.5, 11H.7 | SiiDecoder |
| P08 | Lossless SII parse/order/unknown fields | PARCIAL | `SiiNunit` / unidentified-item print flow | conservative `SiiDocument` parser | A | broader grammar/value and unknown-block fidelity evidence | 11H.1 | parser fixtures |
| P09 | Typed SII domain graph/references | PARCIAL | `CustomClasses/Save/Items/*`, `DataManipulation.cs` linking | targeted views/editors only | A | shared typed resolvers, reference validation, read models | 11H.1 | P08, SiiDocument |
| P10 | `profile.sii` read/write surface | PARCIAL | `SaveFileProfileData.cs`, profile editor | identity rename only; no GUI editor | C | remaining profile fields/read model plus UI | 11H.2, 11H.6 | P09, SafeSaveWriter |
| P11 | Backup/archive policy | PARCIAL | profile editor / `ZipDataUtilitiescs.cs` | `SafeSaveWriter`, `ProfileCloner`, `ProfileSettingsZip` | C | user-visible backup retention/restore policy across profile operations | 11H.2, 11H.6 | SaveEditService |
| P12 | Profile settings import/export | PARCIAL | `FormProfileEditorSettingsImportExport` | `ProfileSettingsZip` is tested; no GUI | B | profile-editor UI and confirmation/error flow | 11H.6 | ProfileSettingsZip |
| P13 | Truck selection/details | PARCIAL | `MainTabs/FormMethodsTruckTab.cs` select/current/info handlers | `find_truck`, vehicle views, repair/refuel | C | complete selection/detail read model and UI | 11H.3, 11H.8 | P09, SaveEditService |
| P14 | Trailer selection/details | PARCIAL | `MainTabs/FormMethodsTrailerTab.cs.cs:630-785` | `find_trailer`, views, repair | C | complete selection/detail read model and UI | 11H.3, 11H.8 | P09, SaveEditService |
| P15 | Trailer components/plate/odometer | PARCIAL | trailer tab detail handlers | read-only vehicle/trailer views | C | proven setters where legacy has them, then UI; retain read-only where no setter exists | 11H.3, 11H.8 | P09 |
| P16 | Program/game settings | PARCIAL | `ProgSettings.cs`, `FormProgramSettings`, `FormSettings` | QSettings game roots only | C | typed settings model/migration and settings UI | 11H.6 | P03 |
| N01 | `info.sii` read/write | NAO IMPLEMENTADO | `SaveFileInfoData.cs`; convoy reads it | no typed info model/editor | A | parse/edit model and safe persistence contract | 11H.2 | P08, SafeSaveWriter |
| N02 | Company driver management | NAO IMPLEMENTADO | `FormMethodsCompanyTab.cs`, driver controls; `DataManipulation` | `resolve_driver` is read-only resolution | C | proven driver mutations/read model and UI | 11H.4, 11H.7 | P09, SaveEditService |
| N03 | Truck components/accessories/colors/plates | NAO IMPLEMENTADO | `FormMethodsTruckTab.cs` component/paint handlers | repair/refuel and read-only accessory views | A | field-level mutation evidence and safe editor | 11H.3 | P09, SaveEditService |
| N04 | Convoy save positioning/export | NAO IMPLEMENTADO | `FormConvoyControlPositions.cs:295-754`; `FormMethodsConvoyToolsTab` | no convoy backend or UI | C | save-position model, export/import, controlled validation, UI | 11H.4, 11H.8 | P08, N01, SaveEditService |
| N05 | User/shared colors | NAO IMPLEMENTADO | `FormColorPicker.cs`; `FormShareUserColors.cs:352-460`; profile tab | no color persistence/import backend or GUI | C | file format and persistence contract, picker/share UI | 11H.9 | P10 |
| N06 | DDS/TGA preview rendering | NAO IMPLEMENTADO | `DDSImageParser`, `TGASharpLib`, freight/convoy drawing | no decoder/renderer or GUI | C | licensed image decode boundary and PySide renderer | 11H.9 | asset fixtures |
| N07 | Localization | NAO IMPLEMENTADO | `FormMainControlsMethods.cs:83-100`, language files | no resource layer or GUI language switching | C | catalog loader/fallback and UI binding | 11H.9 | GUI shell |
| N08 | Update/about/help links | NAO IMPLEMENTADO | `FormCheckUpdates.cs`, `FormAboutBox.cs`, menu handlers | no app service or GUI | C | policy-safe about/help/update-check design and UI | 11H.9 | GUI shell, network policy |

## GUI ready backends

- Game/profile/save discovery: `ProfileDiscovery`, `DiscoverySettings`,
  `GameRootStore`.
- Profile clone, rename, and settings ZIP: `ProfileCloner`,
  `ProfileIdentityEditor`, `ProfileSettingsZip`.
- Safe write, restore, and backup listing: `SaveEditService` and
  `SafeSaveWriter`.
- Player/company operations already proven: experience, skills, gender,
  company name, HQ, money, visits, dealer/recruitment unlocks.
- Garage relocation/sale; Cargo Market randomize/reset; Freight Market writer.
- Truck/trailer repair/refuel and read-only vehicle/trailer projections.

## GUI blocked by backend

- Full profile/info model and retention policy (P10/P11/N01).
- Shared typed graph and parser grammar coverage (P08/P09).
- Company-driver mutations, truck component writes, and convoy positioning
  (N02-N04).
- User colors persistence, DDS/TGA rendering, localization, update/help
  policy (N05-N08).
- 3nK compatibility requires a real legal fixture before it is exposed for
  production use (P06).

## Proposed sequence

1. **11H.1 - SII grammar and typed reference foundation:** close P08/P09 with
   fixture-led parser/domain evidence; reusable by all editors.
2. **11H.2 - Profile and info safe I/O:** P10/P11/N01 using
   `SafeSaveWriter`/`SaveEditService`; no GUI.
3. **11H.3 - Vehicle/trailer component parity:** P13-P15/N03, reuse current
   editors/views and `SaveEditService`.
4. **11H.4 - Company drivers and convoy backend:** N02/N04, after 11H.1/2.
5. **11H.5 - Game version compatibility and decoder diagnostics:** P06/P07;
   read-only version detection, validation registry, controlled-fixture plan.
6. **11H.6 - Profile, discovery, settings, and backup GUI:** P03-P05/P10-P12/P16.
7. **11H.7 - Main/player/company/garage/market GUI:** P01/P02/P07/N02, only
   for operations with completed backend contracts.
8. **11H.8 - Vehicle/trailer/convoy GUI:** P13-P15/N04 after 11H.3/4.
9. **11H.9 - Colors, previews, localization, help/update:** N05-N08; isolate
   external asset/network decisions and complete after core editing.

## Game version compatibility - planned in 11H.5

No implementation in this audit. The future service must detect game/save
version where reliable evidence exists, record ATS 1.61 and ETS2 1.61 as
`VALIDATED`, mark 1.62 and future versions `UNVALIDATED` by default, prevent
assumption of write safety, and define controlled validation using copies/QA
profiles. It must not modify saves merely to identify versions.

## Validation and safety

No production source was modified. No QA or real save was read or changed; no
game process was launched. Current-state gates: pytest 129 passed, 0 failed,
0 skipped; Ruff PASS; mypy PASS. Coverage remains the last implementation gate
measurement, 83.03% from Task 11G.3.
