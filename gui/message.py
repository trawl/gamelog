#!/usr/bin/env python
# -*- coding: utf-8 -*-

try:
    from PySide import QtCore,QtGui
    QtGui.QFileDialog.getOpenFileNameAndFilter = QtGui.QFileDialog.getOpenFileName
except ImportError as error:
    from PyQt4 import QtCore,QtGui
    QtCore.Signal = QtCore.pyqtSignal
    QtCore.Slot = QtCore.pyqtSlot

class ErrorMessage(QtGui.QMessageBox):
    def __init__(self,message,title="Error",parent=None):
        super(ErrorMessage, self).__init__( parent)
        self.setText(message)
        self.setWindowTitle(title)
        self.setStandardButtons(QtGui.QMessageBox.Ok);
        self.setDefaultButton(QtGui.QMessageBox.Ok);
 
