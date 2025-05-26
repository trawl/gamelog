#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import os
import ctypes
import platform
try:
    from PySide6.QtCore import QTranslator, QLibraryInfo, QLocale, Qt
    from PySide6.QtGui import QPalette
    from PySide6.QtWidgets import QApplication
    pyside6 = True
except ImportError:
    from PyQt5.QtCore import QTranslator, QLibraryInfo, QLocale, Qt
    from PyQt5.QtGui import QPalette
    from PyQt5.QtWidgets import QApplication
    pyside6 = False
from gui.mainwindow import MainWindow

if __name__ == "__main__":
    try:
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(
            'GameLog')
    except Exception:
        pass
    # Disable output on windows when using pythonw to avoid filling buffers
    if os.path.basename((sys.executable)) == "pythonw.exe":
        f = open(os.devnull, 'w')
        sys.stdout = f
        sys.stderr = f

    app = QApplication(sys.argv)
    # Default to system language, fallback to Spanish if not available
    qt_translator = QTranslator()
    qt_translator.load('i18n/qtbase_ca')

    translator = QTranslator()
    if translator.load(QLocale.system().name(), 'i18n/'):
        qt_translator.load('i18n/qtbase_' + QLocale.system().name())
    else:
        translator.load('i18n/es_ES')
        qt_translator.load('i18n/qtbase_es')
#    app.setStyle(QStyleFactory.create("plastique"))
    app.installTranslator(qt_translator)
    app.installTranslator(translator)
    app.setDesktopFileName("gamelog")

    mw = MainWindow(translator, qt_translator)
    if pyside6:
        sys.exit(app.exec())
    else:
        # Deprecated
        sys.exit(app.exec_())
