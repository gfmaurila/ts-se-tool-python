import pytest

from tsse.application.player_editor import (
    PlayerEditError,
    experience_to_level,
    level_to_experience,
    resolve_driver,
    set_company_name,
    set_experience,
    set_gender,
    set_hq_city,
    set_money,
    set_skill,
    unlock_dealer,
    unlock_recruitment,
    visit_city,
)
from tsse.core.sii import parse_sii

SOURCE = """SiiNunit
{
economy : e.one {
 experience_points: 100
 adr: 1
 long_distance: 2
 future: preserve
}
bank : b.one {
 money_account: 200
 unknown_bank: preserve
}
}
"""


def test_player_edits_round_trip_and_preserve_unknown_fields() -> None:
    edited = set_skill(set_money(set_experience(parse_sii(SOURCE), 999), -50), "adr", 6)

    assert "experience_points: 999" in edited.serialize()
    assert "money_account: -50" in edited.serialize()
    assert "adr: 6" in edited.serialize()
    assert "future: preserve" in edited.serialize()
    assert "unknown_bank: preserve" in edited.serialize()
    assert parse_sii(edited.serialize()).serialize() == edited.serialize()


@pytest.mark.parametrize("skill,value", [("unknown", 1), ("adr", 7)])
def test_rejects_unproven_or_invalid_skills(skill: str, value: int) -> None:
    with pytest.raises(PlayerEditError):
        set_skill(parse_sii(SOURCE), skill, value)


@pytest.mark.parametrize(
    ("game", "level", "expected"),
    [("ats", 0, 199), ("ets2", 1, 699), ("ats", 1, 699), ("ats", 150, 986999)],
)
def test_legacy_level_to_experience(game: str, level: int, expected: int) -> None:
    assert level_to_experience(game, level) == expected


def test_legacy_experience_to_level_thresholds_and_clamps() -> None:
    assert experience_to_level("ats", 0) == (0, 200)
    assert experience_to_level("ats", 199) == (0, 200)
    assert experience_to_level("ats", 200) == (1, 700)
    assert experience_to_level("ets2", 699) == (1, 700)
    assert level_to_experience("ats", -1) == 199
    assert level_to_experience("ats", 999) == level_to_experience("ats", 150)


def test_visit_city_keeps_parallel_arrays_and_unknown_text() -> None:
    source = parse_sii("""SiiNunit
{
economy : e {
 visited_cities: 1
 visited_cities[0]: old
 visited_cities_count: 1
 visited_cities_count[0]: 4
 future: preserve
}
}
""")
    edited = visit_city(source, "new")
    assert "visited_cities[1]: new" in edited.serialize()
    assert "visited_cities_count[1]: 1" in edited.serialize()
    assert "future: preserve" in edited.serialize()
    assert visit_city(edited, "new").serialize() == edited.serialize()
    assert parse_sii(edited.serialize()).blocks


def test_visit_city_rejects_inconsistent_collections_without_mutation() -> None:
    source = parse_sii("""SiiNunit
{
economy : e {
 visited_cities: 1
 visited_cities[0]: old
 visited_cities_count: 0
}
}
""")
    with pytest.raises(PlayerEditError, match="inconsistent"):
        visit_city(source, "new")


def test_resolve_driver_accepts_real_block_types_and_empty_quit_warned() -> None:
    document = parse_sii("""SiiNunit
{
player : p {
 drivers: 2
 drivers[0]: driver.player
 drivers[1]: driver.ai
 driver_readiness_timer: 2
 driver_readiness_timer[0]: 0
 driver_readiness_timer[1]: 0
 driver_quit_warned: 0
}
driver_player : driver.player {
 future: preserve
}
driver_ai : driver.ai {
 experience_points: 1
 training_policy: 1
 driver_job: preserve
}
}
""")
    assert resolve_driver(document, 0).type_name == "driver_player"
    assert resolve_driver(document, 1).type_name == "driver_ai"
    with pytest.raises(PlayerEditError, match="does not exist"):
        resolve_driver(document, 2)


def test_gender_and_company_name_are_lossless_and_bounded() -> None:
    document = parse_sii("""SiiNunit
{
user_profile : p {
 male: true
 company_name: "Old"
 future: preserve
}
}
""")
    edited = set_company_name(set_gender(document, False), "x" * 20)
    assert "male: false" in edited.serialize()
    assert 'company_name: "xxxxxxxxxxxxxxxxxxxx"' in edited.serialize()
    assert "future: preserve" in edited.serialize()
    assert parse_sii(edited.serialize()).blocks
    for name in ("", "x" * 21):
        with pytest.raises(PlayerEditError):
            set_company_name(document, name)


def test_hq_unlocks_and_driver_error_paths() -> None:
    document = parse_sii("""SiiNunit
{
player : p {
 hq_city: old
 drivers: 1
 drivers[0]: missing
 driver_readiness_timer: 1
 driver_readiness_timer[0]: 0
 driver_quit_warned: 0
}
economy : e {
 unlocked_dealers: 1
 unlocked_dealers[0]: old
 unlocked_recruitments: 1
 unlocked_recruitments[0]: old
}
}
""")
    edited = unlock_recruitment(unlock_dealer(set_hq_city(document, "new"), "new"), "new")
    assert "hq_city: new" in edited.serialize()
    assert unlock_dealer(edited, "new").serialize() == edited.serialize()
    assert unlock_recruitment(edited, "new").serialize() == edited.serialize()
    with pytest.raises(PlayerEditError, match="reference is missing"):
        resolve_driver(document, 0)
    with pytest.raises(PlayerEditError):
        set_gender(document, 1)  # type: ignore[arg-type]
