import shutil
from pathlib import Path

import pytest

from tsse.application.garage_relocation import move_driver_out
from tsse.application.save_edit_service import SaveEditService
from tsse.core.saves.drivers import build_driver_view, driver_garage
from tsse.core.sii import parse_sii
from tsse.infrastructure.decoder import SiiDecoder

FIXTURES = [
    Path("projeto_atual/ATS/67666D617572696C61202D207A657261646F/save/autosave/game.sii"),
    Path("projeto_atual/ETS/4D4150415F455453/save/autosave/game.sii"),
]


def _driver_in_garage(document):  # type: ignore[no-untyped-def]
    units = {block.identifier: block for block in document.blocks}
    for garage in document.blocks:
        if garage.type_name != "garage":
            continue
        for field in garage.fields:
            if field.name == "drivers" and field.array_index is not None:
                driver = units.get(field.value)
                if driver is not None and driver.type_name == "driver_ai":
                    return garage, field.array_index, driver
    pytest.fail("fixture has no driver_ai assigned to a garage slot")


def _first_driver(document):  # type: ignore[no-untyped-def]
    driver = next((block for block in document.blocks if block.type_name == "driver_ai"), None)
    if driver is None:
        pytest.fail("fixture has no driver_ai")
    return driver


@pytest.mark.parametrize("fixture", FIXTURES)
def test_real_fixture_driver_view_and_garage_mutation_round_trip(fixture: Path) -> None:
    original = fixture.read_bytes()
    document = parse_sii(SiiDecoder().decode_file(fixture).data.decode("utf-8"))
    driver = _first_driver(document)

    assert build_driver_view(document, driver).identifier == driver.identifier
    garage = driver_garage(document, driver)
    if garage is not None:
        slot = next(
            field.array_index
            for field in garage.fields
            if field.name == "drivers" and field.value == driver.identifier
        )
        assert slot is not None
        edited, removed = move_driver_out(document, garage.identifier, slot)
        assert removed.drivers == (driver.identifier,)
        assert parse_sii(edited.serialize()).blocks
    assert fixture.read_bytes() == original


def test_ets_driver_garage_mutation_uses_production_save_pipeline(tmp_path: Path) -> None:
    fixture = FIXTURES[1]
    original = fixture.read_bytes()
    decoded = parse_sii(SiiDecoder().decode_file(fixture).data.decode("utf-8"))
    garage, slot, driver = _driver_in_garage(decoded)
    copied = tmp_path / "game.sii"
    shutil.copy2(fixture, copied)

    result = SaveEditService().save(
        copied, lambda document: move_driver_out(document, garage.identifier, slot)[0]
    )
    written = parse_sii(copied.read_text(encoding="utf-8"))
    written_garage = next(
        block for block in written.blocks if block.identifier == garage.identifier
    )
    assert (
        next(field.value for field in written_garage.fields if field.key == f"drivers[{slot}]")
        == "null"
    )
    assert result.backup_path.read_bytes() == original
    assert fixture.read_bytes() == original
