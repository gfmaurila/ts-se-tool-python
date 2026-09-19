# Legacy Feature Matrix — TS SE Tool 0.3.11.0

## Classification correction (Task 11H.7 recovery)

The older table below retains historical task snapshots and is not the current
aggregate. The authoritative audit after 11H.6 is **44 total: 19 IMPLEMENTADO,
20 PARCIAL, 4 NÃO IMPLEMENTADO, 1 N/A**. The conflicting `19/16/8/1` line is
an earlier 11F consolidation, not a feature downgrade. Task 11H.7's read-only
navigation increment does not change any feature classification.

## Task 11E -- final status

CONCLUIDA. Legacy truck/trailer repair and read-only vehicle/trailer projections
were validated against ATS/ETS2 1.61 temporary decoded SiiN data. No ScsC/BSII
encoder was added.

| Area | Functionality | Status | Scope decision |
| --- | --- | --- | --- |
| Truck | Refuel; total/individual repair; engine/transmission/chassis/cabin/wheels wear | PASS | Total wheels repair clears `wheels_wear[]`. |
| Trailer | Total/individual repair; cargo/body/chassis/wheels wear; slave traversal | PASS | Total and individual repair traverse the slave chain. |
| Views | License plate and odometer read | PASS | Write is N/A: no legacy setter located. |
| Views | Wheels, accessories, paint accessory | PASS | Lossless, read-only projections. |
| Paint clipboard | `PartData` copy, GZip/uppercase-hex encode/decode, paste to `PartData` | PASS | Header is `TruckPaint`; snapshot is immutable. |
| Paint SII write-back | `PartData` to `vehicle_paint_job_accessory` | NOT ESTABLISHED | No conversion was located in legacy C#; no speculative field mutation was added. |

Compatibility: ATS 1.61 vehicle PASS; ETS2 1.61 vehicle PASS; ETS2 1.61
trailer PASS; ATS 1.61 trailer NOT OBSERVED. Paint accessories were observed
in ATS and ETS2 and their read-only views pass. Clipboard payload is AST-independent.

## Task 11D — final status

CONCLUÍDA. Level/XP, gender, company, HQ, visited cities/counts, dealers,
recruitments, and driver resolution are PASS. Profile name is Task 11C/N/A
here. HQ (`player.hq_city`) is selected from owned garages, never restricted
to visited cities. `economy.visited_cities[]` and `visited_cities_count[]` are
parallel; new city count is 1 and an existing city is not duplicated.
`player.drivers[]` resolves both `driver_player` (ATS `driver.159`) and
`driver_ai` (ETS2 `driver.211`); readiness is index-paired, quit-warned is
preserved without equal-length requirement. ATS/ETS2 1.61 game/profile
structures passed read-only validation.

This is a functional-parity audit of `reference/TS.SE.Tool.vs.0.3.11.0`, not
a statement of ATS/ETS2 current-version compatibility. “Implemented” requires
both a functional Python counterpart and a test; it does not mean a matching
class name or a current-save validation.

