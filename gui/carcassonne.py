#!/usr/bin/env python
# -*- coding: utf-8 -*-

# from gui.gamestatsfactory import QSBoxFactory
try:
    from PySide import QtCore,QtGui
    QtGui.QFileDialog.getOpenFileNameAndFilter = QtGui.QFileDialog.getOpenFileName
except ImportError as error:
    from PyQt4 import QtCore,QtGui
    QtCore.Signal = QtCore.pyqtSignal
    QtCore.Slot = QtCore.pyqtSlot

from controllers.carcassonneengine import CarcassonneEngine
from gui.game import GameWidget,ScoreSpinBox,GameRoundPlot,GamePlayerWidget,\
    PlayerColours
from gui.gamestats import QuickStatsBox,StatsTable


class CarcassonneWidget(GameWidget):

    bgcolors = [0xFFCC99,0xCCCCCC,0xFFFF99,0xCCFF99,0xCCFFCC]

    def createEngine(self):
        if self.game != 'Carcassonne':
            raise Exception("No engine for game {}".format(self.game))
            return
        self.engine = CarcassonneEngine()     

    def initUI(self):
        super(CarcassonneWidget,self).initUI()
 
        self.finishButton = QtGui.QPushButton(self.roundGroup)
        self.buttonGroupLayout.addWidget(self.finishButton)
        self.finishButton.clicked.connect(self.finish)
 
        self.gameInput = CarcassonneInputWidget(self.engine,self.bgcolors,self)
        self.gameInput.enterPressed.connect(self.commitRound)
        self.focussc = QtGui.QShortcut(QtGui.QKeySequence("Ctrl+A"), self, self.gameInput.setFocus)
        self.roundLayout.addWidget(self.gameInput)
        
        self.gameInput.placeCommitButton(self.commitRoundButton)
        
        self.detailGroup = CarcassonneEntriesDetail(self.engine, self.bgcolors,self)
        self.detailGroup.setStyleSheet("QGroupBox { font-size: 18px; font-weight: bold; }")
        self.widgetLayout.addWidget(self.detailGroup,1,0)        
        self.detailGroup.plot.plotCompleted.connect(self.gameInput.setFocus)
        self.detailGroup.entriesChanged.connect(self.updateScores)
        
        self.playerGroup = QtGui.QGroupBox(self)
        self.widgetLayout.addWidget(self.playerGroup,1,1)

        self.playerGroup.setStyleSheet("QGroupBox { font-size: 18px; font-weight: bold; }")
        self.playersLayout = QtGui.QVBoxLayout(self.playerGroup)
        self.playersLayout.addStretch()
        self.playerGroupBox = {}
        dealer = self.engine.getDealer()
        for i, player in enumerate(self.engine.getListPlayers()):
            pw = GamePlayerWidget(player, PlayerColours[i],self.playerGroup)
            
            if self.engine.getNumEntry() == 1 and player == dealer: pw.setDealer()
            pw.updateDisplay(self.engine.getScoreFromPlayer(player))
            self.playersLayout.addWidget(pw)
            self.playerGroupBox[player] = pw
 
        self.playersLayout.addStretch()
        self.retranslateUI()
        self.gameInput.setFocus()
        
    def retranslateUI(self):
        super(CarcassonneWidget,self).retranslateUI()
        self.finishButton.setText(QtGui.QApplication.translate("GameWidget","&Finish Game"))
        self.playerGroup.setTitle(QtGui.QApplication.translate("CarcassonneWidget","Score"))
        self.gameInput.retranslateUI()
        self.detailGroup.retranslateUI()
    
    
    def getPlayerExtraInfo(self,player):  
        kind = self.gameInput.getKind()
        if kind: return {'kind':kind}
        else: return None

    def updatePanel(self):
        super(CarcassonneWidget,self).updatePanel()
        self.updateScores()
        if self.engine.getWinner(): 
            self.finishButton.setDisabled(True)
            self.detailGroup.updateStats()
        else: self.detailGroup.updateRound()
        
    def checkPlayerScore(self,player,score): 
        if score > 0: return True
        else: return False
        
    def commitRound(self):        
        player = self.gameInput.getPlayer()
        kind = self.gameInput.getKind()
        score = self.gameInput.getScore()
        if player == "":
            QtGui.QMessageBox.warning(self,self.game,QtGui.QApplication.translate("CarcassonneWidget","You must select a player"))
            return
        
        if kind == "":
            QtGui.QMessageBox.warning(self,self.game,QtGui.QApplication.translate("CarcassonneWidget","You must select a kind"))
            return
        
        if not self.checkPlayerScore(player,score):
            QtGui.QMessageBox.warning(self,self.game,QtGui.QApplication.translate("GameWidget","{0} score is not valid").format(player))
            return

        #Everything ok so far, let's confirm
        ret = QtGui.QMessageBox.question(self, QtGui.QApplication.translate("CarcassonneWidget",'Commit Entry'),
        QtGui.QApplication.translate("CarcassonneWidget","Are you sure you want to commit this entry?"), QtGui.QMessageBox.Yes | 
        QtGui.QMessageBox.No, QtGui.QMessageBox.Yes)
        
        if ret == QtGui.QMessageBox.No: return

        # Once here, we can commit round
        self.playerGroupBox[self.engine.getDealer()].unsetDealer()
        self.engine.addEntry(player,score, {'kind': kind})
        self.engine.printStats()
        
        self.updatePanel()
    
    def finish(self): 
        ret = QtGui.QMessageBox.question(self, QtGui.QApplication.translate("CarcassonneWidget",'Finish game'),
        QtGui.QApplication.translate("CarcassonneWidget","Are you sure you want to finish the current game?"), QtGui.QMessageBox.Yes | 
        QtGui.QMessageBox.No, QtGui.QMessageBox.Yes)
        
        if ret == QtGui.QMessageBox.No: return
        self.engine.finishGame()
        self.updatePanel()
        
    def updateScores(self):
        for player in self.players:
            score = self.engine.getScoreFromPlayer(player)
            self.playerGroupBox[player].updateDisplay(score)

        
