# 11F.1 -- Garage / Company / Market structural inspection

Read-only inspection through `SiiDecoder` / SII_Decrypt 1.5.3 and `parse_sii`. No fixture was written.

## ATS 1.61

- Parsed blocks: 17672
- Fixture SHA-256 before/after: `036AC1DD775B4E7E1B0DC11C29E7E039D97950CE7AAB8140DD6F6D59DF2E09CC` (unchanged)

### Economy

- `garages[]`: 119 references; resolved garages: 119; missing: 0; examples: [(0, 'garage.sacramento'), (1, 'garage.hays'), (2, 'garage.denver')]
- `driver_pool[]`: 353 entries; examples: [(0, 'driver.278'), (1, 'driver.86'), (2, 'driver.338')]
- `game_time`: `12447`
- `driver_pool[0]`: `driver.278`; type: `driver_ai`; garage slots: none

### Garages

- Count: 119
- Status values: {'0': 118, '6': 1}
- `vehicles[]`: entries=1, non-null=1, null/empty=0, indexed-contiguous-per-nonempty-garage=True, types={'vehicle': 1}, examples=[0]=_nameless.1c5.f43f.e5e8
- `drivers[]`: entries=1, non-null=1, null/empty=0, indexed-contiguous-per-nonempty-garage=True, types={'driver_player': 1}, examples=[0]=driver.159
- `trailers[]`: entries=0, non-null=0, null/empty=0, indexed-contiguous-per-nonempty-garage=True, types={}, examples=none
- Example garage with vehicle: `garage.mcallen`
- Example garage without vehicle: `garage.sacramento`
- Example garage with driver: `garage.mcallen`
- Example garage without driver: `garage.sacramento`
- Example garage with trailer: `NOT OBSERVED`
- Example garage empty: `garage.sacramento`

### Companies and cargo seeds

- `company` blocks: 2096; identifier examples: ['company.volatile.gld_frm.dodge_city', 'company.volatile.gld_frm.marysville', 'company.volatile.gm_food_str.junction_cty']
- Identifier scheme `company.volatile.<company_type>.<city>`: 2096/2096 observed; examples: ['gld_frm.dodge_city', 'gld_frm.marysville', 'gm_food_str.junction_cty']
- `discovered`: {'false': 1898, 'true': 198}
- `cargo_offer_seeds[]`: companies with seeds=2096, without=0, min=10, max=10
- Seed example: `company.volatile.gld_frm.dodge_city` -> [(0, '14088'), (1, '13514'), (2, '13554')]

### Freight offers

- `job_offer[]`: total=6544, companies with offers=1971, valid=6544, missing=0, resolved types={'job_offer_data': 6544}
- `job_offer_data` blocks reached from companies: 6544
- `target` quoted `<company_type>.<city>` maps to `company.volatile.<target>` for 5488/6544 observed jobs; suffix-resolved block types: {'company': 5488}; not observed in any block identifier: 1056 (examples: ['""', '""', '""'])
- `economy_event` blocks: 6738; `unit_link` references to company blocks: 6562
- Job example: `_nameless.1c6.b403.65a8`
  - `target`: PRESENT; value=`"fb_farm_pln.guymon"`; resolved type=`none`
  - `expiration_time`: PRESENT; value=`12538`; resolved type=`none`
  - `urgency`: PRESENT; value=`0`; resolved type=`none`
  - `cargo`: PRESENT; value=`cargo.flour`; resolved type=`none`
  - `company_truck`: PRESENT; value=`volvo_vnr_e`; resolved type=`none`
  - `trailer_variant`: PRESENT; value=`trailer.scs_curt53_3`; resolved type=`none`
  - `trailer_definition`: PRESENT; value=`trailer_def.scs.flatbed.single_53_3.curtain`; resolved type=`none`
  - `units_count`: PRESENT; value=`21`; resolved type=`none`

## ETS2 1.61

- Parsed blocks: 43027
- Fixture SHA-256 before/after: `DEBE167F2210C69E81588110C93D24A860E400A5C212EA80359A617C6E07868D` (unchanged)

### Economy

- `garages[]`: 236 references; resolved garages: 236; missing: 0; examples: [(0, 'garage.kiel'), (1, 'garage.strasbourg'), (2, 'garage.helsingborg')]
- `driver_pool[]`: 0 entries; examples: []
- `game_time`: `128562`

### Garages

- Count: 236
- Status values: {'3': 64, '0': 172}
- `vehicles[]`: entries=815, non-null=362, null/empty=453, indexed-contiguous-per-nonempty-garage=True, types={'vehicle': 362}, examples=[0]=_nameless.20c.d03a.7778, [1]=_nameless.20c.d03a.70e8, [2]=_nameless.20c.d03a.9ed8
- `drivers[]`: entries=815, non-null=354, null/empty=461, indexed-contiguous-per-nonempty-garage=True, types={'driver_ai': 353, 'driver_player': 1}, examples=[0]=driver.197, [1]=driver.343, [2]=driver.105
- `trailers[]`: entries=2, non-null=2, null/empty=0, indexed-contiguous-per-nonempty-garage=True, types={'trailer': 2}, examples=[0]=_nameless.20c.cdd0.1df8, [0]=_nameless.20c.cdd0.21d8
- Example garage with vehicle: `garage.kiel`
- Example garage without vehicle: `garage.magdeburg`
- Example garage with driver: `garage.kiel`
- Example garage without driver: `garage.magdeburg`
- Example garage with trailer: `garage.coimbra`
- Example garage empty: `garage.magdeburg`

