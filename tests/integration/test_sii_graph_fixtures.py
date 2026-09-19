from pathlib import Path

import pytest

from tsse.core.sii import ReferenceStatus, SiiGraph, parse_sii
from tsse.infrastructure.decoder import SiiDecoder


@pytest.mark.parametrize(
    "fixture, expected",
    [
        (
            Path("projeto_atual/ATS/67666D617572696C61202D207A657261646F/save/autosave/game.sii"),
            {"player", "economy", "company", "garage", "vehicle", "driver_ai", "job_offer_data"},
        ),
        (
            Path("projeto_atual/ETS/4D4150415F455453/save/autosave/game.sii"),
            {
                "player",
                "economy",
                "company",
                "garage",
                "vehicle",
                "trailer",
                "driver_ai",
                "job_offer_data",
            },
        ),
    ],
)
def test_real_fixture_graph_observes_known_legacy_relationships_without_mutation(
    fixture: Path, expected: set[str]
) -> None:
    original = fixture.read_bytes()
    document = parse_sii(SiiDecoder().decode_file(fixture).data.decode("utf-8"))
    graph = SiiGraph(document)

    assert expected <= {block.type_name for block in document.blocks}
    assert not any(block.unparsed_lines for block in document.blocks)
    assert document.serialize() == document.source
    assert parse_sii(document.serialize()).blocks == document.blocks
    assert fixture.read_bytes() == original

    economy = next(block for block in document.blocks if block.type_name == "economy")
    garages = graph.indexed_references(economy, "garages", "garage")
    assert garages
    assert any(graph.inspect(reference).status is ReferenceStatus.VALID for _, reference in garages)

    offers = next(
        (
            references
            for block in document.blocks
            if block.type_name == "company"
            if (references := graph.indexed_references(block, "job_offer", "job_offer_data"))
        ),
        (),
    )
    assert offers
    assert any(graph.inspect(reference).status is ReferenceStatus.VALID for _, reference in offers)
