#!/usr/bin/env python
# -*- coding: utf-8 -*-

import ctypes
import os
import sys

from PySide6.QtWidgets import QApplication

from gui.languagechooser import LanguageManager
from gui.mainwindow import MainWindow

if __name__ == "__main__":
    if sys.platform.startswith("win"):
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("GameLog")
    # Disable output on windows when using pythonw to avoid filling buffers
    if os.path.basename((sys.executable)) == "pythonw.exe":
        f = open(os.devnull, "w")
        sys.stdout = f
        sys.stderr = f

    app = QApplication(sys.argv)
    try:
        with open("styles/main.qss", "r") as f:
            app.setStyleSheet(f.read())
    except FileNotFoundError:
        pass

    app.setDesktopFileName("gamelog")

    app.languageManager = LanguageManager(app)  # pyright: ignore[reportAttributeAccessIssue]
    mw = MainWindow()
    sys.exit(app.exec())
