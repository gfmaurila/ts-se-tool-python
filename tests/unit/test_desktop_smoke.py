import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from tsse.desktop.main import create_window


def test_main_window_smoke(tmp_path) -> None:
    application = QApplication.instance() or QApplication([])

    window = create_window(tmp_path / "Documents")

    assert window.windowTitle() == "TS SE Tool Python"
    assert window.game.count() == 2
    assert window.profile.count() == 0
    window.close()
    assert application is not None
