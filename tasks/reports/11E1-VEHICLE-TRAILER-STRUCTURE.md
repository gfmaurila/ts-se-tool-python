# Task 11E.1 — Vehicle/trailer structural inspection

Read-only inspection of the supplied ATS/ETS2 1.61 `game.sii` fixtures was
performed through `SiiDecoder` (SII_Decrypt 1.5.3) and `parse_sii`. The
decoder receives private temporary copies only. Original fixture bytes were
compared before and after each inspection and remained unchanged.

## Legacy contract

The legacy truck tab (`FormMethodsTruckTab.cs`) sets `fuel_relative` to `1`
when refuelling. Total repair zeros `engine_wear`, `transmission_wear`,
`chassis_wear`, and `cabin_wear`, and replaces `wheels_wear` with an empty
list. Its per-component action zeros one of those four fields or clears the
wheel list. The trailer tab (`FormMethodsTrailerTab.cs.cs`) analogously zeros
`cargo_damage`, `trailer_body_wear`, and `chassis_wear`, or clears
`wheels_wear`; it repeats the action through `slave_trailer` links.

`Vehicle.cs` and `Trailer.cs` define the condition, accessory, license plate,
and odometer fields listed below. `SCSLicensePlate.cs` consumes the legacy
plate string format (plate and country separated by `|`) for display. No C#
setter for plate or odometer was located in these tabs.

Truck paint sharing copies the complete `PartData` of the `paintjob` part,
prefixed with `TruckPaint` and compressed through `ZipDataUtilities`. The
typed `Vehicle_Paint_job_Accessory` representation contains the six colour
fields plus `data_path` and `refund`; these are the legacy fields preserved by
its `PrintOut`.

## ATS 1.61

Decoded document: 17,672 blocks. It contains 14 `vehicle`, 98
`vehicle_accessory`, 198 `vehicle_wheel_accessory`, and 14
`vehicle_paint_job_accessory` blocks. No `trailer` block occurs in this
fixture; this is **NOT OBSERVED**, not an incompatibility finding.

Representative vehicle: `vehicle : _nameless.1c5.f43f.e5e8`.

| Field | Observation |
| --- | --- |
| `engine_wear` | present; encoded float token `&3b42d9ea` |
| `transmission_wear` | present; encoded float token `&3b42d9ea` |
| `chassis_wear` | present; encoded float token `&3cc1459f` |
| `cabin_wear` | present; encoded float token `&3c9a9e19` |
| `fuel_relative` | present; encoded float token `&3eb5228b` |
| `wheels_wear[]` | indexed array, 3 entries: `&3bd5636b`, `&3bd5636b`, `&3bd5636b` |
| `accessories[]` | indexed reference array, 41 entries; all resolved |
| `license_plate` | present: `"R63-6872|texas"` |
| `odometer` | present decimal unsigned-looking integer: `15473` |
| `odometer_float_part` | present encoded float token: `&3e487a09` |

The representative accessory graph resolves to 7 `vehicle_accessory`, 12
`vehicle_wheel_accessory`, 21 `vehicle_addon_accessory`, and 1
`vehicle_paint_job_accessory` blocks; no unresolved reference was observed.
The wheel-wear array has 3 values but the graph has 12 wheel accessory blocks,
so no one-to-one index relationship is evidenced.

Representative paint block: `_nameless.1c6.6abc.5158`.

| Legacy paint field | ATS 1.61 |
| --- | --- |
| `mask_r_color` | `(1, 0, 0)` |
| `mask_g_color` | `(0, 1, 0)` |
| `mask_b_color` | `(0, 0, 1)` |
| `flake_color` | `(0, 1, 0)` |
| `flip_color` | `(1, 0, 0)` |
| `base_color` | `(0, 0, 0)` |
| `data_path` | `"/def/vehicle/truck/peterbilt.389/paint_job/color3.sii"` |
| `refund` | `2900` |

## ETS2 1.61

Decoded document: 43,027 blocks. It contains 393 `vehicle`, 3 `trailer`,
2,760 `vehicle_accessory`, 4,806 `vehicle_wheel_accessory`, and 396
`vehicle_paint_job_accessory` blocks.

Representative vehicle: `vehicle : _nameless.20c.c9bb.0418`.

