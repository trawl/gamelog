#!/usr/bin/env python
# -*- coding: utf-8 -*-

try:
    from PyQt4 import QtCore,QtGui
    QtCore.Signal = QtCore.pyqtSignal
    QtCore.Slot = QtCore.pyqtSlot
except ImportError as error:
    from PySide import QtCore,QtGui
    QtGui.QFileDialog.getOpenFileNameAndFilter = QtGui.QFileDialog.getOpenFileName

from controllers.ratukiengine import RatukiEngine
from gui.game import GameWidget,GameInputWidget,ScoreSpinBox,GameRoundPlot,GamePlayerWidget,PlayerColours


class RatukiWidget(GameWidget):
        
    def createEngine(self):
        if self.game != 'Ratuki':
            raise Exception("No engine for game {}".format(self.game))
            return
        self.engine = RatukiEngine()     

    def initUI(self):
        super(RatukiWidget,self).initUI()
 
        self.gameInput = RatukiInputWidget(self.engine, self)
        self.gameInput.enterPressed.connect(self.commitRound)
        self.roundLayout.addWidget(self.gameInput)
        
        self.configLayout = QtGui.QGridLayout()
        self.matchGroupLayout.addLayout(self.configLayout)
        self.topPointsLineEdit = QtGui.QLineEdit(self.matchGroup)
        self.topPointsLineEdit.setText(str(self.engine.getTop()))
        self.topPointsLineEdit.setValidator(QtGui.QIntValidator(1,10000,self.topPointsLineEdit))
        self.topPointsLineEdit.setFixedWidth(35)
        sp = QtGui.QSizePolicy(QtGui.QSizePolicy.Fixed,QtGui.QSizePolicy.Fixed)
        self.topPointsLineEdit.setSizePolicy(sp)
        self.topPointsLineEdit.textChanged.connect(self.changeTop)
        self.topPointsLineEdit.setDisabled(self.engine.getNumRound()>1)
        self.configLayout.addWidget(self.topPointsLineEdit,0,0)
        
        self.topPointsLabel = QtGui.QLabel(self.matchGroup)
        self.topPointsLabel.setStyleSheet("QLabel { font-size: 14px; font-weight: bold; }")
        self.configLayout.addWidget(self.topPointsLabel,0,1)
        
        self.detailGroup = RatukiRoundsDetail(self.engine, self)
        self.detailGroup.setStyleSheet("QGroupBox { font-size: 18px; font-weight: bold; }")
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
        super(RatukiWidget,self).retranslateUI()
        self.topPointsLabel.setText(QtGui.QApplication.translate("RatukiWidget","Score Limit"))
        self.playerGroup.setTitle(QtGui.QApplication.translate("RatukiWidget","Score"))
        self.detailGroup.retranslateUI()
        
    def checkPlayerScore(self,player,score): return True
    
    def unsetDealer(self): self.playerGroupBox[self.engine.getDealer()].unsetDealer()
    
    def setDealer(self): self.playerGroupBox[self.engine.getDealer()].setDealer() 

    def updatePanel(self):
        self.topPointsLineEdit.setReadOnly(True)
        self.dealerPolicyCheckBox.setEnabled(False)
        for player in self.players:
            score = self.engine.getScoreFromPlayer(player)
            self.playerGroupBox[player].updateDisplay(score)
        
        self.detailGroup.updateRound()
        super(RatukiWidget,self).updatePanel()
        
    def changeTop(self,newtop):
        try:
            newtop = int(newtop)    
            self.engine.setTop(newtop)
            self.detailGroup.updatePlot()
        except ValueError: pass
        
    def setWinner(self):
        super(RatukiWidget,self).setWinner()
        winner = self.engine.getWinner()
        if winner in self.players:
            self.playerGroupBox[winner].setWinner()
        
        
class RatukiInputWidget(GameInputWidget):
    
    def __init__(self,engine, parent=None):
        super(RatukiInputWidget,self).__init__(engine,parent)
        self.initUI()

    def initUI(self):
        self.widgetLayout = QtGui.QHBoxLayout(self)

        for player in self.engine.getListPlayers():
            self.playerInputList[player] = RatukiPlayerInputWidget(player,self)
            self.widgetLayout.addWidget(self.playerInputList[player])
            self.playerInputList[player].winnerSet.connect(self.changedWinner)
    
    def getScores(self):
        scores = {}
        for player,piw in self.playerInputList.items():
            scores[player] = piw.getScore()
        return scores
        
        