class CarcassonneInputWidget(QtGui.QWidget):
    
    enterPressed = QtCore.Signal()
    
    QtGui.QApplication.translate("CarcassonneInputWidget",'City')
    QtGui.QApplication.translate("CarcassonneInputWidget",'Road')
    QtGui.QApplication.translate("CarcassonneInputWidget",'Cloister')
    QtGui.QApplication.translate("CarcassonneInputWidget",'Field')
    QtGui.QApplication.translate("CarcassonneInputWidget",'Goods')
    
    def __init__(self,engine, bgcolors, parent=None):
        super(CarcassonneInputWidget,self).__init__(parent)
        self.engine = engine
        self.parent = parent
        self.bgcolors = bgcolors
        self.setStyleSheet("QGroupBox { font-size: 14px; font-weight: normal; }")
        self.initUI()

    def initUI(self):
        self.widgetLayout = QtGui.QHBoxLayout(self)
        self.playerGroup = QtGui.QGroupBox(self)
        self.widgetLayout.addWidget(self.playerGroup)
        self.playerButtonGroup = QtGui.QButtonGroup(self)
        self.playerGroupLayout = QtGui.QGridLayout(self.playerGroup)
        
        b = QtGui.QRadioButton("",self.playerGroup)
#        self.playerGroupLayout.addWidget(b)
        self.playerButtonGroup.addButton(b,0)
        self.playerButtons=[b]
        b.hide()
        for i, player in enumerate(self.engine.getListPlayers(),1):
            b = QtGui.QRadioButton('{}. {}'.format(i,player),self.playerGroup)
            if len(self.engine.getListPlayers())>2:
                self.playerGroupLayout.addWidget(b,(i-1)%2,(i-1)/2)
            else:
                self.playerGroupLayout.addWidget(b,0,(i-1)%2)
            self.playerButtonGroup.addButton(b,i)
            self.playerButtons.append(b)
        
        self.kindGroup = QtGui.QGroupBox(self)
        self.widgetLayout.addWidget(self.kindGroup)
        self.kindButtonGroup = QtGui.QButtonGroup(self)
        self.kindGroupLayout = QtGui.QGridLayout(self.kindGroup)
        
        b = QtGui.QRadioButton("",self.kindGroup)
