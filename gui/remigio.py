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
        self.shuffler = random.choice(self.players)
        self.initUI()
        
    def createEngine(self):
        if self.game != 'Remigio':
            raise Exception("No engine for game {}".format(self.game))
            return
        self.engine = RemigioEngine()     

    def initUI(self):
#        self.mainLayout = QtGui.QHBoxLayout(self)
#        self.leftLayout = QtGui.QVBoxLayout()
#        self.rightLayout = QtGui.QVBoxLayout()
#        self.mainLayout.addLayout(self.leftLayout)
#        self.mainLayout.addLayout(self.rightLayout)
        self.mainLayout = QtGui.QGridLayout(self)
    
        self.buttonGroup=QtGui.QGroupBox(self)
        self.buttonGroup.setTitle("Ronda {}".format(str(self.engine.getNumRound())))
        self.buttonGroup.setStyleSheet("QGroupBox { font-size: 18px; font-weight: bold; }")

#        self.leftLayout.addWidget(self.buttonGroup)
        self.mainLayout.addWidget(self.buttonGroup,0,0)
        self.buttonGroupLayout= QtGui.QVBoxLayout(self.buttonGroup)
        self.buttonGroupSubLayout= QtGui.QHBoxLayout()
        self.buttonGroupLayout.addLayout(self.buttonGroupSubLayout)
        

        self.cancelMatchButton = QtGui.QPushButton("&Finalizar Partida", self.buttonGroup)
        self.buttonGroupSubLayout.addWidget(self.cancelMatchButton)
        self.cancelMatchButton.clicked.connect(self.cancelMatch)
        
        self.commitRoundButton = QtGui.QPushButton("Cerrar &Ronda", self.buttonGroup)
        self.buttonGroupSubLayout.addWidget(self.commitRoundButton)
        self.commitRoundButton.clicked.connect(self.commitRound)
        
        self.inputGroup = RemigioInputWidget(self.engine,self)
        self.buttonGroupLayout.addWidget(self.inputGroup)

        self.matchGroup = QtGui.QGroupBox(self)
        self.matchGroup.setTitle("Partida")
        self.matchGroup.setStyleSheet("QGroupBox { font-size: 18px; font-weight: bold; }")
#        self.rightLayout.addWidget(self.matchGroup)
        self.mainLayout.addWidget(self.matchGroup,0,1)
        
        self.matchGroupLayout = QtGui.QVBoxLayout(self.matchGroup)
        
        self.clock = GameClock(self)
        self.clock.setMinimumHeight(100)
        self.matchGroupLayout.addWidget(self.clock)
        
        self.configLayout = QtGui.QGridLayout()
        self.matchGroupLayout.addLayout(self.configLayout)
        self.topPointsLabel = QtGui.QLabel(self.matchGroup)
        self.topPointsLabel.setText("Puntos")
        self.topPointsLabel.setFixedWidth(35)
        self.configLayout.addWidget(self.topPointsLabel,0,0)
        
        self.topPointsLineEdit = QtGui.QLineEdit(self.matchGroup)
        self.topPointsLineEdit.setText(str(self.engine.getTop()))
        self.topPointsLineEdit.setValidator(QtGui.QIntValidator(0,10000,self.topPointsLineEdit))
        self.topPointsLineEdit.setFixedWidth(30)
        sp = QtGui.QSizePolicy(QtGui.QSizePolicy.Fixed,QtGui.QSizePolicy.Fixed)
        self.topPointsLineEdit.setSizePolicy(sp)
        self.topPointsLineEdit.textChanged.connect(self.changeTop)
        self.configLayout.addWidget(self.topPointsLineEdit,0,1)
        
        self.detailGroup = RemigioRoundsDetail(self.engine,self)
        self.detailGroup.setStyleSheet("QGroupBox { font-size: 18px; font-weight: bold; }")
#        self.leftLayout.addWidget(self.detailGroup)
        self.mainLayout.addWidget(self.detailGroup,1,0)        
        
        self.playerGroup = QtGui.QGroupBox(self)
