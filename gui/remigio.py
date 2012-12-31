#!/usr/bin/env python
# -*- coding: utf-8 -*-

import random

try:
    from PySide import QtCore,QtGui
    QtGui.QFileDialog.getOpenFileNameAndFilter = QtGui.QFileDialog.getOpenFileName
except ImportError as error:
    from PyQt4 import QtCore,QtGui
    QtCore.Signal = QtCore.pyqtSignal
    QtCore.Slot = QtCore.pyqtSlot

from controllers.remigioengine import RemigioEngine
from gui.game import GameWidget
from gui.message import ErrorMessage
from gui.clock import GameClock

class RemigioWidget(GameWidget):

    def __init__(self, game, players, parent=None):
        super(RemigioWidget, self).__init__(game,players,parent)
        self.initUI()

    def createEngine(self):
        if self.game != 'Remigio':
            raise Exception("No engine for game {}".format(self.game))
            return
        self.engine = RemigioEngine()     

    def initUI(self):
        self.mainlayout = QtGui.QGridLayout(self)
        self.buttonGroup=QtGui.QGroupBox(self)
        self.buttonGroup.setTitle("Ronda {}".format(str(self.engine.getNumRound())))
        self.buttonGroup.setStyleSheet("QGroupBox { font-size: 18px; font-weight: bold; }")
        
        self.mainlayout.addWidget(self.buttonGroup,0,0)
        self.buttonGroupLayout= QtGui.QHBoxLayout(self.buttonGroup)

        self.cancelMatchButton = QtGui.QPushButton("&Finalizar Partida", self.buttonGroup)
        self.buttonGroupLayout.addWidget(self.cancelMatchButton)
        self.cancelMatchButton.clicked.connect(self.cancelMatch)

    