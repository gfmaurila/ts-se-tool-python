import tsse


def test_package_exports_settings() -> None:
    assert tsse.AppSettings.__name__ == "AppSettings"
