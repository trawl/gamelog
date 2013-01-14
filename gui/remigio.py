#!/usr/bin/env python
# -*- coding: utf-8 -*-

try:
    from PySide import QtCore,QtGui
    QtGui.QFileDialog.getOpenFileNameAndFilter = QtGui.QFileDialog.getOpenFileName
except ImportError as error:
    from PyQt4 import QtCore,QtGui
    QtCore.Signal = QtCore.pyqtSignal
    QtCore.Slot = QtCore.pyqtSlot

from controllers.remigioengine import RemigioEngine
from gui.game import GameWidget
from gui.clock import GameClock

class RemigioWidget(GameWidget):

    bgcolors = [0,0xCCFF99,0xFFFF99,0xFFCC99,0xFFCCFF]

    def __init__(self, game, players, parent=None):
        super(RemigioWidget, self).__init__(game,players,parent)
        self.initUI()
        
    def createEngine(self):
        if self.game != 'Remigio':
            raise Exception("No engine for game {}".format(self.game))
            return
        self.engine = RemigioEngine()     

    def initUI(self):
        self.mainLayout = QtGui.QGridLayout(self)
    
        self.buttonGroup=QtGui.QGroupBox(self)
        self.buttonGroup.setStyleSheet("QGroupBox { font-size: 18px; font-weight: bold; }")


        self.mainLayout.addWidget(self.buttonGroup,0,0)
        self.buttonGroupLayout= QtGui.QVBoxLayout(self.buttonGroup)
        self.buttonGroupSubLayout= QtGui.QHBoxLayout()
        self.buttonGroupLayout.addLayout(self.buttonGroupSubLayout)
        

        self.cancelMatchButton = QtGui.QPushButton(self.buttonGroup)
        self.buttonGroupSubLayout.addWidget(self.cancelMatchButton)
        self.cancelMatchButton.clicked.connect(self.cancelMatch)
        
        self.pauseMatchButton = QtGui.QPushButton(self.buttonGroup)
        self.buttonGroupSubLayout.addWidget(self.pauseMatchButton)
        self.pauseMatchButton.clicked.connect(self.pauseMatch)
        
        self.commitRoundButton = QtGui.QPushButton(self.buttonGroup)
        self.buttonGroupSubLayout.addWidget(self.commitRoundButton)
        self.commitRoundButton.clicked.connect(self.commitRound)
        
        self.gameStatusLabel = QtGui.QLabel(self)
        self.gameStatusLabel.setStyleSheet("QLabel { font-size: 16px; font-weight:bold; color: red;}")
        self.gameStatusLabel.setAlignment(QtCore.Qt.AlignCenter)
        self.gameStatusLabel.hide()
        self.buttonGroupLayout.addWidget(self.gameStatusLabel)
        
        self.infoLabel = QtGui.QLabel(self)
        self.infoLabel.setStyleSheet("QLabel {font-weight:bold;}")
        self.infoLabel.setAlignment(QtCore.Qt.AlignCenter)
        
        self.buttonGroupLayout.addWidget(self.infoLabel)
        self.inputGroup = RemigioInputWidget(self.engine,RemigioWidget.bgcolors, self)
        self.buttonGroupLayout.addWidget(self.inputGroup)

        self.matchGroup = QtGui.QGroupBox(self)
        self.matchGroup.setStyleSheet("QGroupBox { font-size: 18px; font-weight: bold; }")
        self.mainLayout.addWidget(self.matchGroup,0,1)
        
        self.matchGroupLayout = QtGui.QVBoxLayout(self.matchGroup)
        
        self.clock = GameClock(self)
        self.clock.setMinimumHeight(100)
        self.matchGroupLayout.addWidget(self.clock)
        
        self.dealerPolicyCheckBox = QtGui.QCheckBox(self.matchGroup)
        if self.engine.getDealingPolicy() == self.engine.WinnerDealer:
            self.dealerPolicyCheckBox.setChecked(True)
        else:
            self.dealerPolicyCheckBox.setChecked(False)
        self.dealerPolicyCheckBox.setStyleSheet("QCheckBox { font-size: 14px; font-weight: bold; }")
        self.dealerPolicyCheckBox.stateChanged.connect(self.changeDealingPolicy)
        self.matchGroupLayout.addWidget(self.dealerPolicyCheckBox)
        
        self.configLayout = QtGui.QGridLayout()
        self.matchGroupLayout.addLayout(self.configLayout)
        
        self.topPointsLineEdit = QtGui.QLineEdit(self.matchGroup)
        self.topPointsLineEdit.setText(str(self.engine.getTop()))
        self.topPointsLineEdit.setValidator(QtGui.QIntValidator(1,10000,self.topPointsLineEdit))
        self.topPointsLineEdit.setFixedWidth(35)
        sp = QtGui.QSizePolicy(QtGui.QSizePolicy.Fixed,QtGui.QSizePolicy.Fixed)
        self.topPointsLineEdit.setSizePolicy(sp)
        self.topPointsLineEdit.textChanged.connect(self.changeTop)
        self.configLayout.addWidget(self.topPointsLineEdit,0,0)
        
        self.topPointsLabel = QtGui.QLabel(self.matchGroup)
        self.topPointsLabel.setStyleSheet("QLabel { font-size: 14px; font-weight: bold; }")
        self.configLayout.addWidget(self.topPointsLabel,0,1)
        
        self.detailGroup = RemigioRoundsDetail(self.engine, RemigioWidget.bgcolors, self)
        self.detailGroup.setStyleSheet("QGroupBox { font-size: 18px; font-weight: bold; }")
        self.mainLayout.addWidget(self.detailGroup,1,0)        
        
        self.playerGroup = QtGui.QGroupBox(self)
        self.mainLayout.addWidget(self.playerGroup,1,1)

        self.playerGroup.setStyleSheet("QGroupBox { font-size: 18px; font-weight: bold; }")
        self.playersLayout = QtGui.QVBoxLayout(self.playerGroup)
        self.playersLayout.addStretch()
        self.playerGroupBox = {}
        for player in self.players:
            pw = RemigioPlayerWidget(player,self.playerGroup)
            if player == self.engine.getDealer():
                pw.setDealer()
            self.playersLayout.addWidget(pw)
            self.playerGroupBox[player] = pw
 
        self.playersLayout.addStretch()
        
        self.retranslateUI()
    
            
    def pauseMatch(self):
        if self.engine.isPaused():
            self.engine.unpause()
            self.clock.unpauseTimer()
            self.gameStatusLabel.hide()
            self.inputGroup.setEnabled(True)
            self.commitRoundButton.setEnabled(True)
        else:
            self.engine.pause()
            self.clock.pauseTimer()
            self.gameStatusLabel.show()
            self.inputGroup.setDisabled(True)
            self.commitRoundButton.setDisabled(True)

        
    def retranslateUI(self):
        self.buttonGroup.setTitle(unicode(QtGui.QApplication.translate("RemigioWidget","Round {0}")).format(str(self.engine.getNumRound())))
        self.cancelMatchButton.setText(QtGui.QApplication.translate("RemigioWidget","&Cancel Match"))
        self.commitRoundButton.setText(QtGui.QApplication.translate("RemigioWidget","Commit &Round"))
        self.pauseMatchButton.setText(QtGui.QApplication.translate("RemigioWidget","&Pause/Play"))
        self.infoLabel.setText(QtGui.QApplication.translate("RemigioWidget","Warning: real points are computed automatically depending on the close type"))    
        self.matchGroup.setTitle(QtGui.QApplication.translate("RemigioWidget","Match"))
        self.dealerPolicyCheckBox.setText(QtGui.QApplication.translate("RemigioWidget","Winner deals"))
        self.topPointsLabel.setText(QtGui.QApplication.translate("RemigioWidget","Score Limit"))
        self.playerGroup.setTitle(QtGui.QApplication.translate("RemigioWidget","Score"))
        self.detailGroup.retranslateUI()
        
        winner = self.engine.getWinner()
        if winner:
            self.gameStatusLabel.setText(QtGui.QApplication.translate("RemigioWidget","{} won this match!").format(winner))    
        else:
            self.gameStatusLabel.setText(QtGui.QApplication.translate("RemigioWidget","Game is paused"))    
    
        
    def commitRound(self):
        self.engine.openRound()
        winner = self.inputGroup.getWinner()
        if not winner:
            QtGui.QMessageBox.warning(self,self.game,unicode(QtGui.QApplication.translate("RemigioWidget","No winner selected")))
            return
        else:
            self.engine.setRoundWinner(winner)
        c_type = self.inputGroup.getCloseType()
        scores = self.inputGroup.getScores()
        for player,score in scores.items():
            if score>=0 :
                self.engine.addRoundInfo(player,score, {'closeType':c_type})
            else:
                QtGui.QMessageBox.warning(self,self.game,unicode(QtGui.QApplication.translate("RemigioWidget","{0} score is not valid").format(player)))
                return

        #Everything ok so far, let's confirm
        ret = QtGui.QMessageBox.question(self, QtGui.QApplication.translate("RemigioWidget",'Commit Round'),
        QtGui.QApplication.translate("RemigioWidget","Are you sure you want to commit the current round?"), QtGui.QMessageBox.Yes | 
        QtGui.QMessageBox.No, QtGui.QMessageBox.Yes)
        
        if ret == QtGui.QMessageBox.No: return

        # Once here, we can commit round...
        self.playerGroupBox[self.engine.getDealer()].unsetDealer()
        self.engine.commitRound()
        self.engine.printStats()
        
        self.updatePanel()
        winner = self.engine.getWinner()
        if winner:
            self.pauseMatchButton.setDisabled(True)
            self.clock.stopTimer()
            self.commitRoundButton.setDisabled(True)
            self.gameStatusLabel.setText(QtGui.QApplication.translate("RemigioWidget","{} won this match!").format(winner))    
            self.gameStatusLabel.show()
            for player in self.players:
                self.inputGroup.setDisabled(True)
            QtGui.QMessageBox.information(self,self.game,unicode(QtGui.QApplication.translate("RemigioWidget","{0} won this game!").format(winner)))
        else:           
            self.playerGroupBox[self.engine.getDealer()].setDealer() 
            
    def changeDealingPolicy(self, *args, **kwargs):
        if self.dealerPolicyCheckBox.isChecked():
            self.engine.setDealingPolicy(self.engine.WinnerDealer)
        else:
            self.engine.setDealingPolicy(self.engine.RRDealer)

    def updatePanel(self):
        self.inputGroup.reset()
        self.topPointsLineEdit.setReadOnly(True)
        self.dealerPolicyCheckBox.setEnabled(False)
        
        if not self.engine.getWinner():
            self.buttonGroup.setTitle(unicode(QtGui.QApplication.translate("RemigioWidget","Round {0}")).format(str(self.engine.getNumRound())))
            
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
    def __init__(self,engine,bgcolors, parent=None):
        super(RemigioInputWidget,self).__init__(parent)
        self.engine = engine
        self.bgcolors = bgcolors
        self.initUI()
        self.winnerSelected = ""

    def initUI(self):
        self.widgetLayout = QtGui.QVBoxLayout(self)       
        self.tableLayout = QtGui.QHBoxLayout()
        self.widgetLayout.addLayout(self.tableLayout)
        
        self.playerInputList = {}
        for player in self.engine.getListPlayers():
            self.playerInputList[player] = RemigioPlayerInputWidget(player,self.bgcolors,self)
            self.tableLayout.addWidget(self.playerInputList[player])
            self.playerInputList[player].winnerSet.connect(self.changedWinner)

            
    def getWinner(self):
        return self.winnerSelected
    
    def getCloseType(self):
        try: return self.playerInputList[self.winnerSelected].getCloseType()
        except KeyError: return 0
    
    def getScores(self):
        scores = {}
        for player,piw in self.playerInputList.items():
            if not piw.isKo():
                scores[player] = piw.getScore()
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
        