| Field | Observation |
| --- | --- |
| four vehicle wear fields | all present, decimal `0` |
| `fuel_relative` | present, decimal `1` |
| `wheels_wear[]` | indexed array, 2 entries: `0`, `0` |
| `accessories[]` | indexed reference array, 46 entries; all resolved |
| `license_plate` | present: `"42-CO-61  |portugal"` |
| `odometer` | present decimal unsigned-looking integer: `33875` |
| `odometer_float_part` | present encoded float token: `&3ee89506` |

The representative vehicle resolves to 7 `vehicle_accessory`, 8
`vehicle_wheel_accessory`, 30 `vehicle_addon_accessory`, and 1
`vehicle_paint_job_accessory`; no unresolved reference was observed. Its two
wheel-wear values do not establish an index correspondence with its eight
wheel accessory blocks.

Representative vehicle paint block: `_nameless.20c.c4b4.b158`. The seven
colour/path/refund fields above are present; `base_color` is
`(&3bfc5048, &3bfc5048, &3bfc5048)`, `data_path` is
`"/def/vehicle/truck/daf.2021/paint_job/color0.sii"`, and `refund` is `0`.

Representative trailer: `trailer : _nameless.20c.cdd0.1df8`.

| Field | Observation |
| --- | --- |
| `cargo_damage`, `trailer_body_wear`, `chassis_wear` | present; decimal `0` |
| `wheels_wear[]` | indexed array, 3 entries: `0`, `0`, `0` |
| `accessories[]` | indexed reference array, 23 entries; all resolved |
| `license_plate` | present: `"C-47083  |portugal"` |
| `odometer`, `odometer_float_part` | present; decimal `0`, `0` |
| `slave_trailer` | present: `null` |

Its accessories resolve to 3 `vehicle_accessory`, 12
`vehicle_wheel_accessory`, 7 `vehicle_addon_accessory`, and 1
`vehicle_paint_job_accessory`. The trailer paint block contains the same eight
legacy fields; its `base_color` is `(&3f19999a, &3f19999a, &3f19999a)`,
`data_path` is `"/def/vehicle/trailer_owned/scs.livestock/paint_job/color5.sii"`,
and `refund` is `2600`.

The inspected chain is `_nameless.20c.cdd0.1df8 -> null` (length 1). Across
all three ETS2 trailer blocks there were zero missing slave targets, zero
self-references, and zero observed cycles. **NO CYCLE OBSERVED** does not
prove cycles are impossible.

## ATS/ETS2 comparison

| Structure | ATS 1.61 | ETS2 1.61 | Classification |
| --- | --- | --- | --- |
| `vehicle` / four wear fields | observed, encoded floats | observed, decimal values | SAME fields; DIFFERENT observed encoding |
| `fuel_relative` | encoded float | decimal | SAME field; DIFFERENT observed encoding |
| `wheels_wear[]` | indexed, 3 entries | indexed, 2 entries | SAME representation |
| `accessories[]` | indexed resolved refs | indexed resolved refs | SAME |
| vehicle plate / odometer | present | present | SAME |
| paint accessory | present | present | SAME fields; values differ |
| `trailer` and trailer fields | NOT OBSERVED | present | NOT OBSERVED / present |
| `slave_trailer` | NOT OBSERVED | present and `null` | NOT OBSERVED / present |

## Decisions and unknowns

- **11E.2 truck repair:** ready. The five legacy repair targets and their
  current 1.61 fields are evidenced in both fixtures. Preserve the exact
  textual float representation for untouched fields.
- **11E.3 trailer repair:** ready. ETS2 supplies a compatible trailer and
  `slave_trailer` evidence; synthetic cycle/missing-reference regressions are
  still required because ATS has no trailer sample and no real chain was seen.
- **11E.4 structured views:** ready for read-only views of condition, wheels,
  accessories, plate, and odometer. The parser exposes indexed fields and
  references. Plate/odometer mutation remains out of scope until legacy setter
  evidence exists.
- **11E.5 paint:** structural evidence is sufficient for a focused paint
  implementation investigation: both games contain the legacy fields and
  paint references. Exact replication must still trace legacy `PartData`
  construction and its compressed clipboard payload before mutation is added.
- Wheel-wear count is not evidenced as matching wheel-accessory count; do not
  introduce positional pairing.
