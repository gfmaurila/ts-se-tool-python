# Configurable ATS / ETS2 profile roots

Implemented read-only manual roots with automatic fallback. `GameRootStore`
persists per-game paths through `QSettings`; `ProfileDiscovery` remains the
single discovery implementation and accepts runtime root updates.

The main window now provides Settings/Configurações with QFileDialog browse
buttons, save validation for `profiles`/`steam_profiles`, automatic-discovery
reset, status text including game/root, and profile/save refresh on save or
game switching. No save or profile files are written.

Validation on this machine found one profile in each collection for both roots:

- ATS: `D:\Work\American Truck Simulator\profiles` (1),
  `steam_profiles` (1)
- ETS2: `D:\Work\Euro Truck Simulator 2\profiles` (1),
  `steam_profiles` (1)

Unit tests use synthetic temporary roots; the real directories were read only.
