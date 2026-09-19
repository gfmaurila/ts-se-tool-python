# 11H.4 — Company drivers and Convoy backend

`Driver_AI.cs` proves six skills, experience/training, and assigned
truck/trailer read fields. The company UI counts garage driver slots;
`DataManipulation.PrepareGarages` and garage controls prove relocation of driver
references. Existing transactional garage relocation was reused; no driver
skill/rating/income/hire/fire setters were invented.

`FormMethodsConvoyToolsTab.cs.cs` proves uppercase gzip-hex GPS copy/paste and
the `player.my_truck_placement` write. It also contains transient GPS-path and
multi-save dialog operations. This task implements current-position copy/paste
and the minimal position writer only.

`core.saves.drivers` provides side-effect-free typed player-driver, driver-truck
and driver-garage resolution plus `DriverView`; invalid references raise
`DriverGraphError`. Unknown fields/blocks and unrelated references survive.

ATS/ETS contain `driver_ai`; neither has Convoy units. ATS driver-to-garage is
not observed. ETS driver relocation passed serialize/reparse and
`SaveEditService` copied-save backup/staging/replace validation. Source fixtures
remained unchanged. Ruff/mypy and targeted driver/Convoy tests pass.

Limits: no GUI, multi-save transfer, modern Convoy behavior, or unsupported
driver formulas/setters.
