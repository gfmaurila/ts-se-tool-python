"""Isolated adapter for the legacy SII_Decrypt command-line program."""

from __future__ import annotations

import shutil
import subprocess
import tempfile
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from tsse.core.sii import DecodedSave, DecodeError, PlaintextDecoder, SaveFormat, detect_save_format


class SiiDecryptError(DecodeError):
    """Base failure while invoking the separately packaged legacy program."""


class SiiDecryptNotFoundError(SiiDecryptError):
    """Raised when no legacy decoder executable is available."""


class SiiDecryptProcessError(SiiDecryptError):
    """Raised when the legacy program returns a non-zero exit status."""



class SiiDecryptOutputError(SiiDecryptError):
    """Raised when the legacy program did not produce valid SiiN text."""


@dataclass(frozen=True, slots=True)
class SiiDecryptResult:
    """Diagnostic information retained only for callers that need it."""

    stdout: str
    stderr: str
    returncode: int


Runner = Callable[[list[str], Path], subprocess.CompletedProcess[str]]


def _run(arguments: list[str], working_directory: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        arguments, cwd=working_directory, check=False, capture_output=True,
        text=True, encoding="utf-8", errors="replace",
    )


class LegacySiiDecryptAdapter:
    """Use SII_Decrypt.exe only on a copied input in a private temp directory."""

    def __init__(
        self,
        executable: Path | None = None,
        runner: Runner = _run,
        temp_root: Path | None = None,
    ) -> None:
        self._executable = executable or Path(__file__).with_name("resources") / "SII_Decrypt.exe"
        self._runner = runner
        self._temp_root = temp_root
        self.last_result: SiiDecryptResult | None = None

    def decode_file(self, source: Path) -> DecodedSave:
        """Decode *source* without ever passing its path to the legacy executable."""
        if not self._executable.is_file():
            raise SiiDecryptNotFoundError(f"SII_Decrypt.exe not found: {self._executable}")
        if not source.is_file():
            raise SiiDecryptError(f"save file not found: {source}")
        if self._temp_root is not None:
            self._temp_root.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(
            prefix="tsse-sii-decrypt-", dir=self._temp_root
        ) as temporary:
            workdir = Path(temporary)
            copied_executable = workdir / "SII_Decrypt.exe"
            copied_input = workdir / "game.sii"
            output = workdir / "game.sii.decoded"
            shutil.copy2(self._executable, copied_executable)
            shutil.copy2(source, copied_input)
            # The legacy Pascal parser consumes ``System.CmdLine``.  Launching
            # through cmd.exe with relative names is its documented stable path;
            # input and executable are both private copies in ``workdir``.
            completed = self._runner(
                [
                    "cmd.exe",
                    "/d",
                    "/s",
                    "/c",
                    r".\SII_Decrypt.exe -i game.sii -o game.sii.decoded",
                ],
                workdir,
            )
            self.last_result = SiiDecryptResult(
                completed.stdout, completed.stderr, completed.returncode
            )
            if completed.returncode != 0:
                raise SiiDecryptProcessError(
                    f"SII_Decrypt.exe failed with exit code {completed.returncode}: "
                    f"{completed.stderr or completed.stdout}"
                )
            if not output.is_file():
                raise SiiDecryptOutputError("SII_Decrypt.exe produced no output file")
            data = output.read_bytes()
            if detect_save_format(data) is not SaveFormat.PLAINTEXT:
                raise SiiDecryptOutputError("SII_Decrypt.exe output is not SiiN plaintext")
            return DecodedSave(data=data, source_format=SaveFormat.SCS_CONTAINER)


class SiiDecoder:
    """File-level decoder: direct SiiN path, legacy adapter for opaque formats."""

    def __init__(self, legacy: LegacySiiDecryptAdapter | None = None) -> None:
        self._legacy = legacy or LegacySiiDecryptAdapter()

    def decode_file(self, source: Path) -> DecodedSave:
        data = source.read_bytes()
        if detect_save_format(data) is SaveFormat.PLAINTEXT:
            return PlaintextDecoder().decode(data)
        return self._legacy.decode_file(source)
