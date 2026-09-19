# 11E.5 -- Legacy TruckPaint copy/paste

## Legacy C# behavior

## Final classification

- **LEGACY CLIPBOARD CONTRACT: PASS.** `PartData`, `TruckPaint`, GZip,
  uppercase hexadecimal, immutable snapshot, and payload regressions are
  implemented.
- **SII PAINT VIEW: PASS / READ-ONLY.** The 11E.4 view exposes the six color
  fields, `data_path`, and `refund` from `vehicle_paint_job_accessory`.
- **PARTDATA TO SII WRITE-BACK: NOT ESTABLISHED.** No conversion is proven by
  the legacy C#; no speculative mapping is implemented.

`Forms/MainTabs/FormMethodsTruckTab.cs` implements the two handlers against
`UserTruckDictionary[...].Parts.Find(xp => xp.PartType == "paintjob").PartData`:

- Copy writes `TruckPaint\r\n`, then every `PartData` item followed by `\r\n`.
- The text is GZip-compressed with `ZipDataUtilities.zipText`, converted to
  uppercase hexadecimal, and placed on the GUI clipboard.
- Paste GZip-decodes the hexadecimal clipboard text, requires the first CRLF
  line to equal `TruckPaint`, then assigns every remaining line to a newly
  allocated `PartData` list. `StringSplitOptions.None` keeps the final empty
  entry emitted by Copy.
- The handlers do not parse, validate, or write a
  `vehicle_paint_job_accessory` SII block. They do not mention paint color
  fields, `data_path`, or `refund`.

The designer explicitly sets both paint buttons to `Enabled = false` in this
legacy version. A directed search found no producer mapping a SII paint block
to `UserCompanyTruckDataPart.PartData`.

## Field contract

| Field | Copy | Paste |
| --- | --- | --- |
| `mask_r_color` | Not mapped by legacy handler | Not mapped by legacy handler |
| `mask_g_color` | Not mapped by legacy handler | Not mapped by legacy handler |
| `mask_b_color` | Not mapped by legacy handler | Not mapped by legacy handler |
| `flake_color` | Not mapped by legacy handler | Not mapped by legacy handler |
| `flip_color` | Not mapped by legacy handler | Not mapped by legacy handler |
| `base_color` | Not mapped by legacy handler | Not mapped by legacy handler |
| `data_path` | Not mapped by legacy handler | Not mapped by legacy handler |
| `refund` | Not mapped by legacy handler | Not mapped by legacy handler |

## Python implementation

`tsse.application.legacy_paint_clipboard.LegacyPaintClipboard` is an immutable
snapshot of the proven transient `PartData` payload. It encodes/decodes the
legacy header, CRLF framing, GZip, and uppercase hexadecimal without retaining
a mutable source-list alias. Invalid hexadecimal/GZip/header input raises the
typed `LegacyPaintClipboardError`; field-level incomplete `PartData` remains
accepted, as in the handler.

No AST mutation API was added. Mapping this payload to the eight fields of
`vehicle_paint_job_accessory` would be a new behavior, not functional parity.
Consequently, transactional SII paste, cross-game SII paste, and a temporary
fixture mutation cannot be validated from the legacy implementation.

## 1.61 evidence and preservation

11E.1/11E.4 established real `vehicle_paint_job_accessory` blocks in both ATS
and ETS2 1.61, with the six color fields plus `data_path` and `refund`. The
legacy handlers provide no connection from their payload to those blocks.
The 11E.5 implementation is independent of fixtures and does not read or
write either original `game.sii`; the ATS and ETS2 fixtures remain intact.

## Tests

`tests/unit/test_legacy_paint_clipboard.py` covers immutable copy snapshots,
uppercase GZip/hex framing, the legacy ignored final unpaired hex character,
legacy trailing-empty paste behavior, incomplete data acceptance, invalid
payloads, and typed invalid `PartData` errors.

Regression subset:

```text
tests/unit/test_vehicle_views.py
tests/unit/test_truck_editor.py
tests/unit/test_trailer_editor.py
tests/unit/test_legacy_paint_clipboard.py
35 passed
```

## Status

The proven clipboard contract is implemented and tested. SII paint-field
copy/paste is **not established by TS SE Tool 0.3.11.0** and is intentionally
not implemented; an authoritative mapping or a user-approved new behavior is
required before it can be added.
