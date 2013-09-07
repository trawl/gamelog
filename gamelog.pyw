#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Python generic imports
import sys
import os
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
        #Disable output on windows when using pythonw to avoid filling buffers
    if os.path.basename((sys.executable)) == "pythonw.exe":
        f=open(os.devnull,'w')
        sys.stdout=f
        sys.stderr=f    
    
    #Default to Spanish language    
    translator = QtCore.QTranslator()
    translator.load('i18n/es_ES')
    app = QtGui.QApplication(sys.argv)
#    app.setStyle(QtGui.QStyleFactory.create("plastique"))
    app.installTranslator(translator)
    mw = MainWindow()
    sys.exit(app.exec_())


