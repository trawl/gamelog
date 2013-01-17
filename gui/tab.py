#!/usr/bin/env python
# -*- coding: utf-8 -*-

try:
    from PySide import QtCore,QtGui
    QtGui.QFileDialog.getOpenFileNameAndFilter = QtGui.QFileDialog.getOpenFileName
except ImportError as error:
    from PyQt4 import QtCore,QtGui
    QtCore.Signal = QtCore.pyqtSignal
    QtCore.Slot = QtCore.pyqtSlot
    
class Tab(QtGui.QWidget):
    
    closeRequested = QtCore.Signal(QtGui.QWidget)
    
    def __init__(self, parent=None):
        super(Tab, self).__init__(parent)
    def requestClose(self):
        self.closeRequested.emit(self)   