# Task 11H.1 - SII grammar and typed-reference foundation

Timestamp: 2026-09-18T20:38:00-03:00

## Status and legacy evidence

**CONCLUIDA.** No GUI, real profile, QA save, game process, or game
configuration was modified. Legacy evidence is `CustomClasses/Save/Items/
SiiNunit.cs` (unit registry and print), `Player.cs` (`assigned_truck`,
`my_truck`, indexed drivers/trucks), `Economy.cs` (indexed garages/company
collections), `Company.cs` (`job_offer[]`), `Vehicle.cs` and `Trailer.cs`
(`accessories[]`), and `DataManipulation.cs:358-446,670-678` (dictionary lookup
and relationship traversal). The C# model keeps raw unit IDs in strings and
uses indexed property names such as `garages[i]` and `job_offer[i]`.

## Grammar audit

The existing conservative parser already accepts the observed SiiN header,
outer braces, named blocks, scalar fields, arbitrary raw value tokens, and
numeric indexed keys. It stores values verbatim (including quoted/escaped
strings, numeric literals, booleans, `null`, and token-like IDs), preserves
field/block order through original source serialization, retains unknown
blocks as blocks, and retains unknown field values. Both real 1.61 documents
had zero `unparsed_lines`; no new grammar production was evidenced or added.

Known limits remain deliberate: this is not a full semantic type parser;
vector/color/other values stay raw strings, reference syntax is limited to
observed bare unit IDs (`[A-Za-z0-9_.-]+`) or `null`, and duplicate unit IDs are
ambiguous rather than silently resolved.

## Typed references and graph resolver

Added immutable `TypedUnitReference`, `ReferenceResolution`, `ReferenceStatus`,
and `SiiGraph` in `core.sii`.

- Valid reference: target exists and satisfies the optional expected type.
- Null reference: exact `null`, resolves to `None`.
- Missing target: valid-looking ID absent (or duplicate/ambiguous), reported as
  `MISSING_TARGET` / `MissingReferenceTargetError`.
- Wrong type: target exists but does not match expected type, reported as
  `WRONG_TARGET_TYPE` / `WrongReferenceTypeError`.
- Malformed reference: quoted, whitespace-containing, or otherwise unsupported
  scalar, reported as `MALFORMED` / `MalformedReferenceError`.

`SiiGraph` resolves units by ID, builds scalar field references, returns indexed
references in numeric order without compacting gaps, and follows caller-declared
scalar chains. It only reads the immutable `SiiDocument`; tests prove document
serialization is unchanged after inspection/traversal.

## Tests and round trip

Unit regressions cover valid/null/missing/wrong/malformed references, multiple
indexed references, duplicate IDs, chain traversal, escaped strings, numeric,
boolean, token values, unknown field/block preservation, side-effect freedom,
and serialize/reparse structural equivalence. Existing player/truck/trailer,
garage, cargo, and freight suites remain green.

## ATS 1.61 copied fixture

- Decrypt/parse: PASS; 17,672 blocks; zero unparsed block lines.
- Graph/relations: PASS; player, economy, company, garage, vehicle,
  `driver_ai`, and `job_offer_data` observed. `economy.garages[] -> garage` and
  observed `company.job_offer[] -> job_offer_data` resolve.
- Serialize/reparse: PASS; original fixture unchanged.
- Not observed as standalone unit blocks: trailer, cargo, convoy.

## ETS2 1.61 copied fixture

- Decrypt/parse: PASS; 43,027 blocks; zero unparsed block lines.
- Graph/relations: PASS; player, economy, company, garage, vehicle, trailer,
  `driver_ai`, and `job_offer_data` observed. The same garage/job-offer
  relations resolve from blocks that contain those indexed fields.
- Serialize/reparse: PASS; original fixture unchanged.
- Not observed as standalone unit blocks: cargo, convoy.

## Quality gates and remaining limitations

- Full pytest: **135 passed, 0 failed, 0 skipped** with
  `--basetemp=.pytest-tmp-11h1`.
- Coverage: **83.50%** (>=80%).
- Ruff: PASS. mypy: PASS.

The feature matrix and parity-audit totals remain **19 IMPLEMENTADO, 16
PARCIAL, 8 NAO IMPLEMENTADO, 1 N/A**: parser and typed graph are still partial
because their intentionally conservative coverage does not model every legacy
value/relationship. Next: 11H.2 may use `SiiGraph`, `SiiDocument`,
`SafeSaveWriter`, and `SaveEditService` for profile/info safe I/O, but is not
started here.