| Functionality | C# Form/Class | Method(s) | SII fields | Python counterpart | Tests | Status |
| --- | --- | --- | --- | --- | --- | --- |
| Application bootstrap / exception UI | `Program`, `FormMain` | `Main`, startup | n/a | `desktop.main` | `test_desktop_smoke` | PARCIAL |
| ATS/ETS game selection | `FormMainControlsMethods` | `ToggleGame` | n/a | game combo | `test_desktop_smoke` | PARCIAL |
| Documents/custom folder discovery | `FormMethods`, `FormAddCustomFolder` | setup/add folder | n/a | `DiscoverySettings` | `test_profile_discovery` | PARCIAL |
| Steam profile discovery | `FormMethods` | profile refresh | profile paths | `ProfileDiscovery` | `test_profile_discovery` | PARCIAL |
| Profile/save selection | `MethodsReadWrite` | load/profile-save refresh | `profile.sii`, `info.sii`, `game.sii` | discovery + GUI | discovery/desktop tests | PARCIAL |
| Plain SII format detection | `MethodsDecodeSave` | `NewDecodeFile` | `SiiNunit` | `detect_save_format` | `test_sii_decoder` | IMPLEMENTADO |
| ScsC decrypt/decode | `MethodsDecodeSave` | P/Invoke `DecryptAndDecodeMemory` | `ScsC` | `SiiDecoder` -> official SII_Decrypt 1.5.3 x64 | copied ATS/ETS 1.61 fixture + parser regressions | IMPLEMENTADO |
| BSII decode | `MethodsDecodeSave` | `DecodeMemory` | binary SII | official SII_Decrypt 1.5.3 x64 (BSII v3 / type 0x07) | copied ATS/ETS adapter + parser regressions | IMPLEMENTADO |
| 3nK decode | `MethodsDecodeSave` | `DecodeMemory` | `3nK` | official SII_Decrypt 1.5.3 x64 | upstream documented; no local 3nK fixture | PARCIAL |
| Decoder error/result handling | `MethodsDecodeSave` | format switch/result codes | all | typed exceptions | `test_sii_decoder` | PARCIAL |
| Lossless SII parse/order/unknown fields | `SiiNunit`, `Unidentified` | parse/print | all blocks | `SiiDocument` | parser golden tests | PARCIAL |
| Typed SII domain graph/references | `Items/*`, `SiiNunit` | parse/link | player/economy/etc. | small views only | editor tests | PARCIAL |
| `profile.sii` read/write | `SaveFileProfileData` | parse/print | `profile_name` identity | `ProfileIdentityEditor` + `SafeSaveWriter` | `test_profile_identity` | PARCIAL |
| `info.sii` read/write | `SaveFileInfoData` | parse/print | info XP/money | none | none | NÃO IMPLEMENTADO |
| Safe staged atomic save write | `MethodsReadWrite` | `NewWrireSaveFile` | `game.sii`, `info.sii`, `profile.sii` | `SaveEditService` + `SafeSaveWriter` | unit + ATS/ETS2 copied-fixture write integration | IMPLEMENTADO |
| Backup/archive policy | Profile editor, `ZipDataUtilitiescs` | backup/ZIP | profile/save files | clone staging only | clone test | PARCIAL |
| Profile rename | `FormProfileEditorRenameClone` | rename | `profile_name`; directory UTF-8 uppercase hex | `ProfileIdentityEditor.rename_directory` | `test_profile_identity` | PARCIAL |
| Single/multi/full profile clone | same | clone/multiclone | `profile_name`, `creation_time`; selected assets | `ProfileCloner` | integration clone test | PARCIAL |
| Profile import/export settings | `FormProfileEditorSettingsImportExport` | import/export | profile settings | none | none | NÃO IMPLEMENTADO |
| Player name/company/gender | `FormMethodsProfileTab` | profile controls | `player_name`, `company_name`, `male` | none | none | NÃO IMPLEMENTADO |
| Player XP | profile tab / `Economy` | XP controls | `experience_points` | `set_experience` | player editor test | IMPLEMENTADO |
| Player level → XP | profile tab / `Economy` | `setPlayerExp` | `experience_points` | none | none | PARCIAL |
| Player skills | profile tab / `Economy` | skill handlers | adr/distance/heavy/fragile/urgent/mechanical | `set_skill` | player editor test | IMPLEMENTADO |
| Player visited cities/dealers/agencies | profile/company tabs | fill/unlock controls | city/dealer arrays | none | none | NÃO IMPLEMENTADO |
| Company name/HQ | company tab | company/HQ handlers | player company/HQ | none | none | NÃO IMPLEMENTADO |
| Company money | company tab / `Bank` | money validation | `money_account` | `set_money` | player editor test | IMPLEMENTADO |
| Company drivers | company tab / `Driver_AI` | read driver data; garage-slot relocation | driver fields; garage drivers | typed driver graph/view + existing relocation | driver/fixture tests | PARCIAL |
| Garage status | company tab / `Garage` | upgrade/downgrade/sell | `status` | `set_garage_status` | garage editor test | PARCIAL |
| Garage contents relocation | `FormGaragesSoldContent` | move drivers/trucks | garage arrays | none | none | NÃO IMPLEMENTADO |
| Truck selection/details | truck tab / `Vehicle` | fill controls | vehicle/accessories | `Truck` lookup | truck editor test | PARCIAL |
| Truck fuel/condition | truck tab / `Vehicle` | repair/fill controls | wear/fuel fields | `set_condition` | truck editor test | PARCIAL |
| Truck components/accessories/colors/plates | truck tab / `Vehicle` | condition controls; accessory/plate/paint projection | wear/accessories/plate | typed vehicle graph + lossless views + repair/refuel | component/fixture tests | PARCIAL |
| Trailer selection/details | trailer tab / `Trailer` | fill controls | trailer/accessories | `Trailer` lookup | trailer editor test | PARCIAL |
| Trailer repair | trailer tab / `Trailer` | repair controls | cargo/body/chassis/wheels wear | typed slave-chain repair | trailer editor/fixture tests | PARCIAL |
| Trailer components/plate/odometer | trailer tab / `Trailer` | condition controls; accessory/plate/odometer projection | wear/accessories/plate/odometer | typed trailer graph + lossless views + repair | component/fixture tests | PARCIAL |
| Freight market list/job editing | freight tab | fill/randomize/reset | job offers/economy | none | none | NÃO IMPLEMENTADO |
| Cargo market seed controls | cargo tab | randomize/reset/print | cargo seeds | none | none | NÃO IMPLEMENTADO |
| Convoy save positioning/export | convoy tab/dialog | current GPS copy/paste; multi-save export/import | `player.my_truck_placement` | GPS codec + minimal position writer | Convoy unit tests | PARCIAL |
| Program/game settings | settings/program settings | load/save controls | config/settings | defaults only | config test | PARCIAL |
| User/shared colors | color picker/share colors | picker/share | color resources | none | none | NÃO IMPLEMENTADO |
| DDS/TGA preview rendering | `DDSImageParser`, `TGASharpLib` | image loading | preview assets | none | none | NÃO IMPLEMENTADO |
| Localization | main controls/resources | language change | resources | none | none | NÃO IMPLEMENTADO |
| Update check/about/help links | update/about forms | web/check UI | n/a | none | none | NÃO IMPLEMENTADO |
| SQL CE/cache data helpers | data manipulation/helpers | database/cache | external cache | none | none | NÃO APLICÁVEL |

