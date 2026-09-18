# Legacy Feature Matrix — TS SE Tool 0.3.11.0

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
| ScsC decrypt/decode | `MethodsDecodeSave` | P/Invoke `DecryptAndDecodeMemory` | `ScsC` | none | typed-error test | NÃO IMPLEMENTADO |
| BSII decode | `MethodsDecodeSave` | `DecodeMemory` | binary SII | none | none | NÃO IMPLEMENTADO |
| 3nK decode | `MethodsDecodeSave` | `DecodeMemory` | `3nK` | detection only | `test_sii_decoder` | PARCIAL |
| Decoder error/result handling | `MethodsDecodeSave` | format switch/result codes | all | typed exceptions | `test_sii_decoder` | PARCIAL |
| Lossless SII parse/order/unknown fields | `SiiNunit`, `Unidentified` | parse/print | all blocks | `SiiDocument` | parser golden tests | PARCIAL |
| Typed SII domain graph/references | `Items/*`, `SiiNunit` | parse/link | player/economy/etc. | small views only | editor tests | PARCIAL |
| `profile.sii` read/write | `SaveFileProfileData` | parse/print | identity, cached XP | none | none | NÃO IMPLEMENTADO |
| `info.sii` read/write | `SaveFileInfoData` | parse/print | info XP/money | none | none | NÃO IMPLEMENTADO |
| Safe staged atomic save write | `MethodsReadWrite` | `NewWrireSaveFile` | `game.sii` | none | none | NÃO IMPLEMENTADO |
| Backup/archive policy | Profile editor, `ZipDataUtilitiescs` | backup/ZIP | profile/save files | clone staging only | clone test | PARCIAL |
| Profile rename | `FormProfileEditorRenameClone` | rename | profile identity | none | none | NÃO IMPLEMENTADO |
| Single/multi/full profile clone | same | clone/multiclone | profile/save assets | `ProfileCloner` | integration clone test | PARCIAL |
| Profile import/export settings | `FormProfileEditorSettingsImportExport` | import/export | profile settings | none | none | NÃO IMPLEMENTADO |
| Player name/company/gender | `FormMethodsProfileTab` | profile controls | `player_name`, `company_name`, `male` | none | none | NÃO IMPLEMENTADO |
| Player XP | profile tab / `Economy` | XP controls | `experience_points` | `set_experience` | player editor test | IMPLEMENTADO |
| Player level → XP | profile tab / `Economy` | `setPlayerExp` | `experience_points` | none | none | PARCIAL |
| Player skills | profile tab / `Economy` | skill handlers | adr/distance/heavy/fragile/urgent/mechanical | `set_skill` | player editor test | IMPLEMENTADO |
| Player visited cities/dealers/agencies | profile/company tabs | fill/unlock controls | city/dealer arrays | none | none | NÃO IMPLEMENTADO |
| Company name/HQ | company tab | company/HQ handlers | player company/HQ | none | none | NÃO IMPLEMENTADO |
| Company money | company tab / `Bank` | money validation | `money_account` | `set_money` | player editor test | IMPLEMENTADO |
| Company drivers | company tab | driver controls | driver blocks | none | none | NÃO IMPLEMENTADO |
| Garage status | company tab / `Garage` | upgrade/downgrade/sell | `status` | `set_garage_status` | garage editor test | PARCIAL |
| Garage contents relocation | `FormGaragesSoldContent` | move drivers/trucks | garage arrays | none | none | NÃO IMPLEMENTADO |
| Truck selection/details | truck tab / `Vehicle` | fill controls | vehicle/accessories | `Truck` lookup | truck editor test | PARCIAL |
| Truck fuel/condition | truck tab / `Vehicle` | repair/fill controls | wear/fuel fields | `set_condition` | truck editor test | PARCIAL |
| Truck components/accessories/colors/plates | truck tab / `Vehicle` | component/color controls | accessories/plate | none | none | NÃO IMPLEMENTADO |
| Trailer selection/details | trailer tab / `Trailer` | fill controls | trailer/accessories | `Trailer` lookup | trailer editor test | PARCIAL |
| Trailer repair | trailer tab / `Trailer` | repair controls | cargo/body/chassis/wheels wear | `repair_trailer` partial | trailer editor test | PARCIAL |
| Trailer components/plate/odometer | trailer tab / `Trailer` | controls | accessories/plate/odometer | none | none | NÃO IMPLEMENTADO |
| Freight market list/job editing | freight tab | fill/randomize/reset | job offers/economy | none | none | NÃO IMPLEMENTADO |
| Cargo market seed controls | cargo tab | randomize/reset/print | cargo seeds | none | none | NÃO IMPLEMENTADO |
| Convoy save positioning/export | convoy tab/dialog | save/move/export/import | saves/preview | none | none | NÃO IMPLEMENTADO |
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
