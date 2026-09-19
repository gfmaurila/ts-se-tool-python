import pytest

from tsse.application.cargo_market import (
    CargoMarketError,
    randomize_city,
    randomize_company,
    reset_city,
    reset_company,
)
from tsse.core.sii import parse_sii

SOURCE = """SiiNunit
{
economy : economy.1 {
 game_time: 1000
 economy_unknown: keep
}
company : company.volatile.farm.alpha {
 job_offer: 1
 job_offer[0]: job.alpha
 cargo_offer_seeds: 2
 cargo_offer_seeds[0]: 10
 cargo_offer_seeds[1]: 20
 unknown_company: alpha
}
company : company.volatile.mine.alpha {
 job_offer: 1
 job_offer[0]: job.mine
 cargo_offer_seeds: 2
 cargo_offer_seeds[0]: 30
 cargo_offer_seeds[1]: 40
}
company : company.volatile.farm.beta {
 job_offer: 0
 cargo_offer_seeds: 2
 cargo_offer_seeds[0]: 50
 cargo_offer_seeds[1]: 60
}
}
"""


def seeds(text: str, identifier: str) -> list[str]:
    block = next(item for item in parse_sii(text).blocks if item.identifier == identifier)
    return [
        field.value
        for field in block.fields
        if field.name == "cargo_offer_seeds" and field.array_index is not None
    ]


def fixed(_low: int, _high: int) -> int:
    return 180


def test_randomize_company_uses_game_time_and_preserves_other_fields() -> None:
    edited = randomize_company(parse_sii(SOURCE), "company.volatile.farm.alpha", fixed)
    text = edited.serialize()
    assert seeds(text, "company.volatile.farm.alpha") == ["1180", "1180"]
    assert seeds(text, "company.volatile.mine.alpha") == ["30", "40"]
    assert "job_offer[0]: job.alpha" in text
    assert "unknown_company: alpha" in text


def test_reset_company_clears_seeds_without_touching_jobs() -> None:
    edited = reset_company(parse_sii(SOURCE), "company.volatile.farm.alpha")
    text = edited.serialize()
    assert seeds(text, "company.volatile.farm.alpha") == []
    assert "job_offer[0]: job.alpha" in text
    assert parse_sii(text).serialize() == text


def test_city_operations_touch_only_non_excluded_companies() -> None:
    edited = randomize_city(parse_sii(SOURCE), "alpha", fixed)
    text = edited.serialize()
    assert seeds(text, "company.volatile.farm.alpha") == ["1180", "1180"]
    assert seeds(text, "company.volatile.mine.alpha") == ["1180", "1180"]
    assert seeds(text, "company.volatile.farm.beta") == ["50", "60"]
    reset = reset_city(edited, "alpha")
    assert seeds(reset.serialize(), "company.volatile.farm.alpha") == []
    assert seeds(reset.serialize(), "company.volatile.mine.alpha") == []
    assert seeds(reset.serialize(), "company.volatile.farm.beta") == ["50", "60"]


def test_invalid_company_city_and_malformed_seeds_are_typed_and_atomic() -> None:
    document = parse_sii(SOURCE)
    with pytest.raises(CargoMarketError):
        randomize_company(document, "company.volatile.farm.missing", fixed)
    with pytest.raises(CargoMarketError):
        reset_city(document, "missing",)
    malformed = parse_sii(SOURCE.replace("cargo_offer_seeds[1]: 40", "cargo_offer_seeds[2]: 40"))
    original = malformed.serialize()
    with pytest.raises(CargoMarketError):
        randomize_city(malformed, "alpha", fixed)
    assert malformed.serialize() == original
