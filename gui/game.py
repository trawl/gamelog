#!/usr/bin/env python
# -*- coding: utf-8 -*-

try:
    from PySide import QtCore,QtGui
    QtGui.QFileDialog.getOpenFileNameAndFilter = QtGui.QFileDialog.getOpenFileName
except ImportError as error:
    from PyQt4 import QtCore,QtGui
    QtCore.Signal = QtCore.pyqtSignal
    QtCore.Slot = QtCore.pyqtSlot

class GameWidget(QtGui.QWidget):
    
    closeRequested = QtCore.Signal(QtGui.QWidget)

    def __init__(self, game, players, parent=None):
        super(GameWidget, self).__init__(parent)
        self.game = game
        self.players=players
        self.createEngine()  
        for nick in players:
            self.engine.addPlayer(nick)
        self.engine.setDealingPolicy(self.engine.RRDealer)
        self.engine.begin()
        self.engine.printStats()
        
    def createEngine(self): pass
    
    
    def cancelMatch(self):
        ret = QtGui.QMessageBox.question(self, QtGui.QApplication.translate("GameWidget",'Cancel Match'),
        QtGui.QApplication.translate("GameWidget","Are you sure you want to cancel this match?"), QtGui.QMessageBox.Yes | 
        QtGui.QMessageBox.No, QtGui.QMessageBox.No)
        
        if ret == QtGui.QMessageBox.No: return
        self.closeMatch()
        self.closeRequested.emit(self)   
        
    def closeMatch(self):
        self.engine.cancelMatch()
     
