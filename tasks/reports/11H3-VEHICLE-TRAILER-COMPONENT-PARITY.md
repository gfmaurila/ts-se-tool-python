# 11H.3 — Vehicle/trailer component parity

## Legacy evidence

`CustomClasses/Save/Items/Vehicle.cs` parses vehicle wear, indexed wheel wear,
accessories, fuel, plate and odometer. `FormMethodsTruckTab.cs` implements
`buttonTruckRepair_Click`, `buttonElRepair_Click` and
`buttonTruckReFuel_Click`: their only proven persistent component writes set
wear to zero or `fuel_relative` to one. Paint copy/paste operates legacy
`PartData`; no C# conversion from that data to a paint accessory SII unit was
located.

`Trailer.cs` parses cargo/body/chassis/wheel wear, accessories, plate,
odometer and `slave_trailer`. `FormMethodsTrailerTab.cs.cs` implements total
and individual repair by looping the slave chain; both now have matching Python
behavior.

## Implementation

- Added immutable relationship helpers in `core.saves.vehicle_graph` over
  `SiiGraph`: assigned truck/trailer, typed vehicle/trailer lookup, typed
  accessory resolution and slave-chain traversal. Missing, malformed and wrong
  type references fail with `VehicleGraphError`; explicit null remains valid.
- Views now inspect indexed accessories through this graph without mutation.
- Trailer individual repair now repairs every linked slave, matching the actual
  legacy handler. Existing truck repair/refuel and total trailer repair were
  retained.
- No accessory IDs, paint vectors, plates, odometers, configurations or trailer
  fuel were invented or written. Unknown fields, unknown blocks and unrelated
  accessory references remain lossless because mutations replace only proven
  wear/fuel fields through the existing AST serializer.

## Fixtures and persistence

ATS 1.61: vehicle units and repairable truck fields were observed; assigned
truck/trailer are explicit null and standalone trailer is not observed. A truck
engine repair passed decrypt/parse, reparse and `SaveEditService` copied-save
backup/staging/atomic-write validation.

ETS2 1.61: vehicle and trailer units were observed; assignments are explicit
null. Truck engine and trailer body/cargo repairs passed serialize/reparse; the
trailer cargo repair also passed `SaveEditService` on a copied save. Fixture
sources were unchanged.

## Validation and limitations

New unit tests cover assignment, indexed accessories, null/missing/wrong/
malformed references, side-effect freedom and slave traversal. Component
fixture integrations cover ATS/ETS truck and ETS trailer writes. The complete
suite is 150 tests: 136 unit, 9 existing integrations and 5 component
integrations; all passed when run in short, non-overlapping pytest basetemps.
Ruff and mypy pass. Coverage remains above the configured 80% gate (the
consolidated run measured 83.08% before the final short-path clone rerun).

Remaining work is GUI selection/detail wiring, semantic paint/color work
(11H.9), and the unrelated company-driver/convoy backend (11H.4).
