#!/usr/bin/env python
# -*- coding: utf-8 -*-

try:
    from PySide import QtCore,QtGui
    QtGui.QFileDialog.getOpenFileNameAndFilter = QtGui.QFileDialog.getOpenFileName
except ImportError as error:
    from PyQt4 import QtCore,QtGui
    QtCore.Signal = QtCore.pyqtSignal
    QtCore.Slot = QtCore.pyqtSlot
    
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
        self.roundGroup.setTitle("{} {}".format(QtGui.QApplication.translate("GameWidget","Round"),str(self.engine.getNumRound())))
        self.pauseMatchButton.setText(QtGui.QApplication.translate("GameWidget","&Pause/Play"))
        self.cancelMatchButton.setText(QtGui.QApplication.translate("GameWidget","&Cancel Match"))
        self.commitRoundButton.setText(QtGui.QApplication.translate("GameWidget","Commit &Round"))
        self.matchGroup.setTitle(QtGui.QApplication.translate("GameWidget","Match"))
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
        ret = QtGui.QMessageBox.question(self, QtGui.QApplication.translate("GameWidget",'Cancel Match'),
        unicode(QtGui.QApplication.translate("GameWidget","Do you want to save the current {} match?")).format(self.game), QtGui.QMessageBox.Yes | 
        QtGui.QMessageBox.No | QtGui.QMessageBox.Cancel, QtGui.QMessageBox.Cancel)
        
        if ret == QtGui.QMessageBox.Cancel: return
        if ret == QtGui.QMessageBox.No:
            self.closeMatch()
        else:
            self.engine.save()
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
                QtGui.QMessageBox.warning(self,self.game,unicode(QtGui.QApplication.translate("GameWidget","{0} score is not valid").format(player)))
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
    
    def checkPlayerScore(self,player,score): 
        if score >= 0: return True
        else: return False
        
    def updatePanel(self):
        self.gameInput.reset()
        self.dealerPolicyCheckBox.setEnabled(False)
        if self.engine.getWinner():
            self.pauseMatchButton.setDisabled(True)
            self.clock.stopTimer()
            self.commitRoundButton.setDisabled(True)
            self.updateGameStatusLabel()    
            self.gameInput.setDisabled(True)
        else:
            self.roundGroup.setTitle(unicode(QtGui.QApplication.translate("GameWidget","Round {0}")).format(str(self.engine.getNumRound())))           
    
    #To be implemented in subclasses
    def createEngine(self): pass
    
    def getPlayerExtraInfo(self,player):  return {}
    
    def unsetDealer(self): pass
    
    def setDealer(self): pass
    
     
class GameInputWidget(QtGui.QWidget):
    
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
        
        
