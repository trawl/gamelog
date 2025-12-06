#!/usr/bin/env python
# -*- coding: utf-8 -*-

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QWidget


class Tab(QWidget):
    closeRequested = Signal(QWidget)
    restartRequested = Signal(QWidget)

    def __init__(self, parent=None):
        super(Tab, self).__init__(parent)

    def requestClose(self):
        self.closeRequested.emit(self)

    def requestRestart(self):
        self.restartRequested.emit(self)
