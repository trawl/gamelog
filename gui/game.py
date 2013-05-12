#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import time

try:
    from PySide import QtCore,QtGui
    QtGui.QFileDialog.getOpenFileNameAndFilter = QtGui.QFileDialog.getOpenFileName
except ImportError as error:
    from PyQt4 import QtCore,QtGui
    QtCore.Signal = QtCore.pyqtSignal
    QtCore.Slot = QtCore.pyqtSlot
    
try:
    import matplotlib
    matplotlib.use('Qt4Agg')
    if 'PySide' in sys.modules: matplotlib.rcParams['backend.qt4']='PySide'
    from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas
    from matplotlib.figure import Figure

except ImportError: pass
    
from gui.tab import Tab
from gui.clock import GameClock
        

class GameWidget(Tab):

    def __init__(self, game, players, engine = None, parent=None):
        super(GameWidget, self).__init__(parent)
        self.game = game
        if engine is not None:
            self.engine = engine
            self.players = self.engine.getPlayers()
        else:
            self.players = players
            self.createEngine()  
            for nick in players: self.engine.addPlayer(nick)
            self.engine.begin()
        self.engine.printStats()
        self.gameInput = None
        self.finished = False
        self.initUI()
        
    def initUI(self):
        #Set up the main grid
        self.setStyleSheet("QGroupBox { font-size: 18px; font-weight: bold; }")
        self.widgetLayout = QtGui.QGridLayout(self)
        self.roundGroup = QtGui.QGroupBox(self)
        self.widgetLayout.addWidget(self.roundGroup,0,0)
        self.matchGroup = QtGui.QGroupBox(self)
        self.widgetLayout.addWidget(self.matchGroup,0,1)
         
        #Round Group
        self.roundLayout = QtGui.QVBoxLayout(self.roundGroup)
        self.buttonGroupLayout= QtGui.QHBoxLayout()
        self.roundLayout.addLayout(self.buttonGroupLayout)        
        
        self.cancelMatchButton = QtGui.QPushButton(self.roundGroup)
        self.buttonGroupLayout.addWidget(self.cancelMatchButton)
        self.cancelMatchButton.clicked.connect(self.cancelMatch)
        
        self.pauseMatchButton = QtGui.QPushButton(self.roundGroup)
        self.buttonGroupLayout.addWidget(self.pauseMatchButton)
        self.pauseMatchButton.clicked.connect(self.pauseMatch)

        self.commitRoundButton = QtGui.QPushButton(self.roundGroup)
        self.buttonGroupLayout.addWidget(self.commitRoundButton)
        self.commitRoundButton.clicked.connect(self.commitRound)

        self.gameStatusLabel = QtGui.QLabel(self.roundGroup)
        self.gameStatusLabel.setAlignment(QtCore.Qt.AlignCenter)
        self.roundLayout.addWidget(self.gameStatusLabel)
        
        #Match Group
        self.matchGroupLayout = QtGui.QVBoxLayout(self.matchGroup)
        
        self.clock = GameClock(self.engine.getGameSeconds(),self)
        self.clock.setMinimumHeight(100)
        self.matchGroupLayout.addWidget(self.clock)
        
        dpolicy = self.engine.getDealingPolicy()
        if (dpolicy != self.engine.NoDealer):
            self.dealerPolicyCheckBox = QtGui.QCheckBox(self.matchGroup)
            if self.engine.getDealingPolicy() == self.engine.WinnerDealer:
                self.dealerPolicyCheckBox.setChecked(True)
            else:
                self.dealerPolicyCheckBox.setChecked(False)
            self.dealerPolicyCheckBox.setStyleSheet("QCheckBox { font-size: 14px; font-weight: bold; }")
            self.dealerPolicyCheckBox.stateChanged.connect(self.changeDealingPolicy)
            self.dealerPolicyCheckBox.setDisabled(self.engine.getNumRound()>1)
            self.matchGroupLayout.addWidget(self.dealerPolicyCheckBox)
        
    def retranslateUI(self):
        try:
            self.roundGroup.setTitle("{} {}".format(QtGui.QApplication.translate("GameWidget","Round"),str(self.engine.getNumRound())))
        except AttributeError: pass
        self.pauseMatchButton.setText(QtGui.QApplication.translate("GameWidget","&Pause/Play"))
        self.cancelMatchButton.setText(QtGui.QApplication.translate("GameWidget","&Cancel Match"))
        self.commitRoundButton.setText(QtGui.QApplication.translate("GameWidget","Commit &Round"))
        self.matchGroup.setTitle(QtGui.QApplication.translate("GameWidget","Match"))
        if (self.engine.getDealingPolicy() != self.engine.NoDealer): 
            self.dealerPolicyCheckBox.setText(QtGui.QApplication.translate("GameWidget","Winner deals"))
        self.updateGameStatusLabel()
    
    def updateGameStatusLabel(self):
        self.gameStatusLabel.setStyleSheet("QLabel { font-size: 16px; font-weight:bold; color: red;}")    
        winner = self.engine.getWinner()
        if winner:
            self.gameStatusLabel.setText(unicode(QtGui.QApplication.translate("GameWidget","{} won this match!")).format(winner))
        elif self.engine.isPaused():
            self.gameStatusLabel.setText(QtGui.QApplication.translate("GameWidget","Game is paused"))
        else:
            self.gameStatusLabel.setText(QtGui.QApplication.translate("GameWidget",""))      
    
    def cancelMatch(self):
        if not self.isFinished():
            ret = QtGui.QMessageBox.question(self, QtGui.QApplication.translate("GameWidget",'Cancel Match'),
            unicode(QtGui.QApplication.translate("GameWidget","Do you want to save the current {} match?")).format(self.game), QtGui.QMessageBox.Yes | 
            QtGui.QMessageBox.No | QtGui.QMessageBox.Cancel, QtGui.QMessageBox.Cancel)
            
            if ret == QtGui.QMessageBox.Cancel: return
            if ret == QtGui.QMessageBox.No:
                self.closeMatch()
            else:
                self.saveMatch()
        self.requestClose()
        
    def pauseMatch(self):
        if self.engine.isPaused():
            self.clock.unpauseTimer()
            self.commitRoundButton.setEnabled(True)
            self.gameInput.setEnabled(True)
            self.engine.unpause()
        else:
            self.clock.pauseTimer()
            self.commitRoundButton.setDisabled(True)
            self.gameInput.setDisabled(True)
            self.engine.pause()
        self.updateGameStatusLabel()
            
    def commitRound(self):
        
        nround = self.engine.getNumRound()
        print("Opening round {}".format(nround))
        self.engine.openRound(nround)
        winner = self.gameInput.getWinner()
        if not winner:
            QtGui.QMessageBox.warning(self,self.game,unicode(QtGui.QApplication.translate("GameWidget","No winner selected")))
            return
        else:
            self.engine.setRoundWinner(winner)
        scores = self.gameInput.getScores()
        for player,score in scores.items():
            if not self.checkPlayerScore(player,score):
                QtGui.QMessageBox.warning(self,self.game,unicode(QtGui.QApplication.translate("GameWidget","{0} score is not valid")).format(player))
                return
            extras = self.getPlayerExtraInfo(player)
            if extras is None: return
            self.engine.addRoundInfo(player,score, extras)

        #Everything ok so far, let's confirm
        ret = QtGui.QMessageBox.question(self, QtGui.QApplication.translate("GameWidget",'Commit Round'),
        QtGui.QApplication.translate("GameWidget","Are you sure you want to commit the current round?"), QtGui.QMessageBox.Yes | 
        QtGui.QMessageBox.No, QtGui.QMessageBox.Yes)
        
        if ret == QtGui.QMessageBox.No: return

        # Once here, we can commit round
        self.unsetDealer()
        self.engine.commitRound()
        self.engine.printStats()
        self.updatePanel()
        if not self.engine.getWinner(): self.setDealer() 
    
    def changeDealingPolicy(self, *args, **kwargs):
        if self.dealerPolicyCheckBox.isChecked():
            self.engine.setDealingPolicy(self.engine.WinnerDealer)
        else:
            self.engine.setDealingPolicy(self.engine.RRDealer)
        
    def closeMatch(self): self.engine.cancelMatch()
    
    def saveMatch(self): self.engine.save()
        
    def checkPlayerScore(self,player,score): 
        if score >= 0: return True
        else: return False
        
    def updatePanel(self):
        self.gameInput.reset()
        try: self.dealerPolicyCheckBox.setEnabled(False)
        except AttributeError: pass
        if self.engine.getWinner():
            self.finished = True
            self.pauseMatchButton.setDisabled(True)
            self.clock.stopTimer()
            self.commitRoundButton.setDisabled(True)
            self.updateGameStatusLabel()    
            self.gameInput.setDisabled(True)
            
        else:
            try:
                nround = self.engine.getNumRound()
                self.roundGroup.setTitle(unicode(QtGui.QApplication.translate("GameWidget","Round {0}")).format(str(nround)))
            except AttributeError: pass
            
    def getGameName(self): return self.game        
    
    def isFinished(self): return self.finished
    
    #To be implemented in subclasses
    def createEngine(self): pass
    
    def getPlayerExtraInfo(self,player):  return {}
    
    def unsetDealer(self): pass
    
    def setDealer(self): pass
    
     
