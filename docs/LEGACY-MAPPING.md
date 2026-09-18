# Legacy Mapping — TS SE Tool 0.3.11.0

Task 00 completed on 2026-09-17. The C# source is already extracted under
`reference/TS.SE.Tool.vs.0.3.11.0`; the archive beside it is not needed for
normal analysis.

## Entry point and composition

- Entry point: `reference/TS.SE.Tool.vs.0.3.11.0/TS SE Tool/Program.cs:34`.
  It configures WinForms exception handling, detects the environment, then
  starts `FormMain` at line 52.
- Project: `reference/TS.SE.Tool.vs.0.3.11.0/TS SE Tool/TS SE Tool.csproj`:
  .NET Framework 4.7.2 WinExe, assembly `TS SE Tool`.
- `FormMain` is a partial WinForms class spread across `FormMain.cs`,
  `FormMethods.cs`, `MethodsReadWrite.cs`, `MethodsDecodeSave.cs`, and
  `DataManipulation.cs`. This mixes presentation, filesystem access, parsing,
  database/cache work, and save mutation; do not reproduce that coupling.

## Games, profiles, and save paths

- The game roots are set in `FormMethods.cs:138-140` to `Euro Truck Simulator
  2` and `American Truck Simulator`. The legacy defaults to ETS2.
- The legacy declares ETS2 save format 61 at `FormMethods.cs:129`; ATS support
  is incomplete there (`SupportedSavefileVersionATS` is commented out) and the
  displayed tested game version is 1.43.x. It is behavioral reference only,
  not version-compatibility evidence for 1.61+.
- Save loading in `MethodsReadWrite.cs:591-604` selects a profile and save
  directory, then reads `profile.sii`, `info.sii`, and `game.sii`.
- Profile operations live in
  `Forms/ProfileEditor/FormProfileEditor.cs` and
  `Forms/ProfileEditor/FormProfileEditorRenameClone.cs`. The latter supports
  rename, clone, multi-clone, and optional full clone; it searches recursively
  for `profile.sii` (line 431) and recognizes `game.sii`, `info.sii`, and
  `preview.tga` during cloning (line 471).

## SII decoding, parsing, and writing

- `MethodsDecodeSave.cs:27-170` reads bytes then calls the native
  `SII_Decrypt.dll` through P/Invoke (`GetFileFormat`, `GetMemoryFormat`,
  `DecryptAndDecodeMemory`, and `DecodeMemory`). The legacy binary is found at
  `TS SE Tool/SII_Decrypt.dll` and `bin/Debug/SII_Decrypt.dll`; its source and
  license provenance are not included. The Python design must expose an
  optional decoder interface and must not claim encrypted-save support until a
  separately licensed implementation is supplied.
- `SaveFileProfileData.cs:28,387,605-695` parses and regenerates `profile.sii`.
  `SaveFileInfoData.cs:29,57,201-254` does the same for `info.sii`.
- `CustomClasses/Save/Items/SiiNunit.cs:12-460` parses `game.sii` into typed
  block objects; `PrintOut` at line 460 reconstructs output. Unknown block
  text is retained using `Unidentified` (`Items/Unidentified.cs:9-21`) and is
  appended during output (`SiiNunit.cs:900-916`).
- The typed data model is under `CustomClasses/Save/Items/`, including player,
  economy, company, garage, vehicle, trailer, driver, bank, jobs, cargo, and
  map/progress blocks. Scalar encodings are in `CustomClasses/Save/DataFormat/`.

## Data-safety assessment

- Legacy save writing opens `game.sii` directly with `StreamWriter(..., false)`
  in `MethodsReadWrite.cs:965`; it has no atomic replacement, parse validation
  of staged output, or mandatory backup. This is incompatible with the target
  safety contract.
- Rename creates an optional ZIP backup then deletes the old directory
  (`FormProfileEditorRenameClone.cs:316-327`). Clone writes a new profile
  directory, but its writes are also direct.
- The legacy preserves unknown *blocks*, but not necessarily exact original
  ordering/whitespace or unknown fields inside recognized blocks because it
  serializes typed objects. New code must use a lossless document/patch model:
  retain original tokens/blocks and change only explicitly targeted fields.

## UI and feature inventory

Main tabs declared in `FormMain.Designer.cs` are Profile, Company, Truck,
Trailer, Freight Market, Cargo Market, and Convoy Tools. Supporting dialogs
include settings, program settings, color picker, garage-sale content, custom
folder, shared colors, update/about/splash, and profile import/export.

Priority for the Python product:

1. P0 — discover ATS/ETS2 profiles; read plain supported `profile.sii`,
   `info.sii`, and `game.sii`; lossless round-trip; staged atomic write with
   mandatory backup; and independent profile cloning.
2. P1 — typed views/edits for profile identity, player/company/economy,
   garages, trucks/trailers, and explicit compatibility diagnostics.
3. P2 — freight/cargo market, convoy tools, user colors, import/export, and
   legacy auxiliary UI/data caches only when fixtures prove their format.
4. P3 — update checker, external SQL CE cache, DDS/TGA rendering, translation
   tooling, and other non-save features. These must not become dependencies of
   core parsing or writing.

## Legacy dependencies and resources

- Project references include `SharpZipLib 1.3.3`, `System.Data.SqlServerCe`,
  `ErikEJ.SqlCe40`, `OpenPainter.ColorPicker`, and `Salient.Data`; see the
  references section of `TS SE Tool.csproj`.
- Included resources include icons and DDS/TGA handling code. `MethodsReadWrite.cs`
  loads application images; `CustomClasses/UtilitiesExternal/DDSImageParser.cs`
  and `TGASharpLib.cs` are display-oriented, not required for P0.
- `TS SE Tool/README.md` and source headers identify Apache-2.0 for the legacy
  source. Verify every separately supplied native/third-party binary before
  redistribution.

## Architecture decisions for the replacement

- Keep `core` independent of PySide6 and filesystem/decoder implementations.
- Model ATS and ETS2 as game profiles with shared SII mechanics and isolated
  path/version differences.
- Treat the extracted C# project and supplied ATS/ETS2 fixtures as read-only
  reference material. Tests must copy fixtures to a temporary directory.
- Do not port the direct-write or SQL CE design. The save writer must create a
  backup, write a sibling temporary file, parse/validate it, and only then
  replace the target.