#        self.kindGroupLayout.addWidget(b)
        self.kindButtonGroup.addButton(b,0)
        self.kindButtons=[b]
        b.hide()
        
        self.scoreSpinBox = ScoreSpinBox(self)
        self.scoreSpinBox.setAlignment(QtCore.Qt.AlignCenter)
        self.scoreSpinBox.setMaximumWidth(60)
        self.scoreSpinBox.setRange(0,300)

        for i, kind in enumerate(self.engine.getEntryKinds(),1):
            b = QtGui.QRadioButton('{}. {}'.format(i,QtGui.QApplication.translate("CarcassonneInputWidget",kind)),self.kindGroup)
            self.kindGroupLayout.addWidget(b,(i-1)%2,(i-1)/2)
            self.kindButtonGroup.addButton(b,i)
            b.clicked.connect(self.scoreSpinBox.setFocus)
            self.kindButtons.append(b)
            
        self.kindButtons[3].toggled.connect(self.setCloisterPoints)
        self.kindButtons[5].toggled.connect(self.setGoodsPoints)
        
        self.scoreGroup = QtGui.QGroupBox(self)
        self.widgetLayout.addWidget(self.scoreGroup)
        self.scoreGroupLayout = QtGui.QHBoxLayout(self.scoreGroup)     
        
        self.scoreGroupLayout.addWidget(self.scoreSpinBox)

        self.reset()
        self.retranslateUI()
        
    def retranslateUI(self):
        self.playerGroup.setTitle(QtGui.QApplication.translate("CarcassonneInputWidget","Select Player"))
        self.kindGroup.setTitle(QtGui.QApplication.translate("CarcassonneInputWidget","Select kind of entry"))
        self.scoreGroup.setTitle(QtGui.QApplication.translate("CarcassonneInputWidget","Points"))
        for i, kind in enumerate(self.engine.getEntryKinds(),1):
            text=QtGui.QApplication.translate("CarcassonneInputWidget",kind)
            self.kindButtons[i].setText('{}. {}'.format(i,text))
        
    def placeCommitButton(self,cb):
        self.scoreGroupLayout.addWidget(cb)
            
    def getPlayer(self): 
        pid = self.playerButtonGroup.checkedId()
        if not pid: return ""
        player = self.engine.getListPlayers()[pid-1]
        return str(player)
    
    def getKind(self): 
        cid = self.kindButtonGroup.checkedId()
        if not cid: return ""
        kind = self.engine.getEntryKinds()[cid-1]
        return str(kind)
    
    def getScore(self): return self.scoreSpinBox.value()
    
    def reset(self):
        self.playerButtons[0].setChecked(True)
        self.kindButtons[0].setChecked(True)
        self.scoreSpinBox.setValue(0)
        self.setFocus()
        
    def keyPressEvent(self,event):
        numberkeys = [QtCore.Qt.Key_1,QtCore.Qt.Key_2,QtCore.Qt.Key_3,
                      QtCore.Qt.Key_4,QtCore.Qt.Key_5,QtCore.Qt.Key_6,
                      QtCore.Qt.Key_7,QtCore.Qt.Key_8,QtCore.Qt.Key_9]
        try: number = numberkeys.index(event.key()) + 1
        except ValueError: number = 0
        if (event.key() == QtCore.Qt.Key_Return):
            self.enterPressed.emit()
        elif number:
            if not self.getPlayer():
                if number <= len(self.engine.getPlayers()):
                    self.playerButtons[number].setChecked(True)
            elif not self.getKind():
                if number <= len(self.engine.getEntryKinds()):
                    self.kindButtons[number].setChecked(True)
                    self.scoreSpinBox.setFocus()
            
        return super(CarcassonneInputWidget,self).keyPressEvent(event)
    
    def setCloisterPoints(self,doit):
        if doit: 
            self.scoreSpinBox.setValue(9)
            self.scoreSpinBox.setMaximum(9)
            self.scoreSpinBox.lineEdit().selectAll()
        else: 
            self.scoreSpinBox.setValue(0)
            self.scoreSpinBox.setMaximum(300)
            
    def setGoodsPoints(self,doit):
        if doit: 
            self.scoreSpinBox.setValue(10)
            self.scoreSpinBox.setReadOnly(True)

        else: 
            self.scoreSpinBox.setReadOnly(False)
            self.scoreSpinBox.setValue(0)
            
            
