#!/usr/bin/env python
# -*- coding: utf-8 -*-

try:
    from PyQt4 import QtCore,QtGui
    QtCore.Signal = QtCore.pyqtSignal
    QtCore.Slot = QtCore.pyqtSlot
except ImportError as error:
    from PySide import QtCore,QtGui
    QtGui.QFileDialog.getOpenFileNameAndFilter = QtGui.QFileDialog.getOpenFileName

from controllers.pochaengine import PochaEngine
from gui.game import GameWidget,GameInputWidget,GameRoundsDetail,GameRoundTable,GameRoundPlot,GamePlayerWidget,PlayerColours


class PochaWidget(GameWidget):
    
    QtGui.QApplication.translate("PochaWidget",'going up')
    QtGui.QApplication.translate("PochaWidget",'going down')
    QtGui.QApplication.translate("PochaWidget",'hand')
    QtGui.QApplication.translate("PochaWidget",'hands')
    QtGui.QApplication.translate("PochaWidget",'coins')
    QtGui.QApplication.translate("PochaWidget",'cups')
    QtGui.QApplication.translate("PochaWidget",'swords')
    QtGui.QApplication.translate("PochaWidget",'clubs')
        
    def createEngine(self):
        if self.game != 'Pocha':
            raise Exception("No engine for game {}".format(self.game))
            return
        self.engine = PochaEngine()     

    def initUI(self):
        super(PochaWidget,self).initUI()
 
        self.gameInput = PochaInputWidget(self.engine, self)
        self.gameInput.enterPressed.connect(self.commitRound)
        self.roundLayout.addWidget(self.gameInput)
        
        self.configLayout = QtGui.QGridLayout()
        
        self.dealerPolicyCheckBox.hide()
        
        self.detailGroup = PochaRoundsDetail(self.engine, self)
        self.detailGroup.edited.connect(self.updatePanel)
        self.widgetLayout.addWidget(self.detailGroup,1,0)        
        
        self.playerGroup = QtGui.QGroupBox(self)
        self.widgetLayout.addWidget(self.playerGroup,1,1)

        self.playerGroup.setStyleSheet("QGroupBox { font-size: 18px; font-weight: bold; }")
        self.playersLayout = QtGui.QVBoxLayout(self.playerGroup)
        self.playersLayout.addStretch()
        self.playerGroupBox = {}
        for i,player in enumerate(self.players):
            pw = GamePlayerWidget(player,PlayerColours[i],self.playerGroup)
            pw.updateDisplay(self.engine.getScoreFromPlayer(player))
            if player == self.engine.getDealer(): pw.setDealer()
            self.playersLayout.addWidget(pw)
            self.playerGroupBox[player] = pw
 
        self.playersLayout.addStretch()
        
        self.retranslateUI()
        
    def retranslateUI(self):
        super(PochaWidget,self).retranslateUI()
        self.playerGroup.setTitle(QtGui.QApplication.translate("PochaWidget","Score"))
        self.detailGroup.retranslateUI()
        
    def setRoundTitle(self):
        super(PochaWidget,self).setRoundTitle()
        hands = self.engine.getHands()
        direction = self.engine.getDirection()
        if hands == 1:
            self.roundGroup.setTitle("{} - {} {} {}".format(self.roundGroup.title(),str(hands),QtGui.QApplication.translate("PochaWidget","hand"), QtGui.QApplication.translate("PochaWidget",direction)))
        else:
            self.roundGroup.setTitle("{} - {} {} {}".format(self.roundGroup.title(),str(hands),QtGui.QApplication.translate("PochaWidget","hands"), QtGui.QApplication.translate("PochaWidget",direction)))
        
    def checkPlayerScore(self,player,score): return True
    
    def unsetDealer(self): self.playerGroupBox[self.engine.getDealer()].unsetDealer()
    
    def setDealer(self): self.playerGroupBox[self.engine.getDealer()].setDealer() 

    def updatePanel(self):
        for player in self.players:
            score = self.engine.getScoreFromPlayer(player)
            self.playerGroupBox[player].updateDisplay(score)
        
        if self.engine.getWinner(): self.detailGroup.updateStats()
        self.detailGroup.updateRound()
        super(PochaWidget,self).updatePanel()
        
    def setWinner(self):
        super(PochaWidget,self).setWinner()
        winner = self.engine.getWinner()
        if winner in self.players:
            self.playerGroupBox[winner].setWinner()
        
    def commitRound(self):
        hands = self.engine.getHands()
        wonhands = self.gameInput.getWonHands()
        won = sum(wonhands.values())
        if min(wonhands.values()):
            QtGui.QMessageBox.warning(self,self.game,QtGui.QApplication.translate("PochaWidget","There are players with no selected won hands."))
            return
        
        if hands != won:
            QtGui.QMessageBox.warning(self,self.game,QtGui.QApplication.translate("PochaWidget","There are {} won hands selected when there should be {}.").format(won,hands))
            return

        super(PochaWidget,self).commitRound()
        
