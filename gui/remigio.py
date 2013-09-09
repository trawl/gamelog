#!/usr/bin/env python
# -*- coding: utf-8 -*-

try:
    from PyQt4 import QtCore,QtGui
    QtCore.Signal = QtCore.pyqtSignal
    QtCore.Slot = QtCore.pyqtSlot
except ImportError as error:
    from PySide import QtCore,QtGui
    QtGui.QFileDialog.getOpenFileNameAndFilter = QtGui.QFileDialog.getOpenFileName
    
from controllers.remigioengine import RemigioEngine
from gui.game import GameWidget,GameInputWidget,ScoreSpinBox,GameRoundPlot,GamePlayerWidget,PlayerColours


class RemigioWidget(GameWidget):

    bgcolors = [0,0xCCFF99,0xFFFF99,0xFFCC99,0xFFCCFF]
        
    def createEngine(self):
        if self.game != 'Remigio':
            raise Exception("No engine for game {}".format(self.game))
            return
        self.engine = RemigioEngine()     

    def initUI(self):
        super(RemigioWidget,self).initUI()
 
        self.gameInput = RemigioInputWidget(self.engine,RemigioWidget.bgcolors, self)
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
        
        self.detailGroup = RemigioRoundsDetail(self.engine, RemigioWidget.bgcolors, self)
        self.detailGroup.setStyleSheet("QGroupBox { font-size: 18px; font-weight: bold; }")
        self.widgetLayout.addWidget(self.detailGroup,1,0)        
        
        self.playerGroup = QtGui.QGroupBox(self)
        self.widgetLayout.addWidget(self.playerGroup,1,1)

        self.playerGroup.setStyleSheet("QGroupBox { font-size: 18px; font-weight: bold; }")
        self.playersLayout = QtGui.QVBoxLayout(self.playerGroup)
        self.playersLayout.addStretch()
        self.playerGroupBox = {}
        for i,player in enumerate(self.players):
            pw = RemigioPlayerWidget(player,PlayerColours[i%len(PlayerColours)],self.playerGroup)
            pw.updateDisplay(self.engine.getScoreFromPlayer(player))
            if player == self.engine.getDealer(): pw.setDealer()
            if self.engine.isPlayerOff(player): pw.koPlayer()
            self.playersLayout.addWidget(pw)
            self.playerGroupBox[player] = pw
 
        self.playersLayout.addStretch()
        
        self.retranslateUI()
        
    def retranslateUI(self):
        super(RemigioWidget,self).retranslateUI()
        self.topPointsLabel.setText(QtGui.QApplication.translate("RemigioWidget","Score Limit"))
        self.playerGroup.setTitle(QtGui.QApplication.translate("RemigioWidget","Score"))
        self.detailGroup.retranslateUI()
        
    
    def updateGameStatusLabel(self):
        super(RemigioWidget,self).updateGameStatusLabel()
        if self.gameStatusLabel.text() == "":
            self.gameStatusLabel.setStyleSheet("QLabel {font-weight:bold;}")
            self.gameStatusLabel.setText(QtGui.QApplication.translate("RemigioWidget","Warning: real points are computed automatically depending on the close type"))
    
    
    def getPlayerExtraInfo(self,player):  
        c_type = self.gameInput.getCloseType()
        if c_type: return {'closeType':c_type}
        else: return None
    
    def unsetDealer(self): self.playerGroupBox[self.engine.getDealer()].unsetDealer()
    
    def setDealer(self): self.playerGroupBox[self.engine.getDealer()].setDealer() 

    def updatePanel(self):
        self.topPointsLineEdit.setReadOnly(True)
        self.dealerPolicyCheckBox.setEnabled(False)
        for player in self.players:
            score = self.engine.getScoreFromPlayer(player)
            self.playerGroupBox[player].updateDisplay(score)
            if self.engine.isPlayerOff(player):
                self.playerGroupBox[player].koPlayer()
                self.gameInput.koPlayer(player)
        
        self.detailGroup.updateRound()
        super(RemigioWidget,self).updatePanel()
        
    def changeTop(self,newtop):
        try:
            newtop = int(newtop)    
            self.engine.setTop(newtop)
            self.detailGroup.updatePlot()
        except ValueError: pass
        
        
class RemigioInputWidget(GameInputWidget):
    
    def __init__(self,engine,bgcolors, parent=None):
        super(RemigioInputWidget,self).__init__(engine,parent)
        self.bgcolors = bgcolors
        self.initUI()

    def initUI(self):
        self.widgetLayout = QtGui.QHBoxLayout(self)

        for player in self.engine.getListPlayers():
            self.playerInputList[player] = RemigioPlayerInputWidget(player,self.bgcolors,self)
            if self.engine.isPlayerOff(player): self.koPlayer(player)
            self.widgetLayout.addWidget(self.playerInputList[player])
            self.playerInputList[player].winnerSet.connect(self.changedWinner)
    
    def getCloseType(self):
        try: return self.playerInputList[self.winnerSelected].getCloseType()
        except KeyError: return 0
    
    def getScores(self):
        scores = {}
        for player,piw in self.playerInputList.items():
            if not piw.isKo(): scores[player] = piw.getScore()
        return scores
            
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
        
        self.scoreSpinBox = ScoreSpinBox(self)
        self.scoreSpinBox.setAlignment(QtCore.Qt.AlignCenter)
        self.scoreSpinBox.setMaximumWidth(60)
        self.scoreSpinBox.setRange(-1,100)
        self.mainLayout.addWidget(self.scoreSpinBox)
        self.mainLayout.setAlignment(self.scoreSpinBox,QtCore.Qt.AlignCenter)
        
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
            self.setFrameShadow(QtGui.QFrame.Sunken)
            self.scoreSpinBox.setValue(0)
            self.scoreSpinBox.setDisabled(True)

        else:
            self.setFrameShadow(QtGui.QFrame.Raised)
            self.scoreSpinBox.setValue(-1)
            self.scoreSpinBox.setEnabled(True)
                    
        self.label.setText(text)
        self.setStyleSheet("QFrame {{ {} }}".format(css))
        
    def mousePressEvent(self, event):
        if self.isWinner(): self.increaseCloseType()
        else: 
            self.scoreSpinBox.setFocus()
            
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
        if self.isWinner(): return 0
        else: return self.scoreSpinBox.value()
                
    def isKo(self): return self.ko
    
    def setKo(self): 
        self.ko = True
        self.setDisabled(True)
            
    