#        self.rightLayout.addWidget(self.playerGroup)
        self.mainLayout.addWidget(self.playerGroup,1,1)
        self.playerGroup.setTitle("Marcador")
        self.playerGroup.setStyleSheet("QGroupBox { font-size: 18px; font-weight: bold; }")
        self.playersLayout = QtGui.QVBoxLayout(self.playerGroup)
        self.playersLayout.addStretch()
        self.playerGroupBox = {}
        for player in self.players:
            pw = RemigioPlayerWidget(player,self.playerGroup)
            if player == self.shuffler:
                pw.setShuffler()
            self.playersLayout.addWidget(pw)
            self.playerGroupBox[player] = pw
 
        self.playersLayout.addStretch()
        
    def commitRound(self):
        self.engine.openRound()
        winner = self.inputGroup.getWinner()
        if not winner:
            ErrorMessage("Debe haber un ganador").exec_()
            return
        else:
            self.engine.setRoundWinner(winner)
        c_type = self.inputGroup.getCloseType()
        scores = self.inputGroup.getScores()
        for player,score in scores.items():
            if score>=0 :
                self.engine.addRoundInfo(player,score, {'closeType':c_type})
            else:
                ErrorMessage(u"La puntuación de {} no es válida".format(player)).exec_()
                return

        #Everything ok so far, let's confirm
        ret = QtGui.QMessageBox.question(self, 'Cerrar Ronda',
        u"Estás seguro que quieres cerrar la ronda actual?", QtGui.QMessageBox.Yes | 
        QtGui.QMessageBox.No, QtGui.QMessageBox.Yes)
        
        if ret == QtGui.QMessageBox.No: return

        # Once here, we can commit round...
        #Shuffler
        self.engine.commitRound()
        self.engine.printStats()
        
        self.updatePanel()
        winner = self.engine.getWinner()
        if winner:
            self.clock.stopTimer()
            for player in self.players:
                self.inputGroup.setDisabled(True)
            ErrorMessage("{} ha ganado la partida.".format(winner),"Fin de la partida").exec_()
            self.commitRoundButton.setDisabled(True)
        else:
            self.playerGroupBox[self.shuffler].unsetShuffler()
            candidate = (self.players.index(self.shuffler) + 1)%len(self.players)
            player = self.players[candidate]
            while True:
                if not self.engine.isPlayerOff(player):
                    self.shuffler = player
                    break
                else:
                    candidate = (candidate + 1)%len(self.players)
                    player = self.players[candidate]
            
            self.playerGroupBox[self.shuffler].setShuffler()


    def updatePanel(self):
        self.inputGroup.reset()
        self.topPointsLineEdit.setReadOnly(True)
        
        if not self.engine.getWinner():
            self.buttonGroup.setTitle("Ronda {}".format(str(self.engine.getNumRound())))
            
        for player in self.players:
            score = self.engine.getScoreFromPlayer(player)
            self.playerGroupBox[player].updateDisplay(score)
            if self.engine.isPlayerOff(player):
                self.playerGroupBox[player].koPlayer()
                self.inputGroup.koPlayer(player)
        
        self.detailGroup.updateRound()
        
    def changeTop(self,newtop):
        try:
            newtop = int(newtop)    
            self.engine.setTop(newtop)
        except ValueError: pass
        
class RemigioInputWidget(QtGui.QWidget):
    def __init__(self,engine,parent=None):
        super(RemigioInputWidget,self).__init__(parent)
        self.engine = engine
        self.initUI()
        self.winnerSelected = ""

    def initUI(self):
        self.widgetLayout = QtGui.QVBoxLayout(self)
        
