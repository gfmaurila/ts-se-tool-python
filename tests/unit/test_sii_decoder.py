from pathlib import Path

import pytest

from tsse.core.sii import (
    ExternalDecoderRequiredError,
    PlaintextDecoder,
    SaveFormat,
    ScsContainerDecoder,
    UnsupportedSaveFormatError,
    detect_save_format,
)
from tsse.infrastructure.decoder import ExternalDecoder


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


def test_external_decoder_is_infrastructure_adapter() -> None:
    decoder = ExternalDecoder(lambda data: b"SiiNunit\r\n" + data)

    decoded = decoder.decode(b"ScsC\x00")

    assert decoded.data == b"SiiNunit\r\nScsC\x00"
    assert decoded.source_format is SaveFormat.SCS_CONTAINER
