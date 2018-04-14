#!/usr/bin/env python
# -*- coding: utf-8 -*-

try:
    from PyQt4 import QtCore,QtGui
    QtCore.Signal = QtCore.pyqtSignal
    QtCore.Slot = QtCore.pyqtSlot
except ImportError as error:
    from PySide import QtCore,QtGui
    QtGui.QFileDialog.getOpenFileNameAndFilter = QtGui.QFileDialog.getOpenFileName
    
import ctypes
       
from gui.tab import Tab
from gui.clock import GameClock
from gui.plots import PlotView
from gui.gamestats import QuickStatsTW
from gui.playerlist import PlayerOrderDialog
        
PlayerColours=[QtGui.QColor(237,44,48),
         QtGui.QColor(23,89,169),
         QtGui.QColor(0,140,70),
         QtGui.QColor(243,124,33),
         QtGui.QColor(101,43,145),
         QtGui.QColor(161,29,33),
         QtGui.QColor(179,56,148)
         ]

class GameWidget(Tab):

    def __init__(self, game, players, engine = None, parent=None):
        super(GameWidget, self).__init__(parent)
        self.game = game
        if engine is not None:
            self.engine = engine
            self.players = self.engine.getListPlayers()
        else:
            self.players = players
            self.createEngine()  
            for nick in players: self.engine.addPlayer(nick)
            self.engine.begin()
        self.engine.printStats()
        self.gameInput = None
        self.finished = False
        self.toggleScreenLock()
        self.initUI()
        
    def initUI(self):
        #Set up the main grid
        self.setStyleSheet("QGroupBox { font-size: 32px; font-weight: bold; }")
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
        
        self.playerOrderButton = QtGui.QPushButton(self.roundGroup)
        self.buttonGroupLayout.addWidget(self.playerOrderButton)
        self.playerOrderButton.clicked.connect(self.changePlayerOrder)

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
        if dpolicy not in (self.engine.NoDealer,self.engine.StarterDealer):
            self.dealerPolicyCheckBox = QtGui.QCheckBox(self.matchGroup)
            if self.engine.getDealingPolicy() == self.engine.WinnerDealer:
                self.dealerPolicyCheckBox.setChecked(True)
            else:
                self.dealerPolicyCheckBox.setChecked(False)
            self.dealerPolicyCheckBox.setStyleSheet("QCheckBox { font-weight: bold; }")
            self.dealerPolicyCheckBox.stateChanged.connect(self.changeDealingPolicy)
            self.dealerPolicyCheckBox.setDisabled(self.engine.getNumRound()>1)
            self.matchGroupLayout.addWidget(self.dealerPolicyCheckBox)
        
    def retranslateUI(self):
        self.setRoundTitle()
        self.pauseMatchButton.setText(QtGui.QApplication.translate("GameWidget","&Pause/Play"))
        self.cancelMatchButton.setText(QtGui.QApplication.translate("GameWidget","&Cancel Match"))
        self.commitRoundButton.setText(QtGui.QApplication.translate("GameWidget","Commit &Round"))
        self.playerOrderButton.setText(QtGui.QApplication.translate("GameWidget","Player &Order"))