#        self.middleLayout = QtGui.QHBoxLayout()
#        self.widgetLayout.addLayout(self.middleLayout)
#        self.winnerLayout = QtGui.QGridLayout()
#        self.middleLayout.addLayout(self.winnerLayout)
#        self.middleLayout.addStretch()
#        
#        self.winnerLabel = QtGui.QLabel(self)
#        self.winnerLabel.setText("Ganador")
#        self.winnerLayout.addWidget(self.winnerLabel,0,0)
#    
##        
#        self.winnerCombo = QtGui.QComboBox(self)
#        self.winnerCombo.addItem("")
#        self.winnerCombo.addItems(self.engine.getListPlayers())
#        self.winnerCombo.currentIndexChanged.connect(self.changedWinner)
#        self.winnerLayout.addWidget(self.winnerCombo,0,1)
#        
#        self.typeLabel = QtGui.QLabel(self)
#        self.typeLabel.setText("Tipo")
#        self.winnerLayout.addWidget(self.typeLabel,1,0)
#    
#        self.typeCombo = QtGui.QComboBox(self)
#        self.typeCombo.addItems(['1x','2x','3x','4x'])
#        self.winnerLayout.addWidget(self.typeCombo,1,1)
        
        self.tableLayout = QtGui.QHBoxLayout()
        self.widgetLayout.addLayout(self.tableLayout)
        
        self.playerInputList = {}
        for player in self.engine.getListPlayers():
            self.playerInputList[player] = RemigioPlayerInputWidget(player, self)
            self.tableLayout.addWidget(self.playerInputList[player])
            self.playerInputList[player].winnerSet.connect(self.changedWinner)

            
    def getWinner(self):
        return self.winnerSelected
#        return self.winnerCombo.currentText()
    
    def getCloseType(self):
#        return self.typeCombo.currentIndex()+1
        try: return self.playerInputList[self.winnerSelected].getCloseType()
        except KeyError: return 0
    
    def getScores(self):
        scores = {}
        for player,piw in self.playerInputList.items():
            if not piw.isKo():
                scores[player] = piw.getScore()*self.getCloseType()
        return scores
    
    def reset(self):
        self.winnerSelected = ""
        for piw in self.playerInputList.values():
            piw.reset()
    
    def changedWinner(self,winner):
        winner = str(winner)
        if self.winnerSelected != "":
            self.playerInputList[self.winnerSelected].reset()
        self.winnerSelected = winner
            
    def koPlayer(self,player):
        self.playerInputList[player].setKo()
        
class RemigioPlayerInputWidget(QtGui.QWidget):
    
    winnerSet = QtCore.Signal(str)
    
    def __init__(self,player,parent=None):
        super(RemigioPlayerInputWidget, self).__init__(parent)
        self.player = player
        self.ko = False
        self.bgcolors = [0,0xCCFF99,0xFFFF99,0xFFCC99,0xFFCCFF]
        
        self.mainLayout = QtGui.QVBoxLayout(self)
        
        self.label = QtGui.QLabel(self)
        self.mainLayout.addWidget(self.label)
        self.label.setAutoFillBackground(False)
        self.label.setFrameShape(QtGui.QFrame.StyledPanel)
        self.label.setFrameShadow(QtGui.QFrame.Raised)
        self.label.setScaledContents(True)
        self.label.setAlignment(QtCore.Qt.AlignCenter)
        self.label.setWordWrap(False)
        
        self.scoreLineEdit = QtGui.QLineEdit(self)
        self.scoreLineEdit.setAlignment(QtCore.Qt.AlignCenter)
        self.mainLayout.addWidget(self.scoreLineEdit)
        self.reset()
    
    def reset(self):
        self.closeType = 0
        self.updatePanel()
        
    def increaseCloseType(self):
        self.closeType = (self.closeType)%4 + 1
        self.updatePanel()
        
    def updatePanel(self):
        
        text = "{}".format(self.player)
        css = ""
        if self.closeType > 0:
            text = text + "({}x)".format(self.closeType)
            css = "font-weight: bold; background-color {0:X}".format(self.bgcolors[self.closeType])
            self.scoreLineEdit.setText("0")
            self.scoreLineEdit.setDisabled(True)
        else:
            self.scoreLineEdit.setText("")
            self.scoreLineEdit.setEnabled(True)
        
        self.label.setText(text)
        self.label.setStyleSheet("QLabel {{ {} }}".format(css))
        
    def mousePressEvent(self, event):
        if not self.isWinner(): 
            self.winnerSet.emit(self.player)
        self.increaseCloseType()

        
    def isWinner(self): return self.closeType > 0
    
    def getCloseType(self): return self.closeType
    
    def getPlayer(self): return self.player      
    
    def getScore(self):
        if self.isWinner():
            return 0
        else:
            try:
                score =  int(self.scoreLineEdit.text())
            except ValueError:
                score = -1
            return score
                
    def isKo(self): return self.ko
    
    def setKo(self): self.ko = True
        
    
