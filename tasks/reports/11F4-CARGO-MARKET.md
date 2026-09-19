# 11F.4 — Cargo Market

## Legacy source and contract

The four handlers in `FormMethodsCargoMarkerTab.cs.cs` operate on the real,
non-excluded companies returned for the selected city. A company is excluded
by the legacy `City.ExcludeCompany` rule when it has zero `job_offer` entries.
Company identity is the SII identifier
`company.volatile.<company_type>.<city>`.

`Randomize Cargo list` creates exactly ten values using
`(uint)economy.game_time + (uint)RandomValue.Next(180, 1800)`. The Python API
injects a compatible bounded random source for deterministic tests. The
operation preserves the current seed count (the 1.61 fixtures have ten).
`Reset Cargo list` assigns an empty `uint[]`; it does not write zero values.
The city handlers apply the same operation to every non-excluded company in
the selected city. No `job_offer`, `job_offer_data`, or economy field is
changed.

## Implementation

`src/tsse/application/cargo_market.py` provides typed company identity and
resolver helpers plus transactional `randomize_company`, `reset_company`,
`randomize_city`, and `reset_city`. All target company blocks and seed
collections are validated before source replacement. Malformed collections,
missing cities/companies, missing `economy.game_time`, excluded companies, and
invalid random offsets raise `CargoMarketError` without partial mutation.

## Compatibility

ATS 1.61 and ETS2 1.61 were decrypted through the existing adapter with a
project-local temporary root. A real company operation and a multi-company
city randomize/reset operation were performed on AST copies, serialized to
temporary SiiN, reparsed, and the original game.sii SHA-256 remained equal.

## Tests

`tests/unit/test_cargo_market.py`: four tests covering company/city operations,
game-time arithmetic, exclusion, reset-empty semantics, preservation,
malformed input, and transactional rollback. The 11F.2/11F.3 garage subset
also passed (16 tests total).
