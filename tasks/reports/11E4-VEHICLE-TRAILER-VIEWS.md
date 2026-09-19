# Task 11E.4 — Structured vehicle/trailer views

## Read-only contract

`vehicle_views.py` adds frozen projections over the immutable parsed SII AST.
It has no setter or serializer and does not modify a document, reorder fields,
normalize values, create defaults, or associate wheel wear with accessories.
The source `SiiDocument` remains the lossless representation.

## License plate

`LicensePlateView` mirrors `SCSLicensePlate.CheckSourceText`: after applying
the legacy SCS string unquoting boundary, it uses the first segment before
`|` as plate text and the second segment, trimmed only of `_` and spaces, as
country. A third or later segment is ignored as in C#. A string lacking `|`
is an invalid view (`valid=False`), corresponding to the legacy display's
`NON VALID FORMAT`; an absent SII field is `None`. There is no plate setter.

## Odometer and wheels

`OdometerView` exposes `odometer` and `odometer_float_part` separately. The
legacy item classes store them separately and no combined display calculation
was found, so none was invented. Integer conversion is offered only when the
stored `odometer` is decimal; the raw values remain available for all forms.

`WheelWearView` exposes ordered indexed `wheels_wear[]` entries as
`(index, raw_value)`. It intentionally does not link an index to a
`vehicle_wheel_accessory`: 11E.1 observed unequal counts in both games.

## Accessories and components

`accessories[]` is resolved polymorphically, preserving its original order:

| Block type | Read-only view |
| --- | --- |
| `vehicle_accessory` | data path, refund, and legacy path-derived component type (`basepart`, chassis/body/cabin/engine/transmission, or generalpart) |
| `vehicle_wheel_accessory` | data path, refund, offset, paint colour, and legacy tire/generalpart classification |
| `vehicle_addon_accessory` | explicit supported structural addon view |
| `vehicle_paint_job_accessory` | six legacy colour fields, `data_path`, and `refund` |
| unresolved reference | explicit `MissingAccessoryView`; no block is fabricated |
| another resolved type | `UnknownAccessoryView`; generic polymorphism does not fail |

`VehicleView` aggregates identifier, four condition fields, fuel, indexed
wheels, accessories, plate, and odometer. `TrailerView` aggregates cargo/body/
chassis conditions, wheels, accessories, plate, odometer, and the raw
`slave_trailer` reference. Constructing a trailer view does not traverse the
chain.

## ATS/ETS2 1.61 validation

Each fixture was decoded through the existing adapter using its private copy,
then parsed and viewed without mutation.

| Fixture | Validation |
| --- | --- |
| ATS 1.61 | vehicle view found valid plate, odometer, indexed wheels, resolved accessories, and paint accessory; document serialization was unchanged; original fixture unchanged. |
| ETS2 1.61 | vehicle and trailer views found valid plates, odometers, indexed wheels, resolved accessories, paint accessories, and trailer `slave_trailer: null`; document serialization was unchanged; original fixture unchanged. |

ATS encoded float tokens and ETS2 decimal examples are surfaced as raw values;
no view relies on a game-specific textual encoding.

## Tests

`test_vehicle_views.py` covers legacy plate parsing including invalid and
multi-segment cases, absent optional fields, odometer fields, ordered wheels,
all four observed accessory types, explicit missing reference, paint fields,
vehicle/trailer composition, slave reference, and lossless read-only use.

- Specific views: 5 passed.
- Vehicle/trailer-related regression subset: 26 passed.
