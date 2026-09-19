# Task 11E.2 — Truck repair and refuel parity

## Legacy behavior verified

`FormMethodsTruckTab.cs` provides exactly five truck repair controls:

| Control | Legacy mutation |
| --- | --- |
| total repair | `engine_wear`, `transmission_wear`, `chassis_wear`, and `cabin_wear` become `0`; `wheels_wear` becomes an empty list |
| engine | `engine_wear: 0` |
| transmission | `transmission_wear: 0` |
| chassis | `chassis_wear: 0` |
| cabin | `cabin_wear: 0` |
| tire/wheels | `wheels_wear` becomes an empty list |
| refuel | `fuel_relative: 1` |

The handler identifies the individual component by UI index `0..4`; it has no
per-wheel repair action. Repair does not refuel. Refuel does not repair any
wear field. Neither operation touches `license_plate`, `odometer`,
`odometer_float_part`, or `accessories`.

## Python implementation

`truck_editor.py` now exposes `repair_truck`, `repair_truck_component`,
`refuel_truck`, and the closed `TruckComponent` enum. The implementation
validates the selected vehicle and every target field before producing a new
parsed document. For wheel repair it validates the declared indexed array
before changing its count to `0` and removing its entries. Missing vehicles,
required fields, malformed wheel counts/indexes, and unsupported components
raise `TruckEditError`; the original document is never mutated.

Unrelated fields retain their source text, including license plate, odometer,
accessories, and unknown fields. No component/accessory positional relation
was added.

## ATS/ETS2 1.61 validation

Each supplied ScsC fixture was decoded through SII_Decrypt 1.5.3 using its
private temporary copy, parsed, mutated only in the returned SiiN document,
serialized, and reparsed.

| Fixture | Total repair | Refuel | Reparse | Original |
| --- | --- | --- | --- | --- |
| ATS 1.61 | PASS | PASS | PASS | byte-for-byte unchanged |
| ETS2 1.61 | PASS | PASS | PASS | byte-for-byte unchanged |

ATS encoded-float wear values and ETS2 decimal example values both accept the
legacy repair target `0`; no conversion of untouched values occurs.

## Regression tests

`tests/unit/test_truck_editor.py` covers total repair, all five individual
controls, malformed wheel arrays, invalid components, missing vehicle/field,
refuel isolation, unrelated-field preservation, and serialize/reparse.

Executed:

- `pytest tests/unit/test_truck_editor.py --basetemp=.pytest-tmp-11e2-truck`: 10 passed.
- `pytest tests/unit/test_truck_editor.py tests/unit/test_trailer_editor.py --basetemp=.pytest-tmp-11e2-related`: 11 passed.

The only emitted warning is the pre-existing inaccessible `.pytest_cache`
directory; it does not affect the project-local basetemp or test result.
