#!/usr/bin/env python
# -*- coding: utf-8 -*-


from PyQt5 import QtCore,QtGui,QtWidgets
QtCore.Signal = QtCore.pyqtSignal
QtCore.Slot = QtCore.pyqtSlot

    
class Tab(QtWidgets.QWidget):
    
    closeRequested = QtCore.Signal(QtWidgets.QWidget)
    
    def __init__(self, parent=None):
        super(Tab, self).__init__(parent)
    def requestClose(self):
        self.closeRequested.emit(self)   