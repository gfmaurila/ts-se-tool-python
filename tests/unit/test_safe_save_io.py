from pathlib import Path

import pytest

from tsse.core.sii import parse_sii
from tsse.infrastructure.filesystem import SafeSaveWriter, SaveValidationError


@pytest.mark.parametrize("name", ["game.sii", "info.sii", "profile.sii"])
def test_staged_write_backups_reopens_and_preserves_unknown_fields(
    tmp_path: Path, name: str
) -> None:
    target = tmp_path / name
    original = "SiiNunit\n{\nthing : id {\n unknown_future: keep-me\n}\n}\n"
    replacement = "SiiNunit\n{\nthing : id {\n unknown_future: keep-me\n edited: yes\n}\n}\n"
    target.write_text(original, encoding="utf-8")

    result = SafeSaveWriter().write_text(target, replacement)

    assert result.backup.read_text(encoding="utf-8") == original
    assert target.read_text(encoding="utf-8") == replacement
    assert parse_sii(target.read_text(encoding="utf-8")).blocks[0].fields[0].value == "keep-me"
    assert not list(tmp_path.glob(f".{name}.tsse-write-*.tmp"))


def test_invalid_candidate_does_not_touch_original_or_create_backup(tmp_path: Path) -> None:
    target = tmp_path / "game.sii"
    original = "SiiNunit\n{\n}\n"
    target.write_text(original, encoding="utf-8")

    with pytest.raises(SaveValidationError):
        SafeSaveWriter().write_text(target, "not a save")

    assert target.read_text(encoding="utf-8") == original
    assert not list(tmp_path.glob("*.tsse-backup-*"))
