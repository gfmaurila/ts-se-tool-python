import subprocess
from pathlib import Path

import pytest

from tsse.core.sii import (
    ExternalDecoderRequiredError,
    PlaintextDecoder,
    SaveFormat,
    ScsContainerDecoder,
    UnsupportedSaveFormatError,
    detect_save_format,
    parse_sii,
)
from tsse.infrastructure.decoder import (
    LegacySiiDecryptAdapter,
    SiiDecoder,
    SiiDecryptNotFoundError,
    SiiDecryptOutputError,
    SiiDecryptProcessError,
)


def test_detects_observed_headers() -> None:
    assert detect_save_format(b"SiiNunit\r\n{") is SaveFormat.PLAINTEXT
    assert detect_save_format(b"ScsC\x00\x01") is SaveFormat.SCS_CONTAINER
    assert detect_save_format(b"3nK\x00") is SaveFormat.THREE_NK
    assert detect_save_format(b"BSII\x00") is SaveFormat.BINARY
    assert detect_save_format(b"not-sii") is SaveFormat.UNKNOWN


def test_plaintext_decoder_preserves_plaintext_fixture_bytes() -> None:
    fixture = Path("samples/ETS/4D4150415F455453/save/autosave/game_TB_decrypted.sii")
    data = fixture.read_bytes()

    decoded = PlaintextDecoder().decode(data)

    assert decoded.data == data
    assert decoded.source_format is SaveFormat.PLAINTEXT


def test_opaque_fixture_returns_explicit_decoder_requirement() -> None:
    fixture = Path("samples/ETS/4D4150415F455453/profile.sii")

    with pytest.raises(ExternalDecoderRequiredError, match="scs-container"):
        PlaintextDecoder().decode(fixture.read_bytes())


@pytest.mark.parametrize(
    "fixture",
    [
        Path("projeto_atual/ATS/67666D617572696C61202D207A657261646F/save/autosave/game.sii"),
        Path("projeto_atual/ETS/4D4150415F455453/save/autosave/game.sii"),
    ],
)
def test_scs_decoder_decodes_copied_real_fixture_without_mutating_original(
    fixture: Path, tmp_path: Path
) -> None:
    original = fixture.read_bytes()
    copied_fixture = tmp_path / "game.sii"
    copied_fixture.write_bytes(original)

    decoded = ScsContainerDecoder().decode(copied_fixture.read_bytes())

    assert decoded.source_format is SaveFormat.SCS_CONTAINER
    # Both supplied 1.61 saves use the current BSII v3 inner payload.
    # This proves only the reversible ScsC envelope stage; BSII remains
    # explicit until its lossless decoder is implemented.
    assert decoded.data.startswith(b"BSII\x03\x00\x00\x00")
    assert fixture.read_bytes() == original


def test_unknown_header_returns_typed_error() -> None:
    with pytest.raises(UnsupportedSaveFormatError, match="unrecognized"):
        PlaintextDecoder().decode(b"unknown")


def test_siin_file_bypasses_legacy_executable(tmp_path: Path) -> None:
    source = tmp_path / "game.sii"
    source.write_bytes(b"SiiNunit\n{\n}\n")

    decoded = SiiDecoder(LegacySiiDecryptAdapter(tmp_path / "missing.exe")).decode_file(source)

    assert decoded.data == source.read_bytes()
    assert decoded.source_format is SaveFormat.PLAINTEXT


@pytest.mark.parametrize(
    "source",
    [
        Path("projeto_atual/ATS/67666D617572696C61202D207A657261646F/save/autosave/game.sii"),
        Path("projeto_atual/ETS/4D4150415F455453/save/autosave/game.sii"),
    ],
)
def test_real_fixture_decodes_bsii_type_07_and_preserves_original(source: Path) -> None:
    original = source.read_bytes()

    decoded = SiiDecoder().decode_file(source)

    assert decoded.data.startswith(b"SiiNunit")
    assert parse_sii(decoded.data.decode("utf-8")).blocks
    assert source.read_bytes() == original


def test_missing_decoder_is_typed_error(tmp_path: Path) -> None:
    source = tmp_path / "game.sii"
    source.write_bytes(b"ScsC")

    with pytest.raises(SiiDecryptNotFoundError):
        LegacySiiDecryptAdapter(tmp_path / "missing.exe").decode_file(source)


def test_process_error_output_error_and_temp_cleanup(tmp_path: Path) -> None:
    source = tmp_path / "game.sii"
    source.write_bytes(b"ScsC")
    executable = tmp_path / "SII_Decrypt.exe"
    executable.write_bytes(b"placeholder")
    seen: list[Path] = []

    def failing_runner(arguments: list[str], workdir: Path) -> subprocess.CompletedProcess[str]:
        seen.append(workdir)
        assert (workdir / "game.sii").read_bytes() == b"ScsC"
        return subprocess.CompletedProcess(arguments, 7, "", "decoder error")

    with pytest.raises(SiiDecryptProcessError, match="exit code 7"):
        LegacySiiDecryptAdapter(executable, failing_runner).decode_file(source)
    assert seen and not seen[0].exists()

    def no_output_runner(arguments: list[str], workdir: Path) -> subprocess.CompletedProcess[str]:
        return subprocess.CompletedProcess(arguments, 0, "", "")

    with pytest.raises(SiiDecryptOutputError, match="no output"):
        LegacySiiDecryptAdapter(executable, no_output_runner).decode_file(source)
