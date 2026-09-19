"""One-save controlled SiiN write validation for explicitly named QA profiles."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
from datetime import datetime
from pathlib import Path

from tsse.application.player_editor import set_company_name
from tsse.core.sii import parse_sii
from tsse.core.sii.decoder import detect_save_format
from tsse.infrastructure.decoder import SiiDecoder


_QA = {
    "ats": (Path(r"D:\Work\American Truck Simulator"), "545353455F544553545F415453", "TSSE_TEST_ATS", "TSSE QA ATS"),
    "ets2": (Path(r"D:\Work\Euro Truck Simulator 2"), "545353455F544553545F45545332", "TSSE_TEST_ETS2", "TSSE QA ETS2"),
}


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def _field(document: object, key: str) -> str:
    for block in document.blocks:  # type: ignore[attr-defined]
        if block.type_name == "user_profile":
            for field in block.fields:
                if field.key == key:
                    return field.value
    raise RuntimeError(f"missing user_profile.{key}")


def _unique_sibling(target: Path, label: str) -> Path:
    stamp = datetime.now().astimezone().strftime("%Y%m%dT%H%M%S%z")
    candidate = target.with_name(f"{target.name}.{label}-{stamp}")
    number = 1
    while candidate.exists():
        candidate = target.with_name(f"{target.name}.{label}-{stamp}-{number}")
        number += 1
    return candidate


def _fsync_file(path: Path) -> None:
    with path.open("rb") as stream:
        os.fsync(stream.fileno())


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("game", choices=sorted(_QA))
    args = parser.parse_args()
    root, encoded, profile_name, after = _QA[args.game]
    profile = (root / "profiles" / encoded).resolve()
    allowed = (root / "profiles" / encoded).resolve()
    if profile != allowed or not profile.is_dir():
        raise RuntimeError("authorized QA profile is absent")

    saves = sorted(path for path in (profile / "save").iterdir() if (path / "game.sii").is_file())
    allowed_saves = {"autosave", "autosave_job"}
    if {path.name for path in saves} - allowed_saves or not saves:
        raise RuntimeError("unexpected save selection; select manually")
    save = next((path for path in saves if path.name == "autosave"), None)
    if save is None or not (save / "info.sii").is_file():
        raise RuntimeError("autosave or info.sii is absent")
    game_sii = (save / "game.sii").resolve()
    if profile not in game_sii.parents:
        raise RuntimeError("target escaped QA profile")

    original = game_sii.read_bytes()
    original_sha = _sha256(game_sii)
    backup = _unique_sibling(game_sii, "tsse-backup")
    with backup.open("xb") as output:
        output.write(original)
        output.flush()
        os.fsync(output.fileno())
    backup_sha = _sha256(backup)
    if original_sha != backup_sha:
        raise RuntimeError("backup SHA-256 mismatch")

    decoded = SiiDecoder().decode_file(game_sii)
    document = parse_sii(decoded.data.decode("utf-8"))
    before = _field(document, "company_name")
    edited = set_company_name(document, after)
    staged_text = edited.serialize()
    reparsed = parse_sii(staged_text)
    if _field(reparsed, "company_name") != f'"{after}"':
        raise RuntimeError("staged company name validation failed")

    staging = _unique_sibling(game_sii, "tsse-staging")
    with staging.open("xb") as output:
        output.write(staged_text.encode("utf-8"))
        output.flush()
        os.fsync(output.fileno())
    staged = staging.read_bytes()
    if not staged.startswith(b"SiiNunit"):
        raise RuntimeError("staging is not SiiN plaintext")
    if _field(parse_sii(staged.decode("utf-8")), "company_name") != f'"{after}"':
        raise RuntimeError("staged reparse/domain validation failed")
    if game_sii.read_bytes() != original:
        raise RuntimeError("ABORTED: concurrent modification detected")

    os.replace(staging, game_sii)
    _fsync_file(game_sii)
    current = game_sii.read_bytes()
    post = parse_sii(current.decode("utf-8"))
    if not current.startswith(b"SiiNunit") or _field(post, "company_name") != f'"{after}"':
        raise RuntimeError("post-write validation failed")
    print(json.dumps({
        "game": args.game,
        "profile": profile_name,
        "profile_directory": str(profile),
        "save_directory": str(save),
        "game_sii": str(game_sii),
        "info_sii": str(save / "info.sii"),
        "original_format": detect_save_format(original).value,
        "backup": str(backup),
        "original_sha256": original_sha,
        "backup_sha256": backup_sha,
        "field": "user_profile.company_name",
        "before": before,
        "after": f'"{after}"',
        "staging": str(staging),
        "modified_sha256": _sha256(game_sii),
    }, indent=2))


if __name__ == "__main__":
    main()