class RemigioPlayerWidget(QtGui.QWidget):
    def __init__(self,nick,parent = None):
        super(RemigioPlayerWidget,self).__init__(parent)
        self.player = nick
        self.initUI()
        
    def initUI(self):
#        self.setMinimumWidth(300)
        self.mainLayout = QtGui.QHBoxLayout(self)
        self.scoreLCD = QtGui.QLCDNumber(self)
        self.scoreLCD.setSegmentStyle(QtGui.QLCDNumber.Flat)
        self.mainLayout.addWidget(self.scoreLCD)
        self.scoreLCD.setNumDigits(3)
        self.scoreLCD.setFixedSize(100,50)
#        self.scoreLCD.setMinimumHeight(30)
        self.scoreLCD.display(0)
#        self.scoreLCD.setMaximumHeight(100)
        self.nameLabel = QtGui.QLabel(self)
        self.nameLabel.setText(self.player)
        self.nameLabel.setStyleSheet("QLabel { font-size: 16px; font-weight:bold; }")
        self.mainLayout.addWidget(self.nameLabel)
        
    def updateDisplay(self,points):
        if points >= 1000: self.scoreLCD.setNumDigits(4)
        self.scoreLCD.display(points)
        
    def setShuffler(self):
        if self.isEnabled():
            self.nameLabel.setStyleSheet("QLabel { font-size: 16px; font-weight: bold; color: red }")
        
    def unsetShuffler(self):
        self.nameLabel.setStyleSheet("QLabel { font-size: 18px; font-weight: bold; color: black}")
        if not self.isEnabled(): self.setDisabled(True)
        
    def koPlayer(self):
        self.setDisabled(True)
     
            
class RemigioRoundsDetail(QtGui.QGroupBox):
    def __init__(self, engine, parent=None):
        super(RemigioRoundsDetail, self).__init__(parent)
        self.engine = engine
        self.initUI()

    def initUI(self):
        self.setTitle('Detalles')
        self.widgetLayout = QtGui.QVBoxLayout(self)
        self.table = QtGui.QTableWidget(0,len(self.engine.getPlayers()))
        self.widgetLayout.addWidget(self.table)
        players = self.engine.getListPlayers()
        self.table.setHorizontalHeaderLabels(players)
        self.table.horizontalHeader().setResizeMode(QtGui.QHeaderView.Stretch)
        
    def updateRound(self):
        rounds = self.engine.getRounds()
        if not len(rounds): return
        players = self.engine.getListPlayers()
        r = rounds[-1]
        i = len(rounds) - 1
        self.table.insertRow(i)
        closeType = r.getCloseType()
        winner = r.getWinner()
        bgcolors = [0,0xCCFF99,0xFFFF99,0xFFCC99,0xFFCCFF]
        background = bgcolors[closeType]
        
        for player,j in zip(players,range(len(players))):
            item = QtGui.QTableWidgetItem()
            item.setFlags(item.flags()^QtCore.Qt.ItemIsEditable)
            item.setTextAlignment(QtCore.Qt.AlignVCenter|QtCore.Qt.AlignCenter)
            item.setBackgroundColor(QtGui.QColor(background))
            if player == winner:
                text = "Ganador ({}x)".format(closeType)
                font = item.font()
                font.setBold(True)
                item.setFont(font)
            elif self.engine.isPlayerOff(player):
                text = ""
                item.setBackgroundColor(QtCore.Qt.gray)          
            else:
                text = str(r.getScore(player))
            item.setText(text)
            self.table.setItem(i,j,item)
        