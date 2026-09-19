# 11F.3 — Garage sale / slot semantics

## Legacy workflow

`FormMethodsCompanyTab.buttonGaragesSell_Click` changes the selected HQ to
status `6` and every other selected garage to `0`, then calls
`DataManipulation.PrepareGarages`.  Statuses established by the legacy helper
are `0` = not owned, `2` = small (3 slots), `3` = large (5 slots), and `6` =
tiny (1 slot).

`PrepareGarages` clears drivers, vehicles and trailers from status-0 garages;
it truncates/pads only driver and vehicle slots for active capacities.  It does
not truncate trailers in active garages. Removed trailers are appended to the
HQ. Drivers/vehicles are transient while the sale-content form is open; on
write, non-null removed drivers are appended to `economy.driver_pool`.

## Implemented parity

`sell_garage` atomically applies the status change and the complete capacity
pass, preserving indexed slots and unknown fields. Driver/vehicle list length
is validated before mutation. The legacy `driver_pool[0]` swap is reproduced
when that protected pool driver is among removed drivers. `driver_player` is
treated as a regular driver reference. Trailer blocks are never deleted.

There is no cancel rollback in the located legacy form: its move lists are UI
transient state over the already edited in-memory model. The Python operation
is transactional instead: any invalid reference/collection raises a typed
error before source replacement.

## Tests

Synthetic coverage verifies a non-HQ sale, HQ/tiny sale with pool-driver swap,
slot padding/no compaction, trailer transfer, unknown preservation, SiiN
serialize/reparse, and rollback on malformed paired collections.

`tests/unit/test_garage_relocation.py`: **12 passed**.

## Real fixture validation

The adapter was given the project-local `.tmp-11f3-validation` root. On
temporary copies only:

- ATS 1.61: decrypt PASS, parse PASS, sale of `garage.sacramento` PASS,
  SiiN serialize/reparse PASS.
- ETS2 1.61: decrypt PASS, parse PASS, sale of `garage.kiel` PASS,
  SiiN serialize/reparse PASS.

SHA-256 before/after was identical for both original `game.sii` files.