### Companies and cargo seeds

- `company` blocks: 1919; identifier examples: ['company.volatile.medas.argostoli', 'company.volatile.medas.athens', 'company.volatile.medas.thessaloniki']
- Identifier scheme `company.volatile.<company_type>.<city>`: 1919/1919 observed; examples: ['medas.argostoli', 'medas.athens', 'medas.thessaloniki']
- `discovered`: {'false': 463, 'true': 1456}
- `cargo_offer_seeds[]`: companies with seeds=1919, without=0, min=10, max=10
- Seed example: `company.volatile.medas.argostoli` -> [(0, '129302'), (1, '129860'), (2, '130208')]

### Freight offers

- `job_offer[]`: total=6288, companies with offers=1753, valid=6288, missing=0, resolved types={'job_offer_data': 6288}
- `job_offer_data` blocks reached from companies: 6288
- `target` quoted `<company_type>.<city>` maps to `company.volatile.<target>` for 5390/6288 observed jobs; suffix-resolved block types: {'company': 5390}; not observed in any block identifier: 898 (examples: ['""', '""', '""'])
- `economy_event` blocks: 12004; `unit_link` references to company blocks: 6288
- Job example: `_nameless.20c.d087.c7e8`
  - `target`: PRESENT; value=`"brawen.bucuresti"`; resolved type=`none`
  - `expiration_time`: PRESENT; value=`129873`; resolved type=`none`
  - `urgency`: PRESENT; value=`1`; resolved type=`none`
  - `cargo`: PRESENT; value=`cargo.used_plast`; resolved type=`none`
  - `company_truck`: PRESENT; value=`volvo_fh2021_4x2_750`; resolved type=`none`
  - `trailer_variant`: PRESENT; value=`trailer.scs_curt_a`; resolved type=`none`
  - `trailer_definition`: PRESENT; value=`trailer_def.scs.box.single_3.curtain`; resolved type=`none`
  - `units_count`: PRESENT; value=`33`; resolved type=`none`

## Comparison and readiness

- Garage/company/job-offer/cargo-seed structures above are direct observations; absent examples are marked `NOT OBSERVED`, not incompatible.
- Readiness is assessed after a focused review of this report; no editor was created by 11F.1.

## Confirmed relationship map

```text
economy
  garages[] -> garage
    vehicles[] -> vehicle (when non-null)
    drivers[] -> driver_player or driver_ai (when non-null)
    trailers[] -> trailer (ETS2 observed; ATS NOT OBSERVED)
  driver_pool[] -> driver_ai (ATS observed; ETS2 empty)

company.volatile.<company_type>.<city>
  cargo_offer_seeds[] -> indexed unsigned-looking decimal tokens
  job_offer[] -> job_offer_data

job_offer_data
  target -> quoted <company_type>.<city> token, not a direct AST reference
  cargo/company_truck/trailer_variant/trailer_definition -> definition tokens,
    not blocks in these saves
```

The C# writer also updates existing `economy_event.unit_link` company events
when it changes job expiration times. Observed company-linked events: ATS
6562/6738; ETS2 6288/12004.

## ATS x ETS2 structural comparison

| Structure | ATS 1.61 | ETS2 1.61 |
| --- | --- | --- |
| economy / game_time / garages | OBSERVED | OBSERVED |
| garage vehicles and drivers | OBSERVED | OBSERVED |
| garage trailers | NOT OBSERVED | OBSERVED |
| driver_pool | 353 `driver_ai` refs | empty collection |
| company / seeds / job offers | OBSERVED | OBSERVED |
| job_offer_data | OBSERVED | OBSERVED |
| target/cargo/truck/trailer fields | token representation | token representation |

## Unknowns and risks for later subtasks

- The available ATS fixture has only one occupied garage slot and no garage
  trailer; this is NOT OBSERVED, not an incompatibility result.
- `job_offer_data.target` is a quoted destination token, not a direct block
  reference. Some target tokens do not have a matching current
  `company.volatile` block in the supplied fixture.
- Freight creation depends on legacy route, cargo, company-truck, and trailer
  catalogs plus `economy_event` timing; those writer semantics require their
  own focused mapping before mutation.

## Ready decisions

- Ready 11F.2 -- garage resolver/relocation: **YES**.
- Ready 11F.3 -- sale/slot semantics: **YES**.
- Ready 11F.4 -- cargo seeds: **YES**.
- Ready 11F.5 -- freight market: **YES**, subject to its focused legacy writer
  mapping; the required save structures are observed.

## Fixture integrity

- ATS game.sii SHA-256: `036AC1DD775B4E7E1B0DC11C29E7E039D97950CE7AAB8140DD6F6D59DF2E09CC`
- ETS2 game.sii SHA-256: `DEBE167F2210C69E81588110C93D24A860E400A5C212EA80359A617C6E07868D`
