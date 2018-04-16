#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Python generic imports
import sys
import os
import ctypes


from PyQt5 import QtCore,QtWidgets
QtCore.Signal = QtCore.pyqtSignal
QtCore.Slot = QtCore.pyqtSlot

    
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
    
    #Default to system language, fallback to Spanish if not available    
    translator = QtCore.QTranslator()
    if not translator.load(QtCore.QLocale.system().name(),'i18n/'):
        translator.load('i18n/es_ES')
    app = QtWidgets.QApplication(sys.argv)
#    app.setStyle(QtWidgets.QStyleFactory.create("plastique"))
    app.installTranslator(translator)
    mw = MainWindow()
    sys.exit(app.exec_())


