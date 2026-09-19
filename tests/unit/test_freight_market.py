from dataclasses import replace

import pytest

from tsse.application.freight_market import (
    FreightMarketError,
    JobOfferPayload,
    clear_pending_jobs,
    expiration_time,
    resolve_job_offer,
    write_job_offer,
)
from tsse.core.sii import parse_sii

SOURCE = """SiiNunit
{
economy : economy.1 {
 game_time: 1000
}
company : company.volatile.farm.alpha {
 job_offer: 1
 job_offer[0]: job.1
 cargo_offer_seeds: 2
 cargo_offer_seeds[0]: 10
 cargo_offer_seeds[1]: 20
 unknown_company: keep
}
job_offer_data : job.1 {
 target: \"farm.beta\"
 expiration_time: 2000
 urgency: 1
 shortest_distance_km: 30
 ferry_time: 0
 ferry_price: 0
 cargo: cargo.old
 company_truck: truck.old
 trailer_variant: trailer.old.variant
 trailer_definition: trailer.old.definition
 units_count: 2
 unknown_job: keep
}
economy_event : economy_event.1 {
 time: 1800
 unit_link: company.volatile.farm.alpha
 param: 0
}
}
"""


def payload() -> JobOfferPayload:
    return JobOfferPayload(
        target="mine.beta",
        expiration_time=2500,
        urgency=2,
        shortest_distance_km=100,
        ferry_time=4,
        ferry_price=50,
        cargo="cargo.new",
        company_truck="truck.new",
        trailer_variant="trailer.new.variant",
        trailer_definition="trailer.new.definition",
        units_count=7,
    )


def test_resolve_write_and_reparse_existing_job_preserves_unknowns() -> None:
    document = parse_sii(SOURCE)
    assert resolve_job_offer(document, "company.volatile.farm.alpha", 0).identifier == "job.1"
    edited = write_job_offer(document, "company.volatile.farm.alpha", 0, payload())
    text = edited.serialize()
    assert 'target: "mine.beta"' in text
    assert "cargo: cargo.new" in text
    assert "units_count: 7" in text
    assert "unknown_job: keep" in text
    assert "cargo_offer_seeds[0]: 10" in text
    assert "time: 2500" in text
    assert parse_sii(text).serialize() == text


def test_expiration_matches_legacy_formula_and_clear_is_transient_only() -> None:
    assert expiration_time(1000, lambda _low, _high: 180, 2, 5) == 1780
    assert clear_pending_jobs([object(), object()]) == ()


def test_invalid_reference_payload_and_missing_field_are_atomic() -> None:
    document = parse_sii(SOURCE)
    original = document.serialize()
    with pytest.raises(FreightMarketError):
        resolve_job_offer(document, "company.volatile.farm.alpha", 1)
    with pytest.raises(FreightMarketError):
        write_job_offer(
            document,
            "company.volatile.farm.alpha",
            0,
            replace(payload(), units_count=-1),
        )
    assert document.serialize() == original
    malformed = parse_sii(SOURCE.replace("job_offer_data : job.1", "vehicle : job.1"))
    with pytest.raises(FreightMarketError):
        resolve_job_offer(malformed, "company.volatile.farm.alpha", 0)
