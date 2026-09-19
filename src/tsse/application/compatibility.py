"""Explicit game-version compatibility policy and read-only decoder diagnostics."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path

from tsse.core.profiles import Game
from tsse.core.sii import DecodeError, SaveFormat, SiiParseError, detect_save_format, parse_sii
from tsse.infrastructure.decoder import SiiDecoder


@dataclass(frozen=True, slots=True, order=True)
class GameVersion:
    """Opaque detected game version; no numeric ordering implies compatibility."""

    value: str


class CompatibilityStatus(StrEnum):
    VALIDATED = "validated"
    UNVALIDATED = "unvalidated"
    UNSUPPORTED = "unsupported"
    UNKNOWN = "unknown"


class CompatibilityWriteBlockedError(RuntimeError):
    """A save write was denied before decoding, backup, or staging."""


@dataclass(frozen=True, slots=True)
class DecoderCapabilities:
    can_read_siin: bool = True
    can_decode_scsc: bool = True
    can_decode_bsii: bool = True
    can_encode_scsc: bool = False
    can_encode_bsii: bool = False


@dataclass(frozen=True, slots=True)
class CompatibilityAssessment:
    game: Game
    version: GameVersion | None
    status: CompatibilityStatus
    unsafe_override: bool = False

    @property
    def write_allowed(self) -> bool:
        return self.status is CompatibilityStatus.VALIDATED or self.unsafe_override


class CompatibilityRegistry:
    """Exact-version registry: only explicit entries can grant write permission."""

    _validated = frozenset({(Game.ATS, "1.61"), (Game.ETS2, "1.61")})

    def assess(self, game: Game, version: GameVersion | None) -> CompatibilityAssessment:
        if version is None:
            return CompatibilityAssessment(game, None, CompatibilityStatus.UNKNOWN)
        status = (
            CompatibilityStatus.VALIDATED
            if (game, version.value) in self._validated
            else CompatibilityStatus.UNVALIDATED
        )
        return CompatibilityAssessment(game, version, status)

    @staticmethod
    def require_write(
        assessment: CompatibilityAssessment, *, unsafe_override: bool = False
    ) -> None:
        if assessment.write_allowed or unsafe_override:
            return
        raise CompatibilityWriteBlockedError(
            f"save write blocked: {assessment.game.value} "
            f"{assessment.version.value if assessment.version else 'unknown'} "
            f"is {assessment.status.value}"
        )


@dataclass(frozen=True, slots=True)
class SaveDiagnostic:
    game: Game
    version: GameVersion | None
    compatibility: CompatibilityStatus
    detected_format: SaveFormat
    decoder_available: bool
    decode_ok: bool
    parse_ok: bool
    block_count: int | None
    write_allowed: bool
    diagnostics: tuple[str, ...]


class SaveDiagnosticService:
    """Read-only format/decode/parse diagnostic; it never writes the source."""

    def __init__(
        self, decoder: SiiDecoder | None = None, registry: CompatibilityRegistry | None = None
    ) -> None:
        self._decoder = decoder or SiiDecoder()
        self._registry = registry or CompatibilityRegistry()

    def inspect(
        self, game: Game, game_sii: Path, version: GameVersion | None = None
    ) -> SaveDiagnostic:
        assessment = self._registry.assess(game, version)
        data = game_sii.read_bytes()
        detected = detect_save_format(data)
        if detected is SaveFormat.UNKNOWN:
            return self._result(assessment, detected, False, False, None, ("UNKNOWN FORMAT",))
        try:
            decoded = self._decoder.decode_file(game_sii)
        except DecodeError as error:
            return self._result(
                assessment, detected, False, False, None, (f"DECODER FAILED: {error}",)
            )
        try:
            document = parse_sii(decoded.data.decode("utf-8"))
        except (UnicodeDecodeError, SiiParseError) as error:
            return self._result(
                assessment, detected, True, False, None, (f"SII PARSE FAILED: {error}",)
            )
        return self._result(assessment, detected, True, True, len(document.blocks), ())

    @staticmethod
    def _result(
        assessment: CompatibilityAssessment,
        detected: SaveFormat,
        decode_ok: bool,
        parse_ok: bool,
        block_count: int | None,
        diagnostics: tuple[str, ...],
    ) -> SaveDiagnostic:
        return SaveDiagnostic(
            assessment.game,
            assessment.version,
            assessment.status,
            detected,
            True,
            decode_ok,
            parse_ok,
            block_count,
            assessment.write_allowed,
            diagnostics,
        )