#         self.matchGroup.setTitle(QtGui.QApplication.translate("GameWidget","Match"))
        if self.engine.getDealingPolicy() not in (self.engine.NoDealer,self.engine.StarterDealer): 
            self.dealerPolicyCheckBox.setText(QtGui.QApplication.translate("GameWidget","Winner deals"))
        self.updateGameStatusLabel()
    
    def updateGameStatusLabel(self):
        self.gameStatusLabel.setStyleSheet("QLabel { font-size: 16px; font-weight:bold; color: red;}")    
        winner = self.engine.getWinner()
        if winner:
            self.gameStatusLabel.setText(QtGui.QApplication.translate("GameWidget","{} won this match!").format(winner))
        elif self.engine.isPaused():
            self.gameStatusLabel.setText(QtGui.QApplication.translate("GameWidget","Game is paused"))
        else:
            self.gameStatusLabel.setText(QtGui.QApplication.translate("GameWidget",""))      
    
    def cancelMatch(self):
        if not self.isFinished():
            ret = QtGui.QMessageBox.question(self, QtGui.QApplication.translate("GameWidget",'Cancel Match'),
            QtGui.QApplication.translate("GameWidget","Do you want to save the current {} match?").format(self.game), QtGui.QMessageBox.Yes | 
            QtGui.QMessageBox.No | QtGui.QMessageBox.Cancel, QtGui.QMessageBox.Cancel)
            
            if ret == QtGui.QMessageBox.Cancel: return
            if ret == QtGui.QMessageBox.No:
                self.closeMatch()
            else:
                self.saveMatch()
                
        self.toggleScreenLock(True)
        self.requestClose()
        
    def pauseMatch(self):
        if self.engine.isPaused():
            self.clock.unpauseTimer()
            self.commitRoundButton.setEnabled(True)
            self.gameInput.setEnabled(True)
            self.engine.unpause()
            self.toggleScreenLock()
        else:
            self.clock.pauseTimer()
            self.commitRoundButton.setDisabled(True)
            self.gameInput.setDisabled(True)
            self.engine.pause()
            self.toggleScreenLock(True)
        self.updateGameStatusLabel()
            
    def commitRound(self):
        
        nround = self.engine.getNumRound()
        print("Opening round {}".format(nround))
        self.engine.openRound(nround)
        winner = self.gameInput.getWinner()
        if not winner:
            QtGui.QMessageBox.warning(self,self.game,QtGui.QApplication.translate("GameWidget","No winner selected"))
            return
        else:
            self.engine.setRoundWinner(winner)
        scores = self.gameInput.getScores()
        for player,score in scores.items():
            if not self.checkPlayerScore(player,score):
                QtGui.QMessageBox.warning(self,self.game,QtGui.QApplication.translate("GameWidget","{0} score is not valid").format(player))
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
        
    def setRoundTitle(self):
        try:
            nround = self.engine.getNumRound()
            self.roundGroup.setTitle(QtGui.QApplication.translate("GameWidget","Round {0}").format(str(nround)))
        except AttributeError: pass
        
    def updatePanel(self):
        self.gameInput.reset()
        try: self.dealerPolicyCheckBox.setEnabled(False)
        except AttributeError: pass
        if self.engine.getWinner():
            self.setWinner()
        else:
            self.setRoundTitle()
            
    def getGameName(self): return self.game        
    
    def isFinished(self): return self.finished
    
    #To be implemented in subclasses
    def createEngine(self): pass
    
    def getPlayerExtraInfo(self,player):  return {}
    
    def unsetDealer(self): pass
    
    def setDealer(self): pass
    
    def setWinner(self):
        self.finished = True
        self.pauseMatchButton.setDisabled(True)
        self.clock.stopTimer()
        self.commitRoundButton.setDisabled(True)
        self.playerOrderButton.setDisabled(True)
        self.updateGameStatusLabel()    
        self.gameInput.setDisabled(True)
        self.toggleScreenLock(True)
        
    def changePlayerOrder(self):
        originaldealer = self.engine.getDealer()
        pod = PlayerOrderDialog(self.engine,self)
#         pod.dealerChanged.connect(self.changedDealer)
        if pod.exec_():
            newdealer = pod.getNewDealer()
            neworder = pod.getNewOrder()
            if self.players != neworder:
                # Do something
                self.engine.setListPlayers(neworder)
                self.players = neworder
                self.updatePlayerOrder()
            if originaldealer != newdealer:
                self.unsetDealer()
                self.engine.setDealer(newdealer)
                self.setDealer()
        
    def updatePlayerOrder(self):
        self.gameInput.updatePlayerOrder()
        
    def toggleScreenLock(self,on=False):
        ES_CONTINUOUS        = 0x80000000
        ES_DISPLAY_REQUIRED  = 0x00000002
        try:
            if not on:
                ctypes.windll.kernel32.SetThreadExecutionState(ES_CONTINUOUS | ES_DISPLAY_REQUIRED)
                print("Disabled Screensaver")
            else:
                ctypes.windll.kernel32.SetThreadExecutionState(0)
                print("Enabled Screensaver")
        except:
            pass


class GameInputWidget(QtGui.QWidget):
    
    enterPressed = QtCore.Signal()
    
    def __init__(self,engine,parent=None):
        super(GameInputWidget,self).__init__(parent)
        self.engine = engine
        self.winnerSelected = ""
        self.playerInputList = {}
            
    def getWinner(self):
        maxScore = -1000000
        for player,score in self.getScores().items():
            if score > maxScore:
                maxScore = score
                self.winnerSelected = player
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
        if event.key() in (QtCore.Qt.Key_Return, QtCore.Qt.Key_Enter):
            self.enterPressed.emit()
            event.accept()
        return super(GameInputWidget,self).keyPressEvent(event)
        
    def mousePressEvent(self,event):
        self.setFocus()
        return QtGui.QWidget.mousePressEvent(self, event)
    
    def updatePlayerOrder(self): pass
        
        
class ScoreSpinBox(QtGui.QSpinBox):
    
    def __init__(self,*args,**kwargs):
        super(ScoreSpinBox,self).__init__(*args,**kwargs)
        self.setAccelerated(True)

    def valueFromText(self,text):
        if text == "": return self.minimum()
        else: return super(ScoreSpinBox,self).valueFromText(text)
        
    def textFromValue(self,value):
        if value == self.minimum(): return ""
        else: return super(ScoreSpinBox,self).textFromValue(value)        
        
