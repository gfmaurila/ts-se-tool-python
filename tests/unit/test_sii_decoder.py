from pathlib import Path

import pytest

from tsse.core.sii import (
    ExternalDecoderRequiredError,
    PlaintextDecoder,
    SaveFormat,
    UnsupportedSaveFormatError,
    detect_save_format,
)
from tsse.infrastructure.decoder import ExternalDecoder


def test_detects_observed_headers() -> None:
    assert detect_save_format(b"SiiNunit\r\n{") is SaveFormat.PLAINTEXT
    assert detect_save_format(b"ScsC\x00\x01") is SaveFormat.SCS_CONTAINER
    assert detect_save_format(b"3nK\x00") is SaveFormat.THREE_NK
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


def test_unknown_header_returns_typed_error() -> None:
    with pytest.raises(UnsupportedSaveFormatError, match="unrecognized"):
        PlaintextDecoder().decode(b"unknown")


def test_external_decoder_is_infrastructure_adapter() -> None:
    decoder = ExternalDecoder(lambda data: b"SiiNunit\r\n" + data)

    decoded = decoder.decode(b"ScsC\x00")

    assert decoded.data == b"SiiNunit\r\nScsC\x00"
    assert decoded.source_format is SaveFormat.SCS_CONTAINER