class GameInputWidget(QtGui.QWidget):
    
    enterPressed = QtCore.Signal()
    
    def __init__(self,engine,parent=None):
        super(GameInputWidget,self).__init__(parent)
        self.engine = engine
        self.winnerSelected = ""
        self.playerInputList = {}
            
    def getWinner(self):
        return self.winnerSelected
    
    def getScores(self):
        scores = {}
        for player,piw in self.playerInputList.items():
            scores[player] = piw.getScore()
        return scores
    
    def reset(self):
        self.winnerSelected = ""
        for piw in self.playerInputList.values():
            piw.reset()
    
    def changedWinner(self,winner):
        print("Changing winner to {}".format(winner))
        winner = str(winner)
        if self.winnerSelected != "":
            self.playerInputList[self.winnerSelected].reset()
        self.winnerSelected = winner
        
    def keyPressEvent(self,event):
        if (event.key() == QtCore.Qt.Key_Return):
            self.enterPressed.emit()
        return super(GameInputWidget,self).keyPressEvent(event)
        
        
class ScoreSpinBox(QtGui.QSpinBox):

    def valueFromText(self,text):
        if text == "": return self.minimum()
        else: return super(ScoreSpinBox,self).valueFromText(text)
        
    def textFromValue(self,value):
        if value == self.minimum(): return ""
        else: return super(ScoreSpinBox,self).textFromValue(value)        


