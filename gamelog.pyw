#!/usr/bin/env python
# -*- coding: utf-8 -*-

import ctypes
import os
import sys

from PySide6.QtCore import QFile, QTextStream
from PySide6.QtWidgets import QApplication

import resources_rc  # noqa: F401
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
    file = QFile(":/styles/main.qss")
    if file.open(QFile.OpenModeFlag.ReadOnly | QFile.OpenModeFlag.Text):
        stream = QTextStream(file)
        app.setStyleSheet(stream.readAll())
        print("Loaded Style styles/main.qss")

    app.setDesktopFileName("gamelog")

    app.languageManager = LanguageManager(app)  # pyright: ignore[reportAttributeAccessIssue]
    mw = MainWindow()
    sys.exit(app.exec())
