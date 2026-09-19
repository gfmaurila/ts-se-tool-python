# Task 11E.3 — Trailer repair and slave-trailer parity

## Legacy C# behavior

`buttonTrailerRepair_Click` starts at the selected trailer and, at each
`slave_trailer` link until `null`, loads that trailer's `TrailerMainData`, sets
`cargo_damage`, `trailer_body_wear`, and `chassis_wear` to `0`, and replaces
`wheels_wear` with an empty list. Thus total repair traverses the complete
linear slave chain.

`buttonTrailerElRepair_Click` exposes four UI indexes: `0` cargo, `1` body,
`2` chassis, and `3` wheels. Cargo/body/chassis become `0`; wheel repair
replaces the complete `wheels_wear` list. The handler walks the
`slave_trailer` names to `null`, but `selectedTrailerData` is assigned before
the label and is not reassigned inside the loop. Consequently, on a valid
multi-trailer chain its *individual* operation repeatedly targets only the
original selected trailer. This legacy behavior is reproduced deliberately.

No per-wheel repair exists. The handlers do not modify accessories, plate,
odometer, or `odometer_float_part`.

## Safe Python behavior

`repair_trailer` resolves and validates the entire chain before preparing any
replacement. It repairs every resolved trailer for the total action.
`repair_trailer_component` validates the same chain, then mutates only the
selected trailer to match the legacy handler. `TrailerComponent` is a closed
enum, so unknown component names raise `TrailerEditError`.

The resolver requires each target to be a `trailer` block and a present
`slave_trailer` field. Missing targets, unexpected target types, self-cycles,
and multi-node cycles raise `TrailerEditError`. Cycle detection is a Python
safety guard against malformed input, not a claim that the legacy UI handled
cycles. Since all resolution/field/array checks occur before reparsing a new
document, error paths leave the original AST untouched.

`wheels_wear` is validated as a declared, contiguous indexed array before it
is cleared to count `0`; no relationship to wheel accessories is invented.

## Preservation

Only the legacy condition fields are changed. `accessories[]`,
`license_plate`, `odometer`, `odometer_float_part`, unknown fields, and blocks
outside the total-repair chain remain textually preserved.

## 1.61 validation

| Fixture | Result |
| --- | --- |
| ETS2 1.61 | Decoded copy -> selected real trailer -> total repair and cargo-only repair -> serialize/reparse: PASS. Original `game.sii` byte-for-byte unchanged. |
| ATS 1.61 | Trailer **NOT OBSERVED** in the supplied fixture. This is not a compatibility failure; synthetic compatible SiiN regressions cover the legacy structure. |

The ETS2 trailer's observed chain is `trailer -> null`; no real non-trivial
chain was available, so the multi-link, missing-target, type, and cycle cases
are explicitly covered by small synthetic fixtures.

## Tests

`tests/unit/test_trailer_editor.py` now covers total repair, all four
individual controls, full `A -> B -> C -> null` total-chain traversal,
preservation, missing reference, unexpected target type, self-cycle,
multi-cycle, invalid component, malformed wheels, transactionality, and
serialize/reparse.

- `pytest tests/unit/test_trailer_editor.py --basetemp=.pytest-tmp-11e3-trailer`: 11 passed.
- Related truck/trailer regression subset: 21 passed.
