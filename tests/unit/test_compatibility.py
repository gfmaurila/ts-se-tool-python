from pathlib import Path

import pytest

from tsse.application.compatibility import (
    CompatibilityAssessment,
    CompatibilityRegistry,
    CompatibilityStatus,
    CompatibilityWriteBlockedError,
    GameVersion,
    SaveDiagnosticService,
)
from tsse.application.save_edit_service import SaveEditService
from tsse.core.profiles import Game
from tsse.core.sii import parse_sii


def test_registry_is_exact_and_never_assumes_future_versions() -> None:
    registry = CompatibilityRegistry()
    assert registry.assess(Game.ATS, GameVersion("1.61")).status is CompatibilityStatus.VALIDATED
    assert registry.assess(Game.ETS2, GameVersion("1.61")).status is CompatibilityStatus.VALIDATED
    assert registry.assess(Game.ATS, GameVersion("1.62")).status is CompatibilityStatus.UNVALIDATED
    assert registry.assess(Game.ETS2, GameVersion("9.99")).status is CompatibilityStatus.UNVALIDATED
    assert registry.assess(Game.ATS, None).status is CompatibilityStatus.UNKNOWN


@pytest.mark.parametrize(
    "assessment",
    [
        CompatibilityRegistry().assess(Game.ATS, GameVersion("1.62")),
        CompatibilityRegistry().assess(Game.ATS, None),
        CompatibilityAssessment(Game.ATS, GameVersion("0.1"), CompatibilityStatus.UNSUPPORTED),
    ],
)
def test_blocked_write_never_creates_persistent_artifacts(
    tmp_path: Path, assessment: CompatibilityAssessment
) -> None:
    target = tmp_path / "game.sii"
    target.write_text("SiiNunit\n{\neconomy : e {\n adr: 0\n}\n}\n", encoding="utf-8")
    original = target.read_bytes()
    with pytest.raises(CompatibilityWriteBlockedError):
        SaveEditService().save(target, lambda document: document, compatibility=assessment)
    assert target.read_bytes() == original
    assert not tuple(tmp_path.glob("*.tsse-backup-*"))


def test_diagnostics_handles_siin_unknown_format_and_unvalidated_read(tmp_path: Path) -> None:
    game = tmp_path / "game.sii"
    game.write_text("SiiNunit\n{\neconomy : e {\n adr: 0\n}\n}\n", encoding="utf-8")
    result = SaveDiagnosticService().inspect(Game.ATS, game, GameVersion("1.62"))
    assert result.compatibility is CompatibilityStatus.UNVALIDATED
    assert result.decode_ok and result.parse_ok and not result.write_allowed
    assert result.block_count == len(parse_sii(game.read_text(encoding="utf-8")).blocks)
    game.write_bytes(b"bad")
    unknown = SaveDiagnosticService().inspect(Game.ATS, game)
    assert unknown.diagnostics == ("UNKNOWN FORMAT",)