class IconLabel(QtGui.QLabel):
#     def __init__(self,parent = None):
#         super(IconLabel,self).__init__(parent)
#         self._pixmap = None
#     def setPixmap(self,pixmap):
#         self._pixmap = pixmap
#         super(IconLabel,self).setPixmap(pixmap)
#     def resizeEvent(self, event):
#         size = min(self.width(), self.height())
#         self.setFixedSize(size,size)
#         if self._pixmap and not self._pixmap.isNull():
#             print(event)
#             self.setPixmap(self._pixmap.scaled(size, size,QtCore.Qt.KeepAspectRatio, QtCore.Qt.SmoothTransformation))
    def setDisabled(self,b): pass
    def setEnabled(self,b): pass
    

class GamePlayerWidget(QtGui.QGroupBox):
    
    def __init__(self,nick,colour=None,parent = None):
        super(GamePlayerWidget,self).__init__(parent)
        self.player = nick
        self.pcolour=colour
        self.initUI()
        
    def initUI(self):
#        self.setMinimumWidth(300)
        self.mainLayout = QtGui.QHBoxLayout(self)
#         self.mainLayout.addStretch()
        self.scoreLCD = QtGui.QLCDNumber(self)
        self.scoreLCD.setSegmentStyle(QtGui.QLCDNumber.Flat)
        self.mainLayout.addWidget(self.scoreLCD)
        self.scoreLCD.setNumDigits(3)
        self.scoreLCD.setFixedSize(100,60)
        self.scoreLCD.display(0)
        self.scoreLCD.setStyleSheet("QLCDNumber {{ color:rgb({},{},{});}}".format(self.pcolour.red(),self.pcolour.green(),self.pcolour.blue()))
        
        self.nameLabel = QtGui.QLabel(self)
        self.nameLabel.setText(self.player)
        sh = "QLabel {{ font-size: 32px; font-weight: bold; color:rgb({},{},{});}}".format(self.pcolour.red(),self.pcolour.green(),self.pcolour.blue())
        self.nameLabel.setStyleSheet(sh)
        self.mainLayout.addWidget(self.nameLabel)
        
        self.dealerPixmap = QtGui.QPixmap('icons/cards.png')
        self.nonDealerPixmap = QtGui.QPixmap()
        self.winnerPixmap = QtGui.QPixmap('icons/winner.png')
        
        self.iconlabel = IconLabel(self)
        self.iconlabel.setFixedSize(50,50)
        self.iconlabel.setScaledContents(True)
        self.mainLayout.insertWidget(0,self.iconlabel)
#         self.mainLayout.addStretch()
        self.unsetDealer()
        
    def updateDisplay(self,points):
        if points >= 1000: self.scoreLCD.setNumDigits(4)
        self.scoreLCD.display(points)

    def setDealer(self): self.iconlabel.setPixmap(self.dealerPixmap)

    def unsetDealer(self): self.iconlabel.setPixmap(self.nonDealerPixmap)
    
    def setWinner(self): self.iconlabel.setPixmap(self.winnerPixmap)
    
    def setColour(self,colour):
        self.pcolour = colour
        self.scoreLCD.setStyleSheet("QLCDNumber {{ color:rgb({},{},{});}}".format(self.pcolour.red(),self.pcolour.green(),self.pcolour.blue()))
        sh = "QLabel {{ font-size: 32px; font-weight: bold; color:rgb({},{},{});}}".format(self.pcolour.red(),self.pcolour.green(),self.pcolour.blue())
        self.nameLabel.setStyleSheet(sh)


class GameRoundsDetail(QtGui.QGroupBox):
    
    edited = QtCore.Signal()
    
    def __init__(self, engine, parent=None):
        super(GameRoundsDetail, self).__init__(parent)
        self.engine = engine
        self.initUI()

    def initUI(self):
        self.setStyleSheet("QGroupBox { font-size: 18px; font-weight: bold; }")
        self.widgetLayout = QtGui.QVBoxLayout(self)
#        self.container = QtGui.QToolBox(self)
        self.container = QtGui.QTabWidget(self)
        self.widgetLayout.addWidget(self.container)
        
        self.tableContainer = QtGui.QFrame(self)
        self.tableContainerLayout = QtGui.QVBoxLayout(self.tableContainer)
        self.tableContainer.setAutoFillBackground(True)
        self.container.addTab(self.tableContainer,'')
        
        self.table = self.createRoundTable(self.engine, self)
        self.tableContainerLayout.addWidget(self.table,stretch=1)
        self.table.edited.connect(self.updateRound)
        self.table.edited.connect(self.edited.emit)
        
        self.plot = self.createRoundPlot(self.engine,self)      
        self.plot.setAutoFillBackground(True)
