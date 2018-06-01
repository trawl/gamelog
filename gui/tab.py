#!/usr/bin/env python
# -*- coding: utf-8 -*-

from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import QWidget


class Tab(QWidget):

    closeRequested = pyqtSignal(QWidget)
    restartRequested = pyqtSignal(QWidget)

    def __init__(self, parent=None):
        super(Tab, self).__init__(parent)

    def requestClose(self):
        self.closeRequested.emit(self)

    def requestRestart(self):
        self.restartRequested.emit(self)