class GameRoundPlot(QtGui.QWidget):

    def __init__(self,engine,parent=None):
        super(GameRoundPlot, self).__init__(parent)
        self.plotlibavailable = 'matplotlib' in sys.modules
#        self.plotlibavailable = False
        self.plotinited = False
        self.engine = engine
        self.parent = parent
        self.axiswidth = 0
        self.initUI()
        
    def initUI(self):
        self.widgetLayout = QtGui.QVBoxLayout(self)
        self.canvas = None
        if not self.isPlotLibAvailable():
            self.label = QtGui.QLabel(self)
            self.label.setAlignment(QtCore.Qt.AlignCenter)
            self.widgetLayout.addWidget(self.label)
        else: 
#            self.initPlot()
            self.initPlotThread = PlotThread()
            self.initPlotThread.initplot.connect(self.initPlot)
            self.initPlotThread.start()

    def initPlot(self):
        (r,g,b,_) = self.palette().color(self.backgroundRole()).getRgbF()
        self.figure = Figure(figsize=(200,200), dpi=72,facecolor=(r,g,b), edgecolor=(0,0,0))
        self.canvas = FigureCanvas(self.figure)
        self.widgetLayout.addWidget(self.canvas)
        self.plotinited = True
        self.initPlotThread.terminate()
            
    def retranslateUI(self):
        if not self.isPlotLibAvailable():
            self.label.setText(QtGui.QApplication.translate("GameRoundPlot","No plotting available"))
        else: self.retranslatePlot()
            
    def isPlotLibAvailable(self): return self.plotlibavailable
    
    def isPlotInited(self): return self.plotinited
        
    def updatePlot(self): pass
    
    def retranslatePlot(self): pass
        
        
class PlotThread(QtCore.QThread):
    
    initplot = QtCore.Signal()
    
    def __init__(self):
        QtCore.QThread.__init__(self)
        
    def __del__(self):
        self.wait()
    
    def run(self):
        time.sleep(0.5)
        self.initplot.emit()
