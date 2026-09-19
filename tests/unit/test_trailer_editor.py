import pytest

from tsse.application.trailer_editor import (
    TrailerComponent,
    TrailerEditError,
    find_trailer,
    repair_trailer,
    repair_trailer_component,
)
from tsse.core.sii import parse_sii


def _trailer(identifier: str, slave: str = "null") -> str:
    return f"""trailer : {identifier} {{
 cargo_damage: 0.5
 trailer_body_wear: 0.2
 chassis_wear: 0.1
 wheels_wear: 2
 wheels_wear[0]: 0.7
 wheels_wear[1]: 0.8
 accessories: 1
 accessories[0]: accessory.keep
 license_plate: \"KEEP|country\"
 odometer: 123
 odometer_float_part: 0.4
 slave_trailer: {slave}
 unknown_future: preserve
}}
"""


SOURCE = "SiiNunit\n{\n" + _trailer("trailer.one") + _trailer("trailer.two") + "}\n"


def _values(source: str, identifier: str) -> dict[str, str]:
    block = next(block for block in parse_sii(source).blocks if block.identifier == identifier)
    return {field.key: field.value for field in block.fields}


def test_total_repair_matches_legacy_and_preserves_unrelated_content() -> None:
    edited = repair_trailer(parse_sii(SOURCE), "trailer.one")
    values = _values(edited.serialize(), "trailer.one")
    trailer = find_trailer(edited, "trailer.one")

    assert (trailer.cargo_damage, trailer.body_wear, trailer.chassis_wear) == (0.0, 0.0, 0.0)
    assert values["wheels_wear"] == "0"
    assert not any(key.startswith("wheels_wear[") for key in values)
    assert values["accessories[0]"] == "accessory.keep"
    assert values["license_plate"] == '"KEEP|country"'
    assert values["odometer"] == "123"
    assert values["odometer_float_part"] == "0.4"
    assert values["unknown_future"] == "preserve"
    assert _values(edited.serialize(), "trailer.two")["cargo_damage"] == "0.5"
    assert parse_sii(edited.serialize()).serialize() == edited.serialize()


def test_total_repair_traverses_the_entire_legacy_slave_chain() -> None:
    source = (
        "SiiNunit\n{\n"
        + _trailer("trailer.a", "trailer.b")
        + _trailer("trailer.b", "trailer.c")
        + _trailer("trailer.c")
        + "}\n"
    )
    edited = repair_trailer(parse_sii(source), "trailer.a")

    for identifier in ("trailer.a", "trailer.b", "trailer.c"):
        values = _values(edited.serialize(), identifier)
        assert (
            values["cargo_damage"] == values["trailer_body_wear"] == values["chassis_wear"] == "0"
        )
        assert values["wheels_wear"] == "0"
        assert values["unknown_future"] == "preserve"


@pytest.mark.parametrize(
    ("component", "field"),
    [
        (TrailerComponent.CARGO, "cargo_damage"),
        (TrailerComponent.BODY, "trailer_body_wear"),
        (TrailerComponent.CHASSIS, "chassis_wear"),
        (TrailerComponent.WHEELS, "wheels_wear"),
    ],
)
def test_individual_repair_follows_legacy_slave_chain_behavior(
    component: TrailerComponent, field: str
) -> None:
    source = "SiiNunit\n{\n" + _trailer("trailer.a", "trailer.b") + _trailer("trailer.b") + "}\n"
    edited = repair_trailer_component(parse_sii(source), "trailer.a", component)
    selected = _values(edited.serialize(), "trailer.a")
    slave = _values(edited.serialize(), "trailer.b")

    assert selected[field] == "0"
    if component is TrailerComponent.WHEELS:
        assert not any(key.startswith("wheels_wear[") for key in selected)
    else:
        assert selected["wheels_wear[0]"] == "0.7"
    # The C# handler updates the currently traversed slave-trailer object.
    assert slave[field] == "0"
    if component is TrailerComponent.WHEELS:
        assert not any(key.startswith("wheels_wear[") for key in slave)
    else:
        assert slave["wheels_wear[0]"] == "0.7"


@pytest.mark.parametrize(
    ("source", "message"),
    [
        ("SiiNunit\n{\n" + _trailer("trailer.a", "trailer.missing") + "}\n", "missing trailer"),
        (
            "SiiNunit\n{\n"
            + _trailer("trailer.a", "not_a_trailer")
            + "vehicle_accessory : not_a_trailer {\n}\n}\n",
            "unexpected type",
        ),
        ("SiiNunit\n{\n" + _trailer("trailer.a", "trailer.a") + "}\n", "cycle"),
        (
            "SiiNunit\n{\n"
            + _trailer("trailer.a", "trailer.b")
            + _trailer("trailer.b", "trailer.a")
            + "}\n",
            "cycle",
        ),
    ],
)
def test_invalid_slave_graph_is_typed_and_leaves_source_intact(source: str, message: str) -> None:
    document = parse_sii(source)
    with pytest.raises(TrailerEditError, match=message):
        repair_trailer(document, "trailer.a")
    assert document.serialize() == source


def test_invalid_component_and_wheels_array_are_typed_and_transactional() -> None:
    document = parse_sii(SOURCE)
    with pytest.raises(TrailerEditError, match="unsupported"):
        repair_trailer_component(document, "trailer.one", "tire")  # type: ignore[arg-type]
    assert document.serialize() == SOURCE

    inconsistent = SOURCE.replace("wheels_wear: 2", "wheels_wear: 3", 1)
    broken = parse_sii(inconsistent)
    with pytest.raises(TrailerEditError, match="inconsistent"):
        repair_trailer(broken, "trailer.one")
    assert broken.serialize() == inconsistent
