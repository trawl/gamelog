#!/usr/bin/env python3
import ctypes
import os
import sys

import resources_rc  # noqa: F401
from core.logging_config import configure_logging
from games import load_builtin_games

# Register game metadata before the UI imports initialize application settings.
load_builtin_games()

# Resolve the log level from GAMELOG_LOG_LEVEL / the saved setting / default.
configure_logging()

from core.ui.gamelogapplication import GamelogApplication  # noqa: E402
from core.ui.languagechooser import LanguageManager  # noqa: E402
from core.ui.mainwindow import MainWindow  # noqa: E402
from core.ui.thememanager import ThemeManager  # noqa: E402

if __name__ == "__main__":
    if sys.platform.startswith("win"):
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("GameLog")
    # Disable output on windows when using pythonw to avoid filling buffers
    if os.path.basename(sys.executable) == "pythonw.exe":
        f = open(os.devnull, "w")  # noqa: SIM115
        sys.stdout = f
        sys.stderr = f

    app = GamelogApplication(sys.argv)
    app.setDesktopFileName("gamelog")
    app.setApplicationName("gamelog")

    if sys.platform == "darwin":
        from PySide6.QtGui import QIcon
        app.setWindowIcon(QIcon(":/icons/cards.png"))

    app.languageManager = LanguageManager(app)
    app.themeManager = ThemeManager(app)
    mw = MainWindow()
    sys.exit(app.exec())