class CarcassonneEntriesDetail(QtGui.QGroupBox):
    
    entriesChanged = QtCore.Signal()
    
    def __init__(self, engine, bgcolors,parent=None):
        super(CarcassonneEntriesDetail, self).__init__(parent)
        self.engine = engine
        self.bgcolors = bgcolors
        self.initUI()

    def initUI(self):
        self.widgetLayout = QtGui.QVBoxLayout(self)
#        self.container = QtGui.QToolBox(self)
        self.container = QtGui.QTabWidget(self)
        self.widgetLayout.addWidget(self.container)
        
        self.tableContainer = QtGui.QFrame(self)
        self.tableContainerLayout = QtGui.QVBoxLayout(self.tableContainer)
        self.tableContainer.setAutoFillBackground(True)
        self.container.addTab(self.tableContainer,'')
        
        self.table = QtGui.QTableWidget(0,len(self.engine.getPlayers()))
        self.tableContainerLayout.addWidget(self.table,stretch=1)
        players = self.engine.getListPlayers()
        self.table.setHorizontalHeaderLabels(players)
        self.table.horizontalHeader().setResizeMode(QtGui.QHeaderView.Stretch)
        self.table.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self.openTableMenu)
        
        self.totalsLabel = QtGui.QLabel("",self)
        self.tableContainerLayout.addWidget(self.totalsLabel)
        
        self.totals = StatsTable(len(self.engine.getEntryKinds()),len(self.engine.getPlayers()))
        self.tableContainerLayout.addWidget(self.totals)
        self.totals.setHorizontalHeaderLabels(players)
        self.totals.horizontalHeader().setResizeMode(QtGui.QHeaderView.Stretch)
        self.totals.setMaximumHeight(self.totals.sizeHint().height())
        
        self.plot = CarcassonneEntriesPlot(self.engine,self)      
        self.plot.setAutoFillBackground(True)
#        self.container.addItem(self.plot,'')
        self.container.addTab(self.plot,'')

        self.statsFrame = QtGui.QWidget(self)
        self.statsFrame.setAutoFillBackground(True)
        self.container.addTab(self.statsFrame,'')

        self.statsLayout= QtGui.QVBoxLayout(self.statsFrame)
        self.gamestats = CarcassonneQSBox(self.statsFrame)
        self.statsLayout.addWidget(self.gamestats)

    def retranslateUI(self):
        self.setTitle(QtGui.QApplication.translate("CarcassonneEntriesDetail",'Details'))
        self.container.setTabText(0,QtGui.QApplication.translate("CarcassonneEntriesDetail","Table"))
        self.container.setTabText(1,QtGui.QApplication.translate("CarcassonneEntriesDetail","Plot"))
        self.container.setTabText(2,QtGui.QApplication.translate("CarcassonneEntriesDetail","Statistics"))
        self.totalsLabel.setText(QtGui.QApplication.translate("CarcassonneEntriesDetail","Totals"))
        self.totals.setVerticalHeaderLabels([QtGui.QApplication.translate("CarcassonneInputWidget",kind) for kind in self.engine.getEntryKinds()])