class PochaInputWidget(GameInputWidget):
    
    def __init__(self,engine, parent=None):
        super(PochaInputWidget,self).__init__(engine,parent)
        self.initUI()

    def initUI(self):
        self.widgetLayout = QtGui.QGridLayout(self)
        players = self.engine.getListPlayers()
        for i,player in enumerate(players):
            self.playerInputList[player] = PochaPlayerInputWidget(player, self.engine, PlayerColours[i], self)
            self.widgetLayout.addWidget(self.playerInputList[player],i/4,i%4)
            self.playerInputList[player].winnerSet.connect(self.changedWinner)
            self.playerInputList[player].newExpected.connect(self.checkExpected)
    
    def getScores(self):
        scores = {}
        for player,piw in self.playerInputList.items():
            scores[player] = piw.getScore()
        return scores
    
    def getWonHands(self):
        won = {}
        for player,piw in self.playerInputList.items():
            won[player] = piw.getWonHands()
        return won

    def checkExpected(self):
        notselected = []
        totalexpected = 0
        hands = self.engine.getHands()
        for player,piw in self.playerInputList.items():
            expected = piw.getExpectedHands()
            if expected < 0: notselected.append(player)
            else: totalexpected += expected
            
        forbidden = hands - totalexpected
        
        for player,piw in self.playerInputList.items():
            if len(notselected) == 1 and player in notselected and forbidden >= 0:
                piw.refreshButtons(forbidden)
            else:
                piw.refreshButtons()
            piw.disableWonRow(len(notselected) == 0 and forbidden == 0)

        
class PochaPlayerInputWidget(QtGui.QFrame):
    
    winnerSet = QtCore.Signal(str)
    newExpected = QtCore.Signal()
    
    def __init__(self,player,engine, colour=None, parent=None):
        super(PochaPlayerInputWidget, self).__init__(parent)
        self.player = player
        self.engine = engine
        self.winner = False
        self.pcolour = colour
        self.mainLayout = QtGui.QVBoxLayout(self)
        self.mainLayout.setSpacing(0)
#         self.setMinimumHeight(40)
#         self.sizePolicy()
#         self.setSizePolicy(QtGui.QSizePolicy.Maximum,QtGui.QSizePolicy.MinimumExpanding)
        
        self.label = QtGui.QLabel(self)
        self.label.setText(self.player)
        self.mainLayout.addWidget(self.label)
        self.label.setAutoFillBackground(False)
        self.setFrameShape(QtGui.QFrame.Panel)
        self.setFrameShadow(QtGui.QFrame.Raised)
        self.label.setScaledContents(True)
        self.label.setAlignment(QtCore.Qt.AlignCenter)
        self.label.setWordWrap(False)
        sh = "QLabel {{ font-size: 20px; font-weight: bold; color:rgb({},{},{});}}".format(self.pcolour.red(),self.pcolour.green(),self.pcolour.blue())
        self.label.setStyleSheet(sh)
        
        self.expectedGroupBox = QtGui.QFrame(self)
        self.mainLayout.addWidget(self.expectedGroupBox)
        self.ebLayout = QtGui.QHBoxLayout(self.expectedGroupBox)
        self.ebLayout.setSpacing(0)
        self.ebLayout.setContentsMargins(2,2,2,2);
        self.expectedGroup = QtGui.QButtonGroup(self)
        self.expectedGroup.buttonReleased.connect(self.enableWonGroup)
        self.expectedButtons = []
        
        self.wonGroupBox = QtGui.QFrame(self)
        self.mainLayout.addWidget(self.wonGroupBox)
        self.wbLayout = QtGui.QHBoxLayout(self.wonGroupBox)
        self.wbLayout.setSpacing(0)
        self.wbLayout.setContentsMargins(2,2,2,2);
        self.wonGroup = QtGui.QButtonGroup(self)
        self.wonButtons = []
        for i in range(-1,9):
            button = QtGui.QPushButton(str(i),self)
            button.setCheckable(True)
            button.setMinimumSize(20, 20)
            button.setSizePolicy(QtGui.QSizePolicy.MinimumExpanding,QtGui.QSizePolicy.Maximum)
            self.expectedGroup.addButton(button,i)
            self.expectedButtons.append(button)
            if i<0: button.hide()
            else: self.ebLayout.addWidget(button)
            
            button = QtGui.QPushButton(str(i),self)
            button.setCheckable(True)
            button.setMinimumSize(20, 20)
            button.setSizePolicy(QtGui.QSizePolicy.MinimumExpanding,QtGui.QSizePolicy.Maximum)
            self.wonGroup.addButton(button,i)
            self.wonButtons.append(button)
            if i<0: button.hide()
            else: self.wbLayout.addWidget(button)
        
        self.reset()
    
    def reset(self):
        self.expectedButtons[0].setChecked(True)
        self.wonButtons[0].setChecked(True)
        self.refreshButtons()
        self.disableWonRow()

    def refreshButtons(self,forbidden=-1):
        hands = self.engine.getHands()
        for eb, wb in zip(self.expectedButtons, self.wonButtons):
            eb.setDisabled(int(eb.text()) > hands)
            if int(eb.text()) == forbidden: eb.setDisabled(True)
            wb.setDisabled(int(wb.text()) > hands)
            
    def disableWonRow(self,disable=True): 
        if self.getExpectedHands()<0: self.wonGroupBox.setDisabled(True)
        else: self.wonGroupBox.setDisabled(disable)

    def enableWonGroup(self, button):
        self.newExpected.emit()

    def isWinner(self): return False
    
    def getPlayer(self): return self.player      
    
    def getScore(self): 
        expected = self.expectedGroup.checkedId()
        won = self.wonGroup.checkedId()
        if expected < 0  or won < 0: return 0
        if expected == won: return 10 + 3 * won
        return -3 * abs(expected - won)

    def getWonHands(self): return self.wonGroup.checkedId()
    
    def getExpectedHands(self): return self.expectedGroup.checkedId()

