import pytest

from tsse.application.player_editor import (
    PlayerEditError,
    set_experience,
    set_money,
    set_skill,
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
