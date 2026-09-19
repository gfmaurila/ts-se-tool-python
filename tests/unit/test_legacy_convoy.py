import gzip

import pytest

from tsse.application.legacy_convoy import (
    LegacyConvoyError,
    copy_truck_position,
    paste_truck_position,
    set_truck_position,
)
from tsse.core.sii import parse_sii

SOURCE = "SiiNunit\n{\nplayer : player.one {\n my_truck_placement: (1,2,3)\n future: keep\n}\n}\n"


def test_legacy_gps_copy_paste_and_minimal_player_write() -> None:
    payload = copy_truck_position("(1,2,3)")
    assert payload == payload.upper()
    assert paste_truck_position(payload) == "(1,2,3)"
    edited = set_truck_position(parse_sii(SOURCE), "(4,5,6)")
    assert "my_truck_placement: (4,5,6)" in edited.serialize()
    assert "future: keep" in edited.serialize()


@pytest.mark.parametrize("payload", ["", "GG", gzip.compress(b"Wrong\r\nX").hex()])
def test_legacy_gps_rejects_invalid_payload(payload: str) -> None:
    with pytest.raises(LegacyConvoyError):
        paste_truck_position(payload)
