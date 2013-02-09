#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Python generic imports
import sys
import ctypes

try:
    from PySide import QtGui,QtCore
except ImportError as error:
    from PyQt4 import QtGui,QtCore
    
# Program imports
from gui.mainwindow import MainWindow

if __name__ == "__main__":
    try: ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID('GameLog')
    except: pass
    #Default to Spanish language    
    translator = QtCore.QTranslator()
    translator.load('i18n/es_ES')
    app = QtGui.QApplication(sys.argv)
    app.installTranslator(translator)
    mw = MainWindow()
    sys.exit(app.exec_())