#        self.container.addItem(self.plot,'')
        self.container.addTab(self.plot,'')

        self.statsFrame = QtGui.QWidget(self)
        self.statsFrame.setAutoFillBackground(True)
        self.container.addTab(self.statsFrame,'')

        self.statsLayout= QtGui.QVBoxLayout(self.statsFrame)
        self.gamestats = self.createQSBox(self.statsFrame)
        self.statsLayout.addWidget(self.gamestats)

    def retranslateUI(self):
#         self.setTitle(QtGui.QApplication.translate("GameRoundsDetail",'Details'))
        self.container.setTabText(0,QtGui.QApplication.translate("GameRoundsDetail","Table"))
        self.container.setTabText(1,QtGui.QApplication.translate("GameRoundsDetail","Plot"))
        self.container.setTabText(2,QtGui.QApplication.translate("GameRoundsDetail","Statistics"))
#        self.container.setItemText(0,QtGui.QApplication.translate("CarcassonneEntriesDetail","Table"))
#        self.container.setItemText(1,QtGui.QApplication.translate("CarcassonneEntriesDetail","Plot"))
#        self.container.setItemText(2,QtGui.QApplication.translate("CarcassonneEntriesDetail","Statistics"))
        self.gamestats.retranslateUI()
        self.plot.retranslateUI()
        self.updateRound()

    def updatePlot(self):
        self.plot.updatePlot()
        
    def updateRound(self):
        self.table.resetClear()
        for r in self.engine.getRounds(): self.table.insertRound(r)
        self.updatePlot()      
        
    def updateStats(self):
        try:
            self.gamestats.update(self.engine.getGame(), self.engine.getListPlayers())
        except:
            self.gamestats.update()
    
    def deleteRound(self,nround):
        self.plot.updatePlot()
        
    # Implement in subclasses if necessary
    def createRoundTable(self, engine, parent=None) : return GameRoundTable(self)
    def createRoundPlot(self, engine, parent=None): return GameRoundPlot(self)
    def createQSBox(self, parent=None): return QuickStatsTW(self.engine.getGame(), self.engine.getListPlayers(), self)
    
    def updatePlayerOrder(self): 
        self.updateRound()


class GameRoundTable(QtGui.QTableWidget):
    
    edited = QtCore.Signal()
    
    def __init__(self,engine,parent=None):
        super(GameRoundTable, self).__init__(parent)
        self.engine = engine
        self.setColumnCount(len(self.engine.getListPlayers()))
        self.initUI()
        
    def initUI(self):
        self.setHorizontalHeaderLabels(self.engine.getListPlayers())
        self.horizontalHeader().setResizeMode(QtGui.QHeaderView.Stretch)
        self.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.openTableMenu)    
        
    def resetClear(self):
        self.setHorizontalHeaderLabels(self.engine.getListPlayers())
        self.clearContents()
        self.setRowCount(0)
        
    def openTableMenu(self,position):
        item = self.indexAt(position)
        nentry = item.row() + 1
        if nentry<=0 or self.engine.getWinner(): return
        
        menu = QtGui.QMenu()
        deleteEntryAction = QtGui.QAction(QtGui.QIcon('icons/delete.png'),QtGui.QApplication.translate("GameRoundTable","Delete Entry"), self)
        menu.addAction(deleteEntryAction)
        action = menu.exec_(self.mapToGlobal(position))
        if action == deleteEntryAction:
            ret = QtGui.QMessageBox.question(self, QtGui.QApplication.translate("GameRoundTable",'Delete Entry'),
            QtGui.QApplication.translate("GameRoundTable","Are you sure you want to delete this entry?"), QtGui.QMessageBox.Yes | 
            QtGui.QMessageBox.No, QtGui.QMessageBox.Yes)
            if ret == QtGui.QMessageBox.No: return
            self.engine.deleteRound(nentry)
            self.removeRow(item.row())
            self.edited.emit()
            
    #ReImplement in subclasses
    def insertRound(self,rnd): pass


class GameRoundPlot(QtGui.QWidget):
    def __init__(self,engine,parent=None):
        super(GameRoundPlot, self).__init__(parent)
        self.plotinited = False
        self.engine = engine
        self.parent = parent
        self.axiswidth = 0
        self.initUI()
        
    def initUI(self):
        self.widgetLayout = QtGui.QHBoxLayout(self)
        self.canvas = PlotView(PlayerColours,self)
        self.canvas.setBackground(self.palette().color(self.backgroundRole()))
        self.canvas.addLinePlot()
        self.widgetLayout.addWidget(self.canvas)
        self.plotinited = True
            
    def retranslateUI(self): self.retranslatePlot()
    
    def isPlotInited(self): return self.plotinited
        
    def updatePlot(self): pass
    
    def retranslatePlot(self): pass
    

        