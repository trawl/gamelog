#!/usr/bin/env python
# -*- coding: utf-8 -*-

import ctypes
import os
import sys

from PySide6.QtCore import QLocale, QTranslator
from PySide6.QtWidgets import QApplication

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
    # Default to system language, fallback to English if not available
    qt_translator = QTranslator()
    translator = QTranslator()
    if translator.load(QLocale.system().name(), "i18n/"):
        qt_translator.load("i18n/qtbase_" + QLocale.system().name())
    else:
        translator.load("i18n/en_GB")
        qt_translator.load("i18n/qtbase_en")
    #    app.setStyle(QStyleFactory.create("plastique"))
    app.installTranslator(qt_translator)
    app.installTranslator(translator)
    app.setDesktopFileName("gamelog")

    mw = MainWindow(translator, qt_translator)
    sys.exit(app.exec())
