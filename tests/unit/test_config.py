from tsse.config import AppSettings


def test_defaults_do_not_target_user_documents(monkeypatch, tmp_path) -> None:
    monkeypatch.chdir(tmp_path)

    settings = AppSettings.defaults()

    assert settings.data_directory == tmp_path / "data"
    assert settings.log_level == "INFO"
