import pytest

from tsse.core.sii import (
    MalformedReferenceError,
    MissingReferenceTargetError,
    ReferenceStatus,
    SiiGraph,
    TypedUnitReference,
    WrongReferenceTypeError,
    parse_sii,
)

SOURCE = '''SiiNunit
{
player : player.one {
 assigned_truck: vehicle.one
 optional_truck: null
 malformed: "vehicle.one"
 quoted_name: "A \\"quoted\\" name"
 number: -42
 active: true
 token: company.alpha
 trucks[3]: vehicle.two
 trucks[1]: vehicle.one
 future_field: keep-me
}
vehicle : vehicle.one {
 accessories: 2
 accessories[0]: accessory.one
 accessories[1]: null
}
vehicle : vehicle.two {
}
vehicle_accessory : accessory.one {
}
future_block : opaque.id {
 unknown: value
}
}
'''


def _graph() -> SiiGraph:
    return SiiGraph(parse_sii(SOURCE))


def test_resolves_valid_null_missing_wrong_and_malformed_references() -> None:
    graph = _graph()
    player = graph.unit("player.one")
    valid = graph.inspect(graph.field_reference(player, "assigned_truck", "vehicle"))
    null = graph.inspect(graph.field_reference(player, "optional_truck", "vehicle"))
    missing = graph.inspect(TypedUnitReference.create("vehicle.absent", "vehicle"))
    wrong = graph.inspect(TypedUnitReference.create("vehicle.one", "trailer"))
    malformed = graph.inspect(graph.field_reference(player, "malformed", "vehicle"))

    assert valid.status is ReferenceStatus.VALID and valid.target == graph.unit("vehicle.one")
    assert null.status is ReferenceStatus.NULL and graph.resolve(null.reference) is None
    assert missing.status is ReferenceStatus.MISSING_TARGET
    assert wrong.status is ReferenceStatus.WRONG_TARGET_TYPE
    assert malformed.status is ReferenceStatus.MALFORMED
    with pytest.raises(MissingReferenceTargetError):
        graph.resolve(missing.reference)
    with pytest.raises(WrongReferenceTypeError):
        graph.resolve(wrong.reference)
    with pytest.raises(MalformedReferenceError):
        graph.resolve(malformed.reference)


def test_indexed_references_follow_chains_and_do_not_mutate_document() -> None:
    graph = _graph()
    player = graph.unit("player.one")
    before = graph.document.serialize()

    indexed = graph.indexed_references(player, "trucks", "vehicle")
    chain = graph.follow(player, ("assigned_truck", "vehicle"))

    assert [index for index, _ in indexed] == [1, 3]
    targets = [graph.resolve(reference) for _, reference in indexed]
    assert [target.identifier if target else None for target in targets] == [
        "vehicle.one",
        "vehicle.two",
    ]
    assert [block.identifier for block in chain] == ["player.one", "vehicle.one"]
    assert graph.document.serialize() == before


def test_preserves_unknown_blocks_fields_escaped_strings_numbers_and_tokens_round_trip() -> None:
    document = parse_sii(SOURCE)
    player = next(block for block in document.blocks if block.identifier == "player.one")

    values = {field.key: field.value for field in player.fields}
    assert values["quoted_name"] == '"A \\"quoted\\" name"'
    assert values["number"] == "-42"
    assert values["active"] == "true"
    assert values["token"] == "company.alpha"
    assert values["future_field"] == "keep-me"
    assert any(block.type_name == "future_block" for block in document.blocks)
    reparsed = parse_sii(document.serialize())
    assert reparsed.blocks == document.blocks
    assert reparsed.serialize() == SOURCE


def test_duplicate_identifiers_are_not_resolved_silently() -> None:
    document = parse_sii("SiiNunit\n{\nthing : same {\n}\nthing : same {\n}\n}\n")
    graph = SiiGraph(document)

    assert graph.inspect(TypedUnitReference.create("same")).status is ReferenceStatus.MISSING_TARGET
