import ctypes
import os
import sys

from PySide6.QtGui import QIcon

import core.resources_rc  # noqa: F401
from core.linux_desktop import install_desktop_entry
from core.logging_config import configure_logging
from games import load_builtin_games

load_builtin_games()
configure_logging()

from core.ui.app import GamelogApplication  # noqa: E402
from core.ui.language import LanguageManager  # noqa: E402
from core.ui.mainwindow import MainWindow  # noqa: E402
from core.ui.theme import ThemeManager  # noqa: E402


def main() -> None:
    if sys.platform.startswith("win"):
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("GameLog")
    if os.path.basename(sys.executable) == "pythonw.exe":
        f = open(os.devnull, "w")  # noqa: SIM115
        sys.stdout = f
        sys.stderr = f
    # Before any window exists: Linux shells resolve the taskbar icon via a
    # desktop entry matching setDesktopFileName() below, so give them one.
    install_desktop_entry()

    app = GamelogApplication(sys.argv)
    app.setDesktopFileName("gamelog")
    app.setApplicationName("gamelog")

    app.setWindowIcon(QIcon(":/icons/cards.png"))

    app.languageManager = LanguageManager(app)
    app.themeManager = ThemeManager(app)
    MainWindow()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