class RemigioPlayerInputWidget(QtGui.QFrame):
    
    winnerSet = QtCore.Signal(str)
    
    def __init__(self,player,bgcolors,parent=None):
        super(RemigioPlayerInputWidget, self).__init__(parent)
        self.player = player
        self.ko = False
        self.bgcolors = bgcolors
        
        self.mainLayout = QtGui.QVBoxLayout(self)
        
        self.label = QtGui.QLabel(self)
        self.mainLayout.addWidget(self.label)
        self.label.setAutoFillBackground(False)
        self.setFrameShape(QtGui.QFrame.Panel)
        self.setFrameShadow(QtGui.QFrame.Raised)
        self.label.setScaledContents(True)
        self.label.setAlignment(QtCore.Qt.AlignCenter)
        self.label.setWordWrap(False)
        
        self.scoreLineEdit = QtGui.QLineEdit(self)
        self.scoreLineEdit.setAlignment(QtCore.Qt.AlignCenter)
        self.scoreLineEdit.setMaximumWidth(60)
        self.mainLayout.addWidget(self.scoreLineEdit)
        self.mainLayout.setAlignment(self.scoreLineEdit,QtCore.Qt.AlignCenter)
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
            text = text + " ({}x)".format(self.closeType)
            css = "font-weight: bold; background-color: #{0:X}".format(self.bgcolors[self.closeType])
            self.scoreLineEdit.setText("0")
            self.scoreLineEdit.setDisabled(True)
            self.setFrameShadow(QtGui.QFrame.Sunken)
        else:
            self.setFrameShadow(QtGui.QFrame.Raised)
            self.scoreLineEdit.setText("")
            self.scoreLineEdit.setEnabled(True)
        
        self.label.setText(text)
        self.setStyleSheet("QFrame {{ {} }}".format(css))
        
    def mousePressEvent(self, event):
        if self.isWinner(): self.increaseCloseType()
        else: self.scoreLineEdit.setFocus()
        
    def mouseDoubleClickEvent(self, event):
        if not self.isWinner(): 
            self.winnerSet.emit(self.player)
            self.increaseCloseType()
        else:
            super(RemigioPlayerInputWidget,self).mouseDoubleClickEvent(event)

        
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
    
    def setKo(self): 
        self.ko = True
        self.setDisabled(True)
        
    
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
        
    def setDealer(self):
        if self.isEnabled():
            self.nameLabel.setStyleSheet("QLabel { font-size: 16px; font-weight: bold; color: red }")
        
    def unsetDealer(self):
        self.nameLabel.setStyleSheet("QLabel { font-size: 18px; font-weight: bold; color: black}")
        if not self.isEnabled(): self.setDisabled(True)
        
    def koPlayer(self):
        self.setDisabled(True)
     
            
