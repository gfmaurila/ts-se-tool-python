import shutil
from pathlib import Path

import pytest

from tsse.application.save_edit_service import SaveEditService
from tsse.application.trailer_editor import TrailerComponent, repair_trailer_component
from tsse.application.truck_editor import TruckComponent, repair_truck_component
from tsse.core.saves.vehicle_graph import (
    resolve_assigned_trailer,
    resolve_assigned_truck,
    resolve_trailer_chain,
)
from tsse.core.saves.vehicle_views import build_trailer_view, build_vehicle_view
from tsse.core.sii import parse_sii
from tsse.infrastructure.decoder import SiiDecoder

ATS = Path("projeto_atual/ATS/67666D617572696C61202D207A657261646F/save/autosave/game.sii")
ETS = Path("projeto_atual/ETS/4D4150415F455453/save/autosave/game.sii")


def _first_with_fields(document, type_name: str, fields: set[str]):  # type: ignore[no-untyped-def]
    for block in document.blocks:
        if block.type_name == type_name and fields <= {field.key for field in block.fields}:
            return block
    pytest.fail(f"fixture has no {type_name} with {sorted(fields)}")


@pytest.mark.parametrize("fixture", [ATS, ETS])
def test_real_fixture_vehicle_components_round_trip_without_mutating_fixture(fixture: Path) -> None:
    original = fixture.read_bytes()
    document = parse_sii(SiiDecoder().decode_file(fixture).data.decode("utf-8"))

    # Both frozen fixtures retain a null current assignment; null is an explicit valid result.
    assert resolve_assigned_truck(document) is None
    truck = _first_with_fields(
        document,
        "vehicle",
        {"engine_wear", "transmission_wear", "chassis_wear", "cabin_wear", "fuel_relative"},
    )
    view = build_vehicle_view(document, truck.identifier)
    assert view.components.engine_wear is not None
    assert view.fuel_relative is not None

    edited = repair_truck_component(document, truck.identifier, TruckComponent.ENGINE)
    reparsed = parse_sii(edited.serialize())
    assert build_vehicle_view(reparsed, truck.identifier).components.engine_wear == "0"
    assert fixture.read_bytes() == original


def test_ets_fixture_trailer_components_round_trip_without_mutating_fixture() -> None:
    original = ETS.read_bytes()
    document = parse_sii(SiiDecoder().decode_file(ETS).data.decode("utf-8"))

    assert resolve_assigned_trailer(document) is None
    trailer = _first_with_fields(
        document,
        "trailer",
        {"cargo_damage", "trailer_body_wear", "chassis_wear", "slave_trailer"},
    )
    view = build_trailer_view(document, trailer.identifier)
    assert view.components.cargo_damage is not None
    assert resolve_trailer_chain(document, trailer.identifier)

    edited = repair_trailer_component(document, trailer.identifier, TrailerComponent.BODY)
    reparsed = parse_sii(edited.serialize())
    assert build_trailer_view(reparsed, trailer.identifier).components.body_wear == "0"
    assert ETS.read_bytes() == original


def test_real_fixture_truck_repair_uses_production_save_pipeline_on_a_copy(
    tmp_path: Path,
) -> None:
    original = ATS.read_bytes()
    decoded = parse_sii(SiiDecoder().decode_file(ATS).data.decode("utf-8"))
    truck = _first_with_fields(
        decoded,
        "vehicle",
        {"engine_wear", "transmission_wear", "chassis_wear", "cabin_wear", "wheels_wear"},
    )
    copied = tmp_path / "game.sii"
    shutil.copy2(ATS, copied)

    result = SaveEditService().save(
        copied,
        lambda document: repair_truck_component(document, truck.identifier, TruckComponent.ENGINE),
    )
    written = parse_sii(copied.read_text(encoding="utf-8"))
    assert build_vehicle_view(written, truck.identifier).components.engine_wear == "0"
    assert result.backup_path.read_bytes() == original
    assert ATS.read_bytes() == original


def test_real_ets_trailer_repair_uses_production_save_pipeline_on_a_copy(tmp_path: Path) -> None:
    original = ETS.read_bytes()
    decoded = parse_sii(SiiDecoder().decode_file(ETS).data.decode("utf-8"))
    trailer = _first_with_fields(decoded, "trailer", {"cargo_damage", "slave_trailer"})
    copied = tmp_path / "game.sii"
    shutil.copy2(ETS, copied)

    result = SaveEditService().save(
        copied,
        lambda document: repair_trailer_component(
            document, trailer.identifier, TrailerComponent.CARGO
        ),
    )
    written = parse_sii(copied.read_text(encoding="utf-8"))
    assert build_trailer_view(written, trailer.identifier).components.cargo_damage == "0"
    assert result.backup_path.read_bytes() == original
    assert ETS.read_bytes() == original
