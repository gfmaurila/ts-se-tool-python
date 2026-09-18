# Profile discovery

Task 02 implements read-only discovery under the conventional Documents roots:
`American Truck Simulator` and `Euro Truck Simulator 2`. A valid profile must
contain `profile.sii`; a valid save slot must contain `game.sii` below its
`save` directory. Both `profiles` and `steam_profiles` are supported.

`DiscoverySettings.custom_game_folders` accepts a game-root override per game.
It is intentionally explicit: no registry or Steam-library scanning is done at
this stage. `installation_folders` is diagnostic configuration only and is not
required to find Documents profiles.

## Cloning constraint

Profile cloning copies the complete source directory through a sibling staging
directory and only then publishes a new destination. The source is never
opened for writing. Directory identity is independent immediately; internal
profile-name/identity mutation is deferred because the available real
`profile.sii` fixtures are opaque `ScsC` containers.