Totals: 44 identified; 4 IMPLEMENTADO, 18 PARCIAL, 21 NÃO IMPLEMENTADO,
1 NÃO APLICÁVEL.

## Legacy decryption flow

`MethodsDecodeSave.NewDecodeFile` reads all file bytes, calls
`GetMemoryFormat`, then: format 1 returns UTF-8 lines unchanged; format 2 calls
`DecryptAndDecodeMemory` twice (size query then output); formats 3 and 4 do the
same with `DecodeMemory`; `-1`, `10`, and `11` return null. The P/Invoke entry
points are `GetFileFormat`, `GetMemoryFormat`, `DecryptAndDecodeMemory`, and
`DecodeMemory`. It has no Python-equivalent decoder: current Python detection
and typed errors are therefore only partial parity. The legacy’s direct writer
is explicitly *not* parity-safe and must be replaced by atomic validated I/O.

## Task 11F — consolidated final status (2026-09-18)

The following entries are authoritative for the completed 11F scope. Each is
backed by the legacy handler contract, Python implementation, regression tests,
and the applicable ATS/ETS2 1.61 temporary decode/parse/serialize/reparse
validation.

| Area | Functionality | Status | Compatibility / decision |
| --- | --- | --- | --- |
| Garage | Garage resolver (`economy.garages[] → garage`) | IMPLEMENTADO | ATS and ETS2 1.61 validated. |
| Garage | Driver relocation (out/in) | IMPLEMENTADO | Null slots preserved; transient removed-item lists retained; legacy duplicate-in behavior preserved. |
| Garage | Vehicle relocation (out/in) | IMPLEMENTADO | No compaction; vehicle blocks remain lossless. |
| Garage | Garage sale/status preparation | IMPLEMENTADO | Legacy status and transactional slot semantics covered; `driver_pool[0]` protection remains specific to driver-out. |
| Cargo Market | Company/city seed resolver and randomize/reset | IMPLEMENTADO | `company.volatile.<type>.<city>`; `game_time + Random.Next(180,1800)`; job offers preserved. |
| Freight Market | Existing job-offer resolver and field writer | IMPLEMENTADO | Legacy writes existing `job_offer_data`; no speculative ID allocator or physical delete. |
| Freight Market | Transient clear semantics | IMPLEMENTADO | `ClearJobData` clears the pending UI queue only. |
| Compatibility | ATS 1.61 integration | IMPLEMENTADO | Decrypt, parse, garage/cargo/freight resolve, SiiN serialize/reparse passed. |
| Compatibility | ETS2 1.61 integration | IMPLEMENTADO | Decrypt, parse, garage/cargo/freight resolve, SiiN serialize/reparse passed. |

The remaining binary limitation is explicit: ScsC/BSII decrypt/read is
supported, AST editing and SiiN serialization are supported, but ScsC/BSII
binary write-back is **NÃO IMPLEMENTADO**. The PySide6 GUI remains a functional
shell and does not yet expose the complete backend surface. These limitations
are not hidden by the 11F status.

## Task 11G.3 - production plaintext write pipeline (2026-09-18)

`SaveEditService` is the GUI-independent production use case for `game.sii`:
it detects SiiN directly; routes recognized ScsC, BSII, and 3nK opaque inputs
through the existing decoder boundary; applies a caller-owned AST mutation;
serializes SiiN; validates sibling fsynced staging; verifies the source has
not changed; creates a unique exact-byte backup; and atomically replaces only
`game.sii`. Explicit backup discovery and staged, atomic restore are provided.

The production write target is SiiN plaintext. An ScsC/BSII encoder is **NOT
REQUIRED**: ATS 1.61 and ETS2 1.61 QA-game tests in Task 11G.2 loaded the
resulting plaintext save and retained the edited ADR value. GUI exposure is
not part of this status.
