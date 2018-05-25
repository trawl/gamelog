#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import os
import ctypes
from PyQt5.QtCore import QTranslator, QLibraryInfo, QLocale
from PyQt5.QtWidgets import QApplication
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

    mw = MainWindow(translator, qt_translator)
    sys.exit(app.exec_())