#        self.container.setItemText(0,QtGui.QApplication.translate("CarcassonneEntriesDetail","Table"))
#        self.container.setItemText(1,QtGui.QApplication.translate("CarcassonneEntriesDetail","Plot"))
#        self.container.setItemText(2,QtGui.QApplication.translate("CarcassonneEntriesDetail","Statistics"))
        self.gamestats.retranslateUI()
        self.recomputeTable()

    def updatePlot(self):
        self.plot.updatePlot()
        
    def resetTotals(self):
        self.totals.clearContents()
        for row in range(len(self.engine.getEntryKinds())):
            background=self.bgcolors[row]
            for col in range(len(self.engine.getListPlayers())):
                item = QtGui.QTableWidgetItem()
                item.setFlags(item.flags()^QtCore.Qt.ItemIsEditable)
                item.setTextAlignment(QtCore.Qt.AlignVCenter|QtCore.Qt.AlignCenter)
                item.setBackground(QtGui.QBrush(QtGui.QColor(background)))
                item.setText("0")
                self.totals.setItem(row,col,item)

    def recomputeTable(self):
        self.table.clearContents()
        self.table.setRowCount(0)
        self.resetTotals()
        for r in self.engine.getEntries(): self.insertEntry(r)
        self.updatePlot()
    
    def insertEntry(self,entry):
        kind = entry.getKind()
        kinds = self.engine.getEntryKinds()
        background = self.bgcolors[kinds.index(kind)]
        kind = QtGui.QApplication.translate("CarcassonneInputWidget",kind)
        i = entry.getNumEntry() - 1
        self.table.insertRow(i)
        for j, player in enumerate(self.engine.getListPlayers()):
            item = QtGui.QTableWidgetItem()
            item.setFlags(item.flags()^QtCore.Qt.ItemIsEditable)
            item.setTextAlignment(QtCore.Qt.AlignVCenter|QtCore.Qt.AlignCenter)
            item.setBackground(QtGui.QBrush(QtGui.QColor(background)))

            if player == entry.getPlayer():
                text = "{} ({})".format(entry.getScore(),kind)
                font = item.font()
                font.setBold(True)
                item.setFont(font)
                totalItem = self.totals.item(kinds.index(entry.getKind()),j)
                totalItem.setText(str(int(totalItem.text())+entry.getScore()))       
            else:
                text = ""
            item.setText(text)
            self.table.setItem(i,j,item)
        self.table.scrollToBottom()
        self.recomputeMaxTotals()            
        
    def updateRound(self):
        entries = self.engine.getEntries()
        if not len(entries): return
        e = entries[-1]
        self.insertEntry(e)
        self.plot.updatePlot()
        
    def updateStats(self):
        self.gamestats.update()
        
    def recomputeMaxTotals(self):
        for row in range(len(self.engine.getEntryKinds())):
            maxvalue = 1
            for col in range(len(self.engine.getListPlayers())):
                total = int(self.totals.item(row,col).text())
                if total>maxvalue:
                    maxvalue = total
            for col in range(len(self.engine.getListPlayers())):
                item = self.totals.item(row,col)
                font = item.font()
                font.setBold(int(item.text())==maxvalue)
                item.setFont(font)
    
    def openTableMenu(self,position):
        item = self.table.indexAt(position)
        nentry = item.row() + 1
        if nentry<=0 or self.engine.getWinner(): return
        
        menu = QtGui.QMenu()
        deleteEntryAction = QtGui.QAction(QtGui.QIcon('icons/delete.png'),QtGui.QApplication.translate("CarcassonneEntriesDetail","Delete Entry"), self)
        menu.addAction(deleteEntryAction)
        action = menu.exec_(self.table.mapToGlobal(position))
        if action == deleteEntryAction:
            ret = QtGui.QMessageBox.question(self, QtGui.QApplication.translate("CarcassonneEntriesDetail",'Delete Entry'),
            QtGui.QApplication.translate("CarcassonneEntriesDetail","Are you sure you want to delete this entry?"), QtGui.QMessageBox.Yes | 
            QtGui.QMessageBox.No, QtGui.QMessageBox.Yes)
            if ret == QtGui.QMessageBox.No: return
            entry = self.engine.getEntries()[nentry-1]
            kind = entry.getKind()
            player = entry.getPlayer()
            score = entry.getScore()
            total = self.totals.item(self.engine.getEntryKinds().index(kind),self.engine.getListPlayers().index(player))
            total.setText(str(int(total.text())-score))       
            self.recomputeMaxTotals()
            self.engine.deleteEntry(nentry)
            self.entriesChanged.emit()
            self.table.removeRow(item.row())
            self.plot.updatePlot()
       
        
class CarcassonneEntriesPlot(GameRoundPlot):
    
    def initPlot(self):
        super(CarcassonneEntriesPlot,self).initPlot()
        self.updatePlot()
        
    def updatePlot(self):
        if not self.isPlotInited(): return
        super(CarcassonneEntriesPlot,self).updatePlot()
        scores = {}
        for player in self.engine.getPlayers():
            scores[player] = [0]
            
        for entry in self.engine.getEntries():
            for player in self.engine.getPlayers():
                if player == entry.getPlayer(): entryscore = entry.getScore()
                else: entryscore = 0
                accumscore = scores[player][-1] + entryscore
                scores[player].append(accumscore)
        
        self.canvas.clearPlotContents()
        
        for player in self.engine.getListPlayers():        
            self.canvas.addSeries(scores[player],player)
        


class CarcassonneQSBox(QuickStatsBox):
    
    def __init__(self,parent = None):
        self.game = "Carcassonne"
        super(CarcassonneQSBox,self).__init__(self.game,parent)
          
    def initUI(self):
        self.singleRecordsLabel = QtGui.QLabel(self)
        self.singleRecordsTable = StatsTable(self)
        self.matchRecordsLabel = QtGui.QLabel(self)
        self.matchRecordsTable = StatsTable(self)        
        
        super(CarcassonneQSBox, self).initUI()
        index=self.widgetLayout.count()-1
#         self.widgetLayout.addWidget(self.singleRecordsLabel)
#         self.widgetLayout.addWidget(self.singleRecordsTable)
        self.widgetLayout.insertWidget(index,self.singleRecordsLabel)
        self.widgetLayout.insertWidget(index+1,self.singleRecordsTable)
        self.widgetLayout.insertWidget(index+2,self.matchRecordsLabel)
        self.widgetLayout.insertWidget(index+3,self.matchRecordsTable)
        
    def retranslateUI(self):
        self.singleRecordsLabel.setText(QtGui.QApplication.translate("CarcassonneQSBox","Records"))
        self.matchRecordsLabel.setText(QtGui.QApplication.translate("CarcassonneQSBox","Match Records"))
        super(CarcassonneQSBox, self).retranslateUI()
        
    def update(self,game=None):
        super(CarcassonneQSBox, self).update(game)
        singleRecordStats = self.stats.getSingleKindRecords()
        matchRecordStats = self.stats.getMatchKindRecords()

        if not singleRecordStats: self.singleRecordsLabel.hide()
        else: self.singleRecordsLabel.show()
            
        for row in singleRecordStats:
            row['record'] = QtGui.QApplication.translate("CarcassonneInputWidget",row['record'])
            
        for row in matchRecordStats:
            row['record'] = QtGui.QApplication.translate("CarcassonneInputWidget",row['record'])

        keys = ['points','player','date']
        headers = [QtGui.QApplication.translate("CarcassonneQSBox",'Record'),QtGui.QApplication.translate("CarcassonneQSBox",'Player'),QtGui.QApplication.translate("CarcassonneQSBox",'Date')]
        self.updateTable(self.singleRecordsTable, singleRecordStats, keys, 'record', headers)
        self.updateTable(self.matchRecordsTable, matchRecordStats, keys, 'record', headers)
        