class RemigioPlayerWidget(GamePlayerWidget):
        
    def koPlayer(self):
        self.iconlabel.setEnabled(True)
        self.iconlabel.setPixmap(QtGui.QPixmap('icons/skull.png'))
#        self.iconlabel.setFixedSize(50,50)
#        self.iconlabel.show()
#         self.nameLabel.setStyleSheet("QLabel { font-size: 18px; font-weight: bold; color: grey}")
     
            
class RemigioRoundsDetail(QtGui.QGroupBox):
    
    def __init__(self, engine, bgcolors, parent=None):
        super(RemigioRoundsDetail, self).__init__(parent)
        self.bgcolors = bgcolors
        self.engine = engine
        self.initUI()

    def initUI(self):
        self.widgetLayout = QtGui.QVBoxLayout(self)
#         self.container = QtGui.QToolBox(self)
        self.container = QtGui.QTabWidget(self)
        self.widgetLayout.addWidget(self.container)
        self.table = QtGui.QTableWidget(0,len(self.engine.getPlayers()))
#         self.container.addItem(self.table,'')
        self.container.addTab(self.table,'')
        self.table.setAutoFillBackground(True)
#        self.widgetLayout.addWidget(self.table)
        players = self.engine.getListPlayers()
        self.table.setHorizontalHeaderLabels(players)
        self.table.horizontalHeader().setResizeMode(QtGui.QHeaderView.Stretch)
        
        self.plot = RemigioRoundPlot(self.engine,self)
        self.plot.setAutoFillBackground(True)
#         self.container.addItem(self.plot,'')
        self.container.addTab(self.plot,'')
        
#        self.retranslateUI()
        
    def retranslateUI(self):
        self.setTitle(QtGui.QApplication.translate("RemigioRoundsDetail",'Details'))
#         self.container.setItemText(0,QtGui.QApplication.translate("RemigioRoundsDetail","Table"))
#         self.container.setItemText(1,QtGui.QApplication.translate("RemigioRoundsDetail","Plot"))
        self.container.setTabText(0,QtGui.QApplication.translate("RemigioRoundsDetail","Table"))
        self.container.setTabText(1,QtGui.QApplication.translate("RemigioRoundsDetail","Plot"))
        self.recomputeTable()


    def updatePlot(self):
        self.plot.updatePlot()

    def recomputeTable(self):
        self.table.clearContents()
        self.table.setRowCount(0)
        for r in self.engine.getRounds(): self.insertRound(r)
        self.updatePlot()
    
    def insertRound(self,r):
        closeType = r.getCloseType()
        winner = r.getWinner()
        background = self.bgcolors[closeType]
        i = r.getNumRound() - 1
        self.table.insertRow(i)
        for j, player in enumerate(self.engine.getListPlayers()):
            item = QtGui.QTableWidgetItem()
            item.setFlags(item.flags()^QtCore.Qt.ItemIsEditable)
            item.setTextAlignment(QtCore.Qt.AlignVCenter|QtCore.Qt.AlignCenter)
            item.setBackground(QtGui.QBrush(QtGui.QColor(background)))
            if player == winner:
                text = QtGui.QApplication.translate("RemigioRoundsDetail","Winner ({}x)").format(closeType)
                font = item.font()
                font.setBold(True)
                item.setFont(font)
            elif self.engine.isPlayerOff(player) or r.getPlayerScore(player) < 0:
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
        self.insertRound(r)
        self.plot.updatePlot()
        
        
class RemigioRoundPlot(GameRoundPlot):
    
    def initPlot(self):
        super(RemigioRoundPlot,self).initPlot()
        self.updatePlot()
        
    def updatePlot(self):
        super(RemigioRoundPlot,self).updatePlot()
        if not self.isPlotInited(): return
        scores = {}
        for player in self.engine.getPlayers():
            scores[player] = [0]
            
        for rnd in self.engine.getRounds():
            for player in self.engine.getPlayers():
                if player not in scores: scores[player] = [0]
                rndscore = rnd.getPlayerScore(player)
                if rndscore >= 0 :
                    accumscore = scores[player][-1] + rndscore
                    scores[player].append(accumscore)
                    
        self.canvas.clearPlotContents()
        self.canvas.addLimit(self.engine.getTop())
        for player in self.engine.getListPlayers():        
            self.canvas.addSeries(scores[player],player)

