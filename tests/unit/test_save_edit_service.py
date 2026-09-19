from dataclasses import replace
from hashlib import sha256
from pathlib import Path

import pytest

from tsse.application.player_editor import set_skill
from tsse.application.save_edit_service import SaveEditService, SaveStructureError
from tsse.core.sii import DecodedSave, SaveFormat, UnsupportedSaveFormatError, parse_sii
from tsse.infrastructure.decoder import SiiDecoder
from tsse.infrastructure.filesystem import (
    AtomicReplaceError,
    BackupCreationError,
    SaveChangedError,
    SaveValidationError,
    save_io,
)

SOURCE = """SiiNunit
{
economy : economy.one {
 adr: 0
 unknown_future: keep
}
}
"""


def _write_save(directory: Path) -> tuple[Path, Path, Path, Path]:
    save = directory / "save"
    save.mkdir()
    game = save / "game.sii"
    info = save / "info.sii"
    profile = directory / "profile.sii"
    other = directory / "other-save.sii"
    game.write_text(SOURCE, encoding="utf-8")
    info.write_text("info untouched", encoding="utf-8")
    profile.write_text("profile untouched", encoding="utf-8")
    other.write_text("other untouched", encoding="utf-8")
    return game, info, profile, other


def _adr(document: object) -> str:
    economy = next(block for block in document.blocks if block.type_name == "economy")  # type: ignore[attr-defined]
    return next(field.value for field in economy.fields if field.key == "adr")


def _set_adr(document: object) -> object:
    return set_skill(document, "adr", 1)  # type: ignore[arg-type]


def test_siin_write_preserves_unrelated_files_and_unknown_fields(tmp_path: Path) -> None:
    game, info, profile, other = _write_save(tmp_path)
    original = game.read_bytes()

    result = SaveEditService().save(game, _set_adr, validate=lambda document: _adr(document) == "1")

    assert result.original_format is SaveFormat.PLAINTEXT
    assert result.original_sha256 == result.backup_sha256 == sha256(original).hexdigest()
    assert result.written_sha256 == sha256(game.read_bytes()).hexdigest()
    assert result.backup_path.read_bytes() == original
    assert game.read_text(encoding="utf-8").startswith("SiiNunit")
    assert _adr(parse_sii(game.read_text(encoding="utf-8"))) == "1"
    assert "unknown_future: keep" in game.read_text(encoding="utf-8")
    assert info.read_text() == "info untouched"
    assert profile.read_text() == "profile untouched"
    assert other.read_text() == "other untouched"
    assert not list(game.parent.glob(".game.sii.tsse-write-*.tmp"))


@pytest.mark.parametrize(
    ("header", "save_format"),
    [(b"ScsC opaque", SaveFormat.SCS_CONTAINER), (b"BSII opaque", SaveFormat.BINARY)],
)
def test_opaque_input_uses_decoder_adapter_and_returns_original_format(
    tmp_path: Path, header: bytes, save_format: SaveFormat
) -> None:
    game, *_ = _write_save(tmp_path)
    game.write_bytes(header)

    class FakeLegacy:
        def decode_file(self, source: Path) -> DecodedSave:
            assert source == game
            return DecodedSave(SOURCE.encode(), save_format)

    result = SaveEditService(SiiDecoder(FakeLegacy())).save(game, _set_adr)

    assert result.original_format is save_format
    assert game.read_bytes().startswith(b"SiiNunit")


def test_multiple_unique_backups_discovery_and_explicit_restore(tmp_path: Path) -> None:
    game, *_ = _write_save(tmp_path)
    service = SaveEditService()
    first = service.save(game, _set_adr)
    second = service.save(game, lambda document: set_skill(document, "adr", 2))

    backups = service.discover_backups(game)
    assert len(backups) == 2 and first.backup_path in backups and second.backup_path in backups
    restored = service.restore(game, first.backup_path)

    assert first.backup_path.exists() and second.backup_path.exists()
    assert restored.backup_path.exists()
    assert _adr(parse_sii(game.read_text(encoding="utf-8"))) == "0"


def test_rejects_malformed_empty_or_validation_failed_output_without_backup(tmp_path: Path) -> None:
    game, *_ = _write_save(tmp_path)
    service = SaveEditService()
    original = game.read_bytes()

    with pytest.raises(SaveStructureError):
        service.save(game, lambda document: replace(document, source=""))
    with pytest.raises(ValueError, match="caller validation"):
        service.save(
            game,
            _set_adr,
            validate=lambda _: (_ for _ in ()).throw(ValueError("caller validation")),
        )

    assert game.read_bytes() == original
    assert not service.discover_backups(game)


def test_concurrent_change_and_backup_failure_abort_without_replacement(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    game, *_ = _write_save(tmp_path)
    service = SaveEditService()

    def external_change(document: object) -> object:
        game.write_text(SOURCE.replace("adr: 0", "adr: 9"), encoding="utf-8")
        return _set_adr(document)

    with pytest.raises(SaveChangedError):
        service.save(game, external_change)
    assert _adr(parse_sii(game.read_text())) == "9"

    game.write_text(SOURCE, encoding="utf-8")
    monkeypatch.setattr(
        save_io.shutil, "copy2", lambda *_: (_ for _ in ()).throw(OSError("backup fail"))
    )
    with pytest.raises(BackupCreationError):
        service.save(game, _set_adr)
    assert game.read_text() == SOURCE


def test_replace_failure_preserves_backup_and_invalid_restore_is_rejected(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    game, *_ = _write_save(tmp_path)
    service = SaveEditService()
    monkeypatch.setattr(
        save_io.os, "replace", lambda *_: (_ for _ in ()).throw(OSError("replace fail"))
    )

    with pytest.raises(AtomicReplaceError):
        service.save(game, _set_adr)
    assert game.read_text() == SOURCE
    backup = next(game.parent.glob("game.sii.tsse-backup-*"))
    assert backup.read_text() == SOURCE

    invalid = game.parent / "game.sii.tsse-backup-invalid"
    invalid.write_bytes(b"")
    with pytest.raises(SaveValidationError):
        service.restore(game, invalid)


def test_malformed_input_is_not_written(tmp_path: Path) -> None:
    game, *_ = _write_save(tmp_path)
    game.write_bytes(b"not a recognized save")

    with pytest.raises(UnsupportedSaveFormatError):
        SaveEditService().save(game, _set_adr)
    assert game.read_bytes() == b"not a recognized save"
