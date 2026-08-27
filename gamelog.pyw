#!/usr/bin/env python3
import ctypes
import os
import sys

import resources_rc  # noqa: F401
from games import load_builtin_games

# Register game metadata before the UI imports initialize application settings.
load_builtin_games()

from gui.gamelogapplication import GamelogApplication
from gui.languagechooser import LanguageManager
from gui.mainwindow import MainWindow
from gui.thememanager import ThemeManager

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

    app.languageManager = LanguageManager(app)
    app.themeManager = ThemeManager(app)
    mw = MainWindow()
    sys.exit(app.exec())
