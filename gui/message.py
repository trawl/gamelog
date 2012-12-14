#!/usr/bin/python
# -*- coding: utf-8 -*-
import sys
from PyQt4 import QtCore, QtGui

class ErrorMessage(QtGui.QMessageBox):
    def __init__(self,message,title="Error",parent=None):
        super(ErrorMessage, self).__init__( parent)
        self.setText(message)
        self.setWindowTitle(title)
        self.setStandardButtons(QtGui.QMessageBox.Ok);
        self.setDefaultButton(QtGui.QMessageBox.Ok);
 