class PochaRoundsDetail(GameRoundsDetail):
    
    def __init__(self, engine, parent=None):
        self.bgcolors = [0xCCFF99,0xFFCC99]
        super(PochaRoundsDetail, self).__init__(engine,parent)
        
    def createRoundTable(self, engine, parent=None):
        return PochaRoundTable(self.engine,self.bgcolors, parent)
      
    def createRoundPlot(self, engine, parent=None): 
        return PochaRoundPlot(self.engine,self)
    
    
class PochaRoundTable(GameRoundTable):
    
    def __init__(self, engine, bgcolors, parent=None):
        self.bgcolors = bgcolors
        super(PochaRoundTable, self).__init__(engine,parent)

    def insertRound(self,r):
        winner = r.getWinner()
        i = r.getNumRound() - 1
        self.insertRow(i)
        hitem = QtGui.QTableWidgetItem("{} {}".format(self.engine.getHands(r.getNumRound()),QtGui.QApplication.translate("PochaWidget",self.engine.getDirection(r.getNumRound()))))
        self.setVerticalHeaderItem(i,hitem)
        
        for j, player in enumerate(self.engine.getListPlayers()):
            item = QtGui.QTableWidgetItem()
            item.setFlags(item.flags()^QtCore.Qt.ItemIsEditable)
            item.setTextAlignment(QtCore.Qt.AlignVCenter|QtCore.Qt.AlignCenter)
            score = r.getPlayerScore(player)
            if score > 0 : background = self.bgcolors[0]
            else: background = self.bgcolors[1]
            item.setBackground(QtGui.QBrush(QtGui.QColor(background)))
            text = str(score)
            if player == winner: text += QtGui.QApplication.translate("PochaRoundTable"," (Winner)")
            item.setText(text)
            self.setItem(i,j,item)
        self.scrollToBottom()
        
        
class PochaRoundPlot(GameRoundPlot):
    
    def initPlot(self):
        super(PochaRoundPlot,self).initPlot()
        self.updatePlot()
        
    def updatePlot(self):
        super(PochaRoundPlot,self).updatePlot()
        if not self.isPlotInited(): return
        scores = {}
        for player in self.engine.getPlayers():
            scores[player] = [0]
            
        for rnd in self.engine.getRounds():
            for player in self.engine.getPlayers():
                rndscore = rnd.getPlayerScore(player)
                accumscore = scores[player][-1] + rndscore
                scores[player].append(accumscore)


        self.canvas.clearPlotContents()
        for player in self.engine.getListPlayers():        
            self.canvas.addSeries(scores[player],player)
            
            
