# 11F.2 -- Garage resolver and transactional relocation

## Legacy behavior

- Driver/truck out replaces exactly the selected garage slot with `null` and
  appends the removed reference to transient parallel lists (`extraDrivers` /
  `extraVehicles`), with a `null` peer entry.
- Driver in uses the first selected transient driver and fills every `null`
  driver slot of every garage whose status is not zero. This literal legacy
  behavior can duplicate that reference across free slots.
- Truck in consumes selected transient trucks in order, filling free vehicle
  slots of active garages without compacting arrays. Items left without a slot
  remain transient.
- `buttonMoveDriversOut_Click` itself declines `economy.driver_pool[0]`; this
  is localized to driver-out, not a global relocation policy.

## Python contract

`garage_relocation.py` resolves `economy.garages[]` to real `garage` blocks,
validates declared indexed collections before mutation, and supports
`driver_player`/`driver_ai` driver references and `vehicle` references.
Missing or unexpected blocks raise `GarageRelocationError` before a document is
rewritten. Collections retain their original indices and `null` slots; trailers,
status, item blocks, and unknown fields are untouched.

## Validation

- Synthetic regressions: 9 passed. They cover driver-player/AI and vehicle
  resolution, empty/missing/unexpected/inconsistent input, pool-zero behavior,
  null-slot preservation, transient state, and SiiN reparse.
- ATS 1.61 temporary decode: driver and vehicle out/in reparse PASS.
- ETS2 1.61 temporary decode: driver and vehicle out/in reparse PASS.
- Originals were read-only and verified unchanged by the validation script.

## Scope boundary

No garage sale/status change, trailer relocation, Cargo Market, or Freight
Market behavior was implemented. Same-garage placement is not a dedicated
legacy operation: the legacy in handlers scan every active garage, including
the source when it is active.
