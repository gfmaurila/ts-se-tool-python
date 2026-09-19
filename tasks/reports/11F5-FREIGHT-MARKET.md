# 11F.5 — Freight Market

## Legacy handlers

`AddCargo` builds a transient `JobAdded` queue. `PrepareCompaniesJobWrite`
later iterates that queue and writes into the already existing
`company.job_offer[i]` reference and its `job_offer_data` block. The legacy
does not allocate a new SII block or ID. `ClearJobData` clears only the
transient queue; it does not delete persistent job blocks or references.
During save, matching `economy_event` entries are updated by `unit_link` and
`param` to the queued job expiration time; unrelated events remain unchanged.

The written fields are `target`, `expiration_time`, `urgency`,
`shortest_distance_km`, `ferry_time`, `ferry_price`, `cargo`, `company_truck`,
`trailer_variant`, `trailer_definition`, and `units_count`. Unknown fields and
all unrelated collections are preserved. `target` is quoted as
`"<destination_company>.<destination_city>"`; cargo receives the `cargo.`
prefix. `expiration_time` is `game_time + Random.Next(180,1800) +
JobsAmountAdded * JobPickupTime * 60`.

## Implementation

`freight_market.py` provides typed `JobOfferPayload`, company/index resolver,
transactional existing-block writer, expiration helper, matching
`economy_event` update, and transient clear semantics. Invalid references,
malformed collections, missing fields, and invalid numeric inputs fail before
source replacement. No job ID allocator, new block creation, or persistent
delete is invented.

## Real fixtures

ATS and ETS2 were decrypted using a project-local temporary root. For each,
the first valid company job was resolved, rewritten with its existing values,
serialized to temporary SiiN, reparsed, and its reference remained stable.
Original SHA-256 remained unchanged:

- ATS: `036AC1DD775B4E7E1B0DC11C29E7E039D97950CE7AAB8140DD6F6D59DF2E09CC`
- ETS2: `DEBE167F2210C69E81588110C93D24A860E400A5C212EA80359A617C6E07868D`

## Tests

Three Freight Market tests cover resolve/write/reparse, exact expiration
formula, transient clear, unknown/job/seed preservation, malformed references,
and atomic failure. Freight + Cargo + garage regression subset: 19 passed.