class RemigioRoundsDetail(QtGui.QGroupBox):
    def __init__(self, engine, bgcolors, parent=None):
        super(RemigioRoundsDetail, self).__init__(parent)
        self.bgcolors = bgcolors
        self.engine = engine
        self.initUI()

    def initUI(self):
        self.widgetLayout = QtGui.QVBoxLayout(self)
        self.table = QtGui.QTableWidget(0,len(self.engine.getPlayers()))
        self.widgetLayout.addWidget(self.table)
        players = self.engine.getListPlayers()
        self.table.setHorizontalHeaderLabels(players)
        self.table.horizontalHeader().setResizeMode(QtGui.QHeaderView.Stretch)
        self.retranslateUI()
        
    def retranslateUI(self):
        self.setTitle(QtGui.QApplication.translate("RemigioRoundsDetail",'Details'))
        self.recomputeTable()

    def recomputeTable(self):
        self.table.clearContents()
        for i,r in enumerate(self.engine.getRounds()):
            self.insertRound(r,i)
    
    def insertRound(self,r,i):
        closeType = r.getCloseType()
        winner = r.getWinner()
        background = self.bgcolors[closeType]
        self.table.insertRow(i)
        for j, player in enumerate(self.engine.getListPlayers()):
            item = QtGui.QTableWidgetItem()
            item.setFlags(item.flags()^QtCore.Qt.ItemIsEditable)
            item.setTextAlignment(QtCore.Qt.AlignVCenter|QtCore.Qt.AlignCenter)
            item.setBackground(QtGui.QBrush(QtGui.QColor(background)))
            if player == winner:
                text = unicode(QtGui.QApplication.translate("RemigioRoundsDetail","Winner ({}x)")).format(closeType)
                font = item.font()
                font.setBold(True)
                item.setFont(font)
            elif self.engine.isPlayerOff(player) or r.getPlayerScore < 0:
                text = ""
                item.setBackground(QtGui.QBrush(QtCore.Qt.gray))          
            else:
                text = str(r.getPlayerScore(player))
            item.setText(text)
            self.table.setItem(i,j,item)
        self.table.scrollToBottom()
        
    def updateRound(self):
        rounds = self.engine.getRounds()
        if not len(rounds): return
        r = rounds[-1]
        i = len(rounds) - 1
        self.insertRound(r,i)
    

        
