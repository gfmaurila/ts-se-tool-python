from PySide6.QtCore import QSettings

from tsse.config import AppSettings, GameRootStore
from tsse.core.profiles import Game


def test_defaults_do_not_target_user_documents(monkeypatch, tmp_path) -> None:
    monkeypatch.chdir(tmp_path)

    settings = AppSettings.defaults()

    assert settings.data_directory == tmp_path / "data"
    assert settings.log_level == "INFO"


def test_game_root_store_persists_ats_and_ets2(tmp_path) -> None:
    backend = QSettings(str(tmp_path / "settings.ini"), QSettings.Format.IniFormat)
    store = GameRootStore(backend)
    ats = tmp_path / "American Truck Simulator"
    ets = tmp_path / "Euro Truck Simulator 2"
    store.set_root(Game.ATS, ats)
    store.set_root(Game.ETS2, ets)

    restored = GameRootStore(
        QSettings(str(tmp_path / "settings.ini"), QSettings.Format.IniFormat)
    )
    assert restored.get_root(Game.ATS) == ats
    assert restored.get_root(Game.ETS2) == ets


def test_game_root_store_clear_restores_automatic_fallback(tmp_path) -> None:
    backend = QSettings(str(tmp_path / "settings.ini"), QSettings.Format.IniFormat)
    store = GameRootStore(backend)
    store.set_root(Game.ATS, tmp_path / "custom")
    store.clear_root(Game.ATS)
    assert store.get_root(Game.ATS) is None
