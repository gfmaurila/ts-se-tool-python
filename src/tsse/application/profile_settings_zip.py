"""Safe import/export of the legacy profile-settings ZIP contract."""

from __future__ import annotations

import os
import shutil
import tempfile
import uuid
import zipfile
from pathlib import Path

_EXACT = frozenset({"config.cfg", "config_local.cfg", "controls.sii"})
_MAX_ENTRIES = 64
_MAX_BYTES = 32 * 1024 * 1024


class ProfileSettingsZipError(RuntimeError):
    """A settings archive is invalid or could not be safely transferred."""


def _allowed(name: str) -> bool:
    return name in _EXACT or (name.startswith("gearbox_") and name.endswith(".sii"))


def _selected(profile: Path, names: list[str]) -> list[Path]:
    files = []
    for name in names:
        if not _allowed(name) or Path(name).name != name:
            raise ProfileSettingsZipError(f"unsupported settings file: {name}")
        path = profile / name
        if not path.is_file():
            raise ProfileSettingsZipError(f"settings file not found: {path}")
        files.append(path)
    if not files:
        raise ProfileSettingsZipError("no settings files selected")
    return files


class ProfileSettingsZip:
    """Port the legacy root-basename ZIP format with safe staging."""

    def export(self, profile: Path, destination: Path, names: list[str]) -> Path:
        files = _selected(profile, names)
        temporary = destination.with_name(f".{destination.name}.{uuid.uuid4().hex}.tmp")
        try:
            with zipfile.ZipFile(temporary, "x", zipfile.ZIP_DEFLATED) as archive:
                for file in files:
                    archive.write(file, file.name)
            with zipfile.ZipFile(temporary) as archive:
                if set(archive.namelist()) != {file.name for file in files}:
                    raise ProfileSettingsZipError("staged ZIP validation failed")
                if archive.testzip() is not None:
                    raise ProfileSettingsZipError("staged ZIP is corrupt")
            os.replace(temporary, destination)
        except (OSError, zipfile.BadZipFile) as error:
            raise ProfileSettingsZipError(f"could not export settings: {error}") from error
        finally:
            if temporary.exists():
                temporary.unlink()
        return destination

    def import_(self, archive_path: Path, profile: Path, names: list[str]) -> tuple[Path, ...]:
        wanted = set(_selected_names(names))
        if not profile.is_dir():
            raise ProfileSettingsZipError(f"profile directory not found: {profile}")
        stage = Path(tempfile.mkdtemp(prefix="tsse-settings-", dir=profile.parent))
        backups: list[tuple[Path, Path]] = []
        try:
            with zipfile.ZipFile(archive_path) as archive:
                infos = archive.infolist()
                if len(infos) > _MAX_ENTRIES or sum(info.file_size for info in infos) > _MAX_BYTES:
                    raise ProfileSettingsZipError("ZIP exceeds defensive limits")
                present = {info.filename for info in infos}
                if not wanted <= present:
                    raise ProfileSettingsZipError("ZIP lacks a selected settings file")
                for info in infos:
                    self._validate_entry(info.filename, stage)
                    if info.filename in wanted:
                        target = stage / info.filename
                        target.parent.mkdir(parents=True, exist_ok=True)
                        with archive.open(info) as src, target.open("xb") as dst:
                            shutil.copyfileobj(src, dst)
            for name in wanted:
                staged, target = stage / name, profile / name
                backup = profile / f".{name}.tsse-import-{uuid.uuid4().hex}.bak"
                if target.exists():
                    shutil.copy2(target, backup)
                    backups.append((target, backup))
                os.replace(staged, target)
            return tuple(profile / name for name in sorted(wanted))
        except (OSError, zipfile.BadZipFile) as error:
            for target, backup in reversed(backups):
                if backup.exists():
                    os.replace(backup, target)
            raise ProfileSettingsZipError(f"could not import settings: {error}") from error
        finally:
            shutil.rmtree(stage, ignore_errors=True)

    @staticmethod
    def _validate_entry(name: str, stage: Path) -> None:
        normalized = name.replace("\\", "/")
        if not _allowed(normalized) or normalized != Path(normalized).name:
            raise ProfileSettingsZipError(f"unsafe or unsupported ZIP entry: {name}")
        target = (stage / normalized).resolve()
        if not target.is_relative_to(stage.resolve()):
            raise ProfileSettingsZipError(f"ZIP entry escapes staging: {name}")


def _selected_names(names: list[str]) -> list[str]:
    if not names or any(not _allowed(name) or Path(name).name != name for name in names):
        raise ProfileSettingsZipError("invalid settings selection")
    return names
