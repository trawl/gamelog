#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Python generic imports
import sys

try:
    from PySide import QtGui
except ImportError as error:
    from PyQt4 import QtGui
    
# Program imports
from gui.mainwindow import MainWindow


if __name__ == "__main__":
    
#    db.connectDB()
    
    app = QtGui.QApplication(sys.argv)
    mw = MainWindow()
    mw.show()
    sys.exit(app.exec_())