class RatukiPlayerInputWidget(QtGui.QFrame):
    
    winnerSet = QtCore.Signal(str)
    
    def __init__(self,player,parent=None):
        super(RatukiPlayerInputWidget, self).__init__(parent)
        self.player = player
        self.winner = False
        self.mainLayout = QtGui.QVBoxLayout(self)
        
        self.label = QtGui.QLabel(self)
        self.label.setText(self.player)
        self.mainLayout.addWidget(self.label)
        self.label.setAutoFillBackground(False)
        self.setFrameShape(QtGui.QFrame.Panel)
        self.setFrameShadow(QtGui.QFrame.Raised)
        self.label.setScaledContents(True)
        self.label.setAlignment(QtCore.Qt.AlignCenter)
        self.label.setWordWrap(False)
        
        self.scoreSpinBox = ScoreSpinBox(self)
        self.scoreSpinBox.setAlignment(QtCore.Qt.AlignCenter)
        self.scoreSpinBox.setMaximumWidth(60)
        self.scoreSpinBox.setRange(-100,100)
        self.mainLayout.addWidget(self.scoreSpinBox)
        self.mainLayout.setAlignment(self.scoreSpinBox,QtCore.Qt.AlignCenter)
        
        self.reset()
    
    def reset(self):
        self.winner = False
        self.scoreSpinBox.setValue(0)
        self.updatePanel()
        
    def updatePanel(self):
        css = ""
        if self.winner:
            css = "font-weight: bold; background-color: #{0:X}".format(0xFFFF99)
            self.setFrameShadow(QtGui.QFrame.Sunken)
        else:
            self.setFrameShadow(QtGui.QFrame.Raised)
        self.setStyleSheet("QFrame {{ {} }}".format(css))
        
    def mousePressEvent(self, event):
        self.scoreSpinBox.setFocus()
            
    def mouseDoubleClickEvent(self, event):
        if not self.isWinner(): 
            self.winner = True
            self.updatePanel()
            self.winnerSet.emit(self.player)
        else:
            super(RatukiPlayerInputWidget,self).mouseDoubleClickEvent(event)

    def isWinner(self): return self.winner
    
    
    def getPlayer(self): return self.player      
    
    def getScore(self): return self.scoreSpinBox.value()

            
class RatukiRoundsDetail(QtGui.QGroupBox):
    
    def __init__(self, engine, parent=None):
        super(RatukiRoundsDetail, self).__init__(parent)
        self.engine = engine
        self.bgcolors = [0xCCFF99,0xFFCC99]
        self.initUI()

    def initUI(self):
        self.widgetLayout = QtGui.QVBoxLayout(self)
#         self.container = QtGui.QToolBox(self)
        self.container = QtGui.QTabWidget(self)
        self.widgetLayout.addWidget(self.container)
        self.table = QtGui.QTableWidget(0,len(self.engine.getPlayers()))
        self.table.setAutoFillBackground(True)
#         self.container.addItem(self.table,'')
        self.container.addTab(self.table,'')
#        self.widgetLayout.addWidget(self.table)
        players = self.engine.getListPlayers()
        self.table.setHorizontalHeaderLabels(players)
        self.table.horizontalHeader().setResizeMode(QtGui.QHeaderView.Stretch)
        
        self.plot = RatukiRoundPlot(self.engine,self)
        self.plot.setAutoFillBackground(True)
#         self.container.addItem(self.plot,'')
        self.container.addTab(self.plot,'')
        
#        self.retranslateUI()
        
    def retranslateUI(self):
        self.setTitle(QtGui.QApplication.translate("RatukiRoundsDetail",'Details'))
#         self.container.setItemText(0,QtGui.QApplication.translate("RatukiRoundsDetail","Table"))
#         self.container.setItemText(1,QtGui.QApplication.translate("RatukiRoundsDetail","Plot"))
        self.container.setTabText(0,QtGui.QApplication.translate("RatukiRoundsDetail","Table"))
        self.container.setTabText(1,QtGui.QApplication.translate("RatukiRoundsDetail","Plot"))
        self.recomputeTable()


    def updatePlot(self):
        self.plot.updatePlot()

    def recomputeTable(self):
        self.table.clearContents()
        self.table.setRowCount(0)
        for r in self.engine.getRounds(): self.insertRound(r)
        self.updatePlot()
    
    def insertRound(self,r):
        winner = r.getWinner()
        i = r.getNumRound() - 1
        self.table.insertRow(i)
        for j, player in enumerate(self.engine.getListPlayers()):
            item = QtGui.QTableWidgetItem()
            item.setFlags(item.flags()^QtCore.Qt.ItemIsEditable)
            item.setTextAlignment(QtCore.Qt.AlignVCenter|QtCore.Qt.AlignCenter)
            score = r.getPlayerScore(player)
            if score > 0 : background = self.bgcolors[0]
            else: background = self.bgcolors[1]
            item.setBackground(QtGui.QBrush(QtGui.QColor(background)))
            text = str(score)
            if player == winner: text += QtGui.QApplication.translate("RatukiRoundsDetail"," (Winner)")
            item.setText(text)
            self.table.setItem(i,j,item)
        self.table.scrollToBottom()
        
    def updateRound(self):
        rounds = self.engine.getRounds()
        if not len(rounds): return
        r = rounds[-1]
        self.insertRound(r)
        self.plot.updatePlot()
        
        
class RatukiRoundPlot(GameRoundPlot):
    
    def initPlot(self):
        super(RatukiRoundPlot,self).initPlot()
        self.updatePlot()
        
    def updatePlot(self):
        super(RatukiRoundPlot,self).updatePlot()
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
        self.canvas.addLimit(self.engine.getTop())
        for player in self.engine.getListPlayers():        
            self.canvas.addSeries(scores[player],player)
            
            
