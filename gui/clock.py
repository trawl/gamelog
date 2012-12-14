#!/usr/bin/python
# -*- coding: utf-8 -*-

try:
    from PySide import QtCore,QtGui
    QtGui.QFileDialog.getOpenFileNameAndFilter = QtGui.QFileDialog.getOpenFileName
except ImportError as error:
    from PyQt4 import QtCore,QtGui
    QtCore.Signal = QtCore.pyqtSignal
    QtCore.Slot = QtCore.pyqtSlot

class GameClock(QtGui.QLCDNumber):
    
    def __init__(self,parent=None):
        super(GameClock,self).__init__(parent)
        self.setSegmentStyle(QtGui.QLCDNumber.Filled)
        self.time = QtCore.QTime(0,0,0)
        self.timer = QtCore.QTimer(self)
        self.timer.start(1000)
        self.setNumDigits(5)
        self.showTime()
        

        QtCore.QObject.connect(self.timer, QtCore.SIGNAL('timeout()'), self.showTime)
     
        
    def showTime(self):
        
        self.time = self.time.addSecs(1)
        text = self.time.toString("hh:mm:ss")
        if self.time.hour(): self.setNumDigits(8)
        self.display(text)
        
    def stopTimer(self):
        self.timer.stop()
        