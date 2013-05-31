#!/usr/bin/env python
# -*- coding: utf-8 -*-

try:
    from PySide import QtCore,QtGui
    QtGui.QFileDialog.getOpenFileNameAndFilter = QtGui.QFileDialog.getOpenFileName
except ImportError as error:
    from PyQt4 import QtCore,QtGui
    QtCore.Signal = QtCore.pyqtSignal
    QtCore.Slot = QtCore.pyqtSlot
    
try: import matplotlib
except ImportError: pass

from controllers.carcassoneengine import CarcassoneEngine
from gui.game import GameWidget,ScoreSpinBox,GameRoundPlot


class CarcassoneWidget(GameWidget):

    bgcolors = [0xFFCC99,0xCCCCCC,0xFFFF99,0xCCFF99,0xCCFFCC]

    def createEngine(self):
        if self.game != 'Carcassone':
            raise Exception("No engine for game {}".format(self.game))
            return
        self.engine = CarcassoneEngine()     

    def initUI(self):
        super(CarcassoneWidget,self).initUI()
 
        self.finishButton = QtGui.QPushButton(self.roundGroup)
        self.buttonGroupLayout.addWidget(self.finishButton)
        self.finishButton.clicked.connect(self.finish)
 
        self.gameInput = CarcassoneInputWidget(self.engine,self.bgcolors,self)
        self.gameInput.enterPressed.connect(self.commitRound)
        self.focussc = QtGui.QShortcut(QtGui.QKeySequence("Ctrl+A"), self, self.gameInput.setFocus)
        self.roundLayout.addWidget(self.gameInput)
        
        self.gameInput.placeCommitButton(self.commitRoundButton)
        
        self.detailGroup = CarcassoneEntriesDetail(self.engine, self.bgcolors,self)
        self.detailGroup.setStyleSheet("QGroupBox { font-size: 18px; font-weight: bold; }")
        self.widgetLayout.addWidget(self.detailGroup,1,0)        
        
        self.playerGroup = QtGui.QGroupBox(self)
        self.widgetLayout.addWidget(self.playerGroup,1,1)

        self.playerGroup.setStyleSheet("QGroupBox { font-size: 18px; font-weight: bold; }")
        self.playersLayout = QtGui.QVBoxLayout(self.playerGroup)
        self.playersLayout.addStretch()
        self.playerGroupBox = {}
        for player in self.players:
            pw = CarcassonePlayerWidget(player,self.playerGroup)
            pw.updateDisplay(self.engine.getScoreFromPlayer(player))
            self.playersLayout.addWidget(pw)
            self.playerGroupBox[player] = pw
 
        self.playersLayout.addStretch()
        self.retranslateUI()
        
    def retranslateUI(self):
        super(CarcassoneWidget,self).retranslateUI()
        self.finishButton.setText(QtGui.QApplication.translate("GameWidget","&Finish Game"))
        self.playerGroup.setTitle(QtGui.QApplication.translate("CarcassoneWidget","Score"))
        self.gameInput.retranslateUI()
        self.detailGroup.retranslateUI()
    
    
    def getPlayerExtraInfo(self,player):  
        kind = self.gameInput.getKind()
        if kind: return {'kind':kind}
        else: return None

    def updatePanel(self):
        super(CarcassoneWidget,self).updatePanel()
        for player in self.players:
            score = self.engine.getScoreFromPlayer(player)
            self.playerGroupBox[player].updateDisplay(score)

        if self.engine.getWinner(): self.finishButton.setDisabled(True)
        else: self.detailGroup.updateRound()
        
    def checkPlayerScore(self,player,score): 
        if score > 0: return True
        else: return False
        
    def commitRound(self):        
        player = self.gameInput.getPlayer()
        kind = self.gameInput.getKind()
        score = self.gameInput.getScore()
        
        if player == "":
            QtGui.QMessageBox.warning(self,self.game,unicode(QtGui.QApplication.translate("CarcassoneWidget","You must select a player")))
            return
        
        if kind == "":
            QtGui.QMessageBox.warning(self,self.game,unicode(QtGui.QApplication.translate("CarcassoneWidget","You must select a kind")))
            return
        
        if not self.checkPlayerScore(player,score):
            QtGui.QMessageBox.warning(self,self.game,unicode(QtGui.QApplication.translate("GameWidget","{0} score is not valid")).format(player))
            return

        #Everything ok so far, let's confirm
        ret = QtGui.QMessageBox.question(self, QtGui.QApplication.translate("CarcassoneWidget",'Commit Entry'),
        QtGui.QApplication.translate("CarcassoneWidget","Are you sure you want to commit this entry?"), QtGui.QMessageBox.Yes | 
        QtGui.QMessageBox.No, QtGui.QMessageBox.Yes)
        
        if ret == QtGui.QMessageBox.No: return

        # Once here, we can commit round
        self.engine.addEntry(player,score, {'kind': kind})
        self.engine.printStats()
        self.updatePanel()

    
    def finish(self): 
        ret = QtGui.QMessageBox.question(self, QtGui.QApplication.translate("CarcassoneWidget",'Finish game'),
        QtGui.QApplication.translate("CarcassoneWidget","Are you sure you want to finish the current game?"), QtGui.QMessageBox.Yes | 
        QtGui.QMessageBox.No, QtGui.QMessageBox.Yes)
        
        if ret == QtGui.QMessageBox.No: return
        self.engine.finishGame()
        self.updatePanel()
        
        
class CarcassoneInputWidget(QtGui.QWidget):
    
    enterPressed = QtCore.Signal()
    
    def __init__(self,engine, bgcolors, parent=None):
        super(CarcassoneInputWidget,self).__init__(parent)
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
            b = QtGui.QRadioButton('{}. {}'.format(i,QtGui.QApplication.translate("CarcassoneInputWidget",kind)),self.kindGroup)
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
        self.playerGroup.setTitle(QtGui.QApplication.translate("CarcassoneInputWidget","Select Player"))
        self.kindGroup.setTitle(QtGui.QApplication.translate("CarcassoneInputWidget","Select kind of entry"))
        self.scoreGroup.setTitle(QtGui.QApplication.translate("CarcassoneInputWidget","Points"))
        
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
            
        return super(CarcassoneInputWidget,self).keyPressEvent(event)
    
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
            
    
class CarcassonePlayerWidget(QtGui.QWidget):
    
    def __init__(self,nick,parent = None):
        super(CarcassonePlayerWidget,self).__init__(parent)
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
        self.nameLabel.setStyleSheet("QLabel { font-size: 18px; font-weight: bold; color: black}")
        self.mainLayout.addWidget(self.nameLabel)
        
    def updateDisplay(self,points):
        if points >= 1000: self.scoreLCD.setNumDigits(4)
        self.scoreLCD.display(points)
        
            
class CarcassoneEntriesDetail(QtGui.QGroupBox):
    
    def __init__(self, engine, bgcolors,parent=None):
        super(CarcassoneEntriesDetail, self).__init__(parent)
        self.engine = engine
        self.bgcolors = bgcolors
        self.initUI()

    def initUI(self):
        self.widgetLayout = QtGui.QVBoxLayout(self)
        self.container = QtGui.QToolBox(self)
        self.widgetLayout.addWidget(self.container)
        self.table = QtGui.QTableWidget(0,len(self.engine.getPlayers()))
        self.container.addItem(self.table,'')
#        self.widgetLayout.addWidget(self.table)
        players = self.engine.getListPlayers()
        self.table.setHorizontalHeaderLabels(players)
        self.table.horizontalHeader().setResizeMode(QtGui.QHeaderView.Stretch)
        
        self.plot = CarcassoneEntriesPlot(self.engine,self)
        self.container.addItem(self.plot,'')
        
#        self.retranslateUI()
        
    def retranslateUI(self):
        self.setTitle(QtGui.QApplication.translate("CarcassoneEntriesDetail",'Details'))
        self.container.setItemText(0,QtGui.QApplication.translate("CarcassoneEntriesDetail","Table"))
        self.container.setItemText(1,QtGui.QApplication.translate("CarcassoneEntriesDetail","Plot"))
        self.recomputeTable()


    def updatePlot(self):
        self.plot.updatePlot()

    def recomputeTable(self):
        self.table.clearContents()
        self.table.setRowCount(0)
        for r in self.engine.getEntries(): self.insertEntry(r)
        self.updatePlot()
    
    def insertEntry(self,entry):
        kind = entry.getKind()
        kinds = self.engine.getEntryKinds()
        background = self.bgcolors[kinds.index(kind)]
        kind = QtGui.QApplication.translate("CarcassoneInputWidget",kind)
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
            else:
                text = ""
            item.setText(text)
            self.table.setItem(i,j,item)
        self.table.scrollToBottom()
        
    def updateRound(self):
        entries = self.engine.getEntries()
        if not len(entries): return
        e = entries[-1]
        self.insertEntry(e)
        self.plot.updatePlot()
        
        
class CarcassoneEntriesPlot(GameRoundPlot):
    
    def initPlot(self):
        super(CarcassoneEntriesPlot,self).initPlot()
        self.axes = self.figure.add_subplot(111)
        self.updatePlot()
        
    def updatePlot(self):
        super(CarcassoneEntriesPlot,self).updatePlot()
        if not self.isPlotLibAvailable() or not self.isPlotInited(): return
        scores = {}
        for player in self.engine.getPlayers():
            scores[player] = [0]
            
        for entry in self.engine.getEntries():
            for player in self.engine.getPlayers():
                if player == entry.getPlayer(): entryscore = entry.getScore()
                else: entryscore = 0
                accumscore = scores[player][-1] + entryscore
                scores[player].append(accumscore)
        self.axes.cla()
        self.axes.set_axis_bgcolor('none')
        maxscore = max([self.engine.getScoreFromPlayer(player) for player in self.engine.getListPlayers()])
        self.axes.axis([0, self.engine.getNumEntry(),0,maxscore+10])
        self.axes.get_xaxis().set_major_locator(matplotlib.ticker.MaxNLocator(integer=True))
        for player in self.engine.getListPlayers():
            self.axes.plot(scores[player],linewidth=2.5, linestyle="-",marker='o',label=player)
        
        box = self.axes.get_position()
        if not self.axiswidth: self.axiswidth = box.width
        
        self.axes.set_position([box.x0, box.y0,  self.axiswidth * 0.9, box.height])
        legend = self.axes.legend(loc='center left', bbox_to_anchor=(1, 0.5))
        legend.legendPatch.set_facecolor('none')
#        legend.legendPatch.set_alpha(0.0)
        try: self.canvas.draw()
        except RuntimeError: pass
