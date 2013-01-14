#!/usr/bin/env python
# -*- coding: utf-8 -*-
try:
    from PySide import QtCore,QtGui
    QtGui.QFileDialog.getOpenFileNameAndFilter = QtGui.QFileDialog.getOpenFileName
except ImportError as error:
    from PyQt4 import QtCore,QtGui
    QtCore.Signal = QtCore.pyqtSignal
    QtCore.Slot = QtCore.pyqtSlot
    
import re

from controllers.phase10engine import Phase10Engine,Phase10MasterEngine
from gui.game import GameWidget
from gui.clock import GameClock

class Phase10Widget(GameWidget):

    def __init__(self, game, players, parent=None):
        super(Phase10Widget, self).__init__(game,players,parent)
        self.initUI()

    def createEngine(self):
        if self.game == 'Phase10Master':
            self.engine = Phase10MasterEngine()
        elif self.game == 'Phase10':
            self.engine = Phase10Engine()
        else:
            raise Exception("No engine for game {}".format(self.game))
            return

    def initUI(self):
        #Setup Layouts
        self.widgetLayout = QtGui.QGridLayout(self)
        self.leftLayout =  QtGui.QVBoxLayout()
        if len(self.players)>4:
            players_grid = True
            self.playerGroupsLayout =  QtGui.QGridLayout()
            
        else:
            players_grid = False
            self.playerGroupsLayout =  QtGui.QVBoxLayout()
        
        self.miscElementsLayout = QtGui.QVBoxLayout()
        self.widgetLayout.addLayout(self.miscElementsLayout,1,1)
        
        self.matchGroup = QtGui.QGroupBox(self)
        self.matchGroup.setStyleSheet("QGroupBox { font-size: 18px; font-weight: bold; }")
#        self.rightLayout.addWidget(self.matchGroup)
        self.widgetLayout.addWidget(self.matchGroup,0,1)
        
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
        
        
        self.phasesInOrderCheckBox = QtGui.QCheckBox(self.matchGroup)
        self.phasesInOrderCheckBox.setChecked(True)
        self.phasesInOrderCheckBox.setStyleSheet("QCheckBox { font-size: 14px; font-weight: bold; }")
        self.matchGroupLayout.addWidget(self.phasesInOrderCheckBox)
        
        self.extraGroup = QtGui.QGroupBox(self)
        self.extraGroup.setStyleSheet("QGroupBox { font-size: 18px; font-weight: bold; }")
        self.miscElementsLayout.addWidget(self.extraGroup)
        self.extraGroupLayout = QtGui.QVBoxLayout(self.extraGroup)
        
        self.phaseLabels = []
        for _ in range(len(self.getPhases())):
            self.extraGroupLayout.addSpacing(10)
            label = QtGui.QLabel(self)
            label.setStyleSheet("QLabel {font-size: 16px; font-weight: bold; }")
            self.phaseLabels.append(label)
            self.extraGroupLayout.addWidget(label)
   
        self.roundGroup = QtGui.QGroupBox(self)
        self.roundGroup.setStyleSheet("QGroupBox { font-size: 18px; font-weight: bold; }")
        self.widgetLayout.addWidget(self.roundGroup,0,0)
        
        self.roundLayout = QtGui.QVBoxLayout(self.roundGroup)
        self.buttonGroupLayout= QtGui.QHBoxLayout()
        self.roundLayout.addLayout(self.buttonGroupLayout)
        self.roundLayout.addStretch()
        
        self.cancelMatchButton = QtGui.QPushButton(self.roundGroup)
        self.buttonGroupLayout.addWidget(self.cancelMatchButton)
        self.cancelMatchButton.clicked.connect(self.cancelMatch)
        
        self.pauseMatchButton = QtGui.QPushButton(self.roundGroup)
        self.buttonGroupLayout.addWidget(self.pauseMatchButton)
        self.pauseMatchButton.clicked.connect(self.pauseMatch)

        self.detailMatchButton = QtGui.QPushButton(self.roundGroup)
        self.detailMatchButton.setDisabled(True)
        self.buttonGroupLayout.addWidget(self.detailMatchButton)
        self.detailMatchButton.clicked.connect(self.showDetails)

        self.commitRoundButton = QtGui.QPushButton(self.roundGroup)
        self.buttonGroupLayout.addWidget(self.commitRoundButton)
        self.commitRoundButton.clicked.connect(self.commitRound)
        
        self.gameStatusLabel = QtGui.QLabel(self.roundGroup)
        self.gameStatusLabel.setAlignment(QtCore.Qt.AlignCenter)
        self.roundLayout.addWidget(self.gameStatusLabel)
        self.roundLayout.addStretch()

        self.widgetLayout.addLayout(self.playerGroupsLayout,1,0)
        
        #Init variables
        self.playerGroupBox=dict()
        self.playerNewRoundLayout=dict()
        self.roundWinnerRadioButton=dict()
        self.roundScore=dict()
        self.roundPhaseCleared=dict()
        self.phaseCompletedLabels=dict()
        self.winnerButtonGroup=QtGui.QButtonGroup()
        self.nobodyWinnerRadioButton = QtGui.QRadioButton(self)
        self.nobodyWinnerRadioButton.hide()
        self.nobodyWinnerRadioButton.setChecked(True)
        self.winnerButtonGroup.addButton(self.nobodyWinnerRadioButton)
        
        
        if not players_grid: self.playerGroupsLayout.addStretch()
        np = 0
        for player in self.players:
            self.playerGroupBox[player] = Phase10PlayerWidget(player,self.winnerButtonGroup,self)
            self.phasesInOrderCheckBox.stateChanged.connect(self.playerGroupBox[player].switchPhasesInOrder)
            if players_grid: 
                self.playerGroupsLayout.addWidget(self.playerGroupBox[player],np/2,np%2)
            else: self.playerGroupsLayout.addWidget(self.playerGroupBox[player])    
            np += 1
            
        if not players_grid: self.playerGroupsLayout.addStretch()
        
        self.playerGroupBox[self.engine.getDealer()].setDealer()
        self.retranslateUI()
        
    def retranslateUI(self):
        self.matchGroup.setTitle(QtGui.QApplication.translate("Phase10Widget","Match"))
        self.dealerPolicyCheckBox.setText(QtGui.QApplication.translate("Phase10Widget","Winner deals"))
        self.phasesInOrderCheckBox.setText(QtGui.QApplication.translate("Phase10Widget","Phases in order"))
        self.pauseMatchButton.setText(QtGui.QApplication.translate("Phase10Widget","&Pause/Play"))
        self.extraGroup.setTitle(QtGui.QApplication.translate("Phase10Widget","Phases"))
        self.roundGroup.setTitle("{} {}".format(QtGui.QApplication.translate("Phase10Widget","Round"),str(self.engine.getNumRound())))
        self.cancelMatchButton.setText(QtGui.QApplication.translate("Phase10Widget","&Cancel Match"))
        self.detailMatchButton.setText(QtGui.QApplication.translate("Phase10Widget","&Details..."))
        self.commitRoundButton.setText(QtGui.QApplication.translate("Phase10Widget","Commit &Round"))
        self.updateGameStatusLabel()
        
        for player in self.players:
            self.playerGroupBox[player].retranslateUI()
        
        phaseword = unicode(QtGui.QApplication.translate("Phase10Widget","Phase"))
        for number,(phase,label) in enumerate(zip(self.getPhases(),self.phaseLabels),start=1):
            label.setText(unicode(u"{0} {1:02}: {2}".format(phaseword,number,phase)))
            
    def updateGameStatusLabel(self):
        self.gameStatusLabel.setStyleSheet("QLabel { font-size: 16px; font-weight:bold; color: red;}")    
        winner = self.engine.getWinner()
        if winner:
            self.gameStatusLabel.setText(unicode(QtGui.QApplication.translate("Phase10Widget","{} won this match!")).format(winner))
        elif self.engine.isPaused():
            self.gameStatusLabel.setText(QtGui.QApplication.translate("Phase10Widget","Game is paused"))
        else:
            self.gameStatusLabel.setText(QtGui.QApplication.translate("Phase10Widget",""))        
            
    def pauseMatch(self):
        if self.engine.isPaused():
            self.engine.unpause()
            self.clock.unpauseTimer()
            self.commitRoundButton.setEnabled(True)
            for player in self.players:
                self.playerGroupBox[player].setEnabled(True)
        else:
            self.engine.pause()
            self.clock.pauseTimer()
            self.commitRoundButton.setDisabled(True)
            for player in self.players:
                self.playerGroupBox[player].setDisabled(True)
                
        self.updateGameStatusLabel()
                
    def commitRound(self):
        self.engine.openRound()
        winner=None
        for player in self.players:
            pw = self.playerGroupBox[player]
            a_phase = pw.getRoundPhase()
            cleared =  pw.isRoundCleared()
            if pw.isWinner():
                winner = player
                self.engine.setRoundWinner(winner)
                score = 0
                if not cleared:
                    QtGui.QMessageBox.warning(self,self.game,unicode("{} ({})".format(QtGui.QApplication.translate("Phase10Widget","No phase selected for the winner"),player)))
                    return

            else:
                try:
                    score = int(pw.getRoundScore())
                except ValueError:
                    QtGui.QMessageBox.warning(self,self.game,unicode(QtGui.QApplication.translate("Phase10Widget","{0} score is not valid").format(player)))
                    return
                if score%5!=0 or (score<50 and not cleared):
                    QtGui.QMessageBox.warning(self,self.game,unicode(QtGui.QApplication.translate("Phase10Widget","{0} score is not valid").format(player)))
                    return
            self.engine.addRoundInfo(player,score, {'aimedPhase':a_phase, 'isCompleted':cleared})
        if not winner:
            QtGui.QMessageBox.warning(self,self.game,unicode(QtGui.QApplication.translate("Phase10Widget","No winner selected")))
            return

        #Everything ok so far, let's confirm
        ret = QtGui.QMessageBox.question(self, QtGui.QApplication.translate("Phase10Widget",'Commit Round'),
        QtGui.QApplication.translate("Phase10Widget","Are you sure you want to commit the current round?"), QtGui.QMessageBox.Yes | 
        QtGui.QMessageBox.No, QtGui.QMessageBox.Yes)
        
        if ret == QtGui.QMessageBox.No: return

        # Once here, we can commit round...
        self.playerGroupBox[self.engine.getDealer()].unsetDealer() 
        self.engine.commitRound()
        self.engine.printStats()
        
        self.updatePanel()
        winner = self.engine.getWinner()
        if winner:
            self.updateGameStatusLabel()
            for player in self.players:
                self.playerGroupBox[player].setDisabled(True)
                self.clock.stopTimer()
                self.commitRoundButton.setDisabled(True)
                self.phasesInOrderCheckBox.setDisabled(True)  
        else:   
            self.playerGroupBox[self.engine.getDealer()].setDealer() 

    def changeDealingPolicy(self, *args, **kwargs):
        if self.dealerPolicyCheckBox.isChecked():
            self.engine.setDealingPolicy(self.engine.WinnerDealer)
        else:
            self.engine.setDealingPolicy(self.engine.RRDealer)


    def updatePanel(self):        
        self.detailMatchButton.setEnabled(True)
        self.phasesInOrderCheckBox.setEnabled(False)
        self.dealerPolicyCheckBox.setEnabled(False)
        if not self.engine.getWinner():
            self.roundGroup.setTitle(unicode(QtGui.QApplication.translate("Phase10Widget","Round {0}")).format(str(self.engine.getNumRound())))
            
        self.nobodyWinnerRadioButton.setChecked(True)
        for player in self.players:
            score = self.engine.getScoreFromPlayer(player)
            completed = self.engine.getCompletedPhasesFromPlayer(player)
            remaining = self.engine.getRemainingPhasesFromPlayer(player)
            self.playerGroupBox[player].updateDisplay(score,completed,remaining)

    def showDetails(self):
        Phase10RoundsDetail(self.engine).exec_()
        
    def getPhases(self):
        types = {'s': {
                       '2':[
                            unicode(QtGui.QApplication.translate("Phase10Widget",'pair')),
                            unicode(QtGui.QApplication.translate("Phase10Widget",'pairs'))
                            ], 
                       '3':[
                            unicode(QtGui.QApplication.translate("Phase10Widget",'three of a kind','singular')),
                            unicode(QtGui.QApplication.translate("Phase10Widget",'three of a kind','plural'))
                            ], 
                       '4':[
                            unicode(QtGui.QApplication.translate("Phase10Widget",'four of a kind','singular')),
                            unicode(QtGui.QApplication.translate("Phase10Widget",'four of a kind','plural'))
                            ],
                       '5':[
                            unicode(QtGui.QApplication.translate("Phase10Widget",'five of a kind','singular')),
                            unicode(QtGui.QApplication.translate("Phase10Widget",'five of a kind','plural'))
                            ]
                        },
                 'c': unicode(QtGui.QApplication.translate("Phase10Widget","cards of the same colour")), 
                 'r': [
                       unicode(QtGui.QApplication.translate("Phase10Widget",'run of')),
                       unicode(QtGui.QApplication.translate("Phase10Widget", 'runs of'))
                       ], 
                 'cr': [
                        unicode(QtGui.QApplication.translate("Phase10Widget",'colour run of')),
                        unicode(QtGui.QApplication.translate("Phase10Widget",'colour runs of'))
                        ]
                 }
        phases = []
        for code in self.engine.getPhases():
            first = True
            phase = u""
            for part in code.split():
                m = re.match(r'(\d)([src]|cr)(\d)',part)
                if m:
                    n, tcode, cards = m.groups()
                    if int(n)>1: plural = 1
                    else: plural = 0
                    if not first: phase += " + "
                    first = False
                    if tcode == 's':
                        phase += u"{} {}".format(n,types[tcode][cards][plural])
                    elif tcode == 'c':
                        phase += u"{} {}".format(cards,types[tcode])
                    elif tcode in ['r', 'cr']:
                        phase += u"{} {} {}".format(n,types[tcode][plural],cards)
            phases.append(phase)
        return phases


class Phase10PlayerWidget(QtGui.QGroupBox):
    def __init__(self, nick, bgroup = None, parent=None):
        super(Phase10PlayerWidget,self).__init__(parent)
        self.setStyleSheet("QGroupBox { font-size: 18px; font-weight: bold; }")
        self.setTitle(nick)
        self.nick = nick
        self.bgroup = bgroup
        self.phases_in_order = True
        self.current_phase = 1
        self.initUI()

    def initUI(self):
        self.widgetLayout = QtGui.QHBoxLayout(self)
        self.leftLayout = QtGui.QHBoxLayout()
        self.middleLayout = QtGui.QGridLayout()
#        self.middleLayout.setMargin(5)
        self.middleLayout.setSpacing(5)
#        self.rightLayout = QtGui.QVBoxLayout()
        self.rightLayout = QtGui.QGridLayout()
        self.widgetLayout.addStretch()
        self.widgetLayout.addLayout(self.leftLayout)
        self.widgetLayout.addLayout(self.middleLayout)
        self.widgetLayout.addLayout(self.rightLayout)
        self.widgetLayout.addStretch()      
        
        #Left part - score
        self.scoreLCD = QtGui.QLCDNumber(self)
        self.scoreLCD.setSegmentStyle(QtGui.QLCDNumber.Flat)
        self.leftLayout.addWidget(self.scoreLCD)
        self.scoreLCD.setNumDigits(3)
        self.scoreLCD.setMinimumWidth(100)
        self.scoreLCD.setMaximumHeight(125)
        
        #Middle part - Phase list
        self.phaseLabels=list()
        for phase in range(1,11):
            label = Phase10Label(phase,self)
            if phase == self.current_phase:
                label.setCurrent()
            self.phaseLabels.append(label)
            self.middleLayout.addWidget(label,(phase-1)/5,(phase-1)%5,1,1)
        
        #Right Part - New round form
#        self.rightLayout.addSpacing(20)
#        layout = QtGui.QHBoxLayout()
#        self.rightLayout.addLayout(layout)
        self.roundWinnerRadioButton = QtGui.QRadioButton()

        self.bgroup.addButton(self.roundWinnerRadioButton)
#        layout.addWidget(self.roundWinnerRadioButton)
        self.rightLayout.addWidget(self.roundWinnerRadioButton,0,0)
        
        
        self.roundScore=QtGui.QLineEdit(self)
        self.roundScore.setFixedWidth(30)
        self.roundScore.setValidator(QtGui.QIntValidator(5,200,None))
        self.rightLayout.addWidget(self.roundScore,0,1)

        self.roundPhaseClearedCheckbox = QtGui.QCheckBox(self)
        self.rightLayout.addWidget(self.roundPhaseClearedCheckbox,1,0)
        
        self.roundWinnerRadioButton.toggled.connect(self.roundScore.setDisabled)
        self.roundWinnerRadioButton.toggled.connect(self.roundPhaseClearedCheckbox.setDisabled)
        self.roundWinnerRadioButton.toggled.connect(self.roundPhaseClearedCheckbox.setChecked)
        self.roundScore.textChanged.connect(self.updateRoundPhaseCleared)
        self.retranslateUI()
        
    def retranslateUI(self):
        self.roundWinnerRadioButton.setText(QtGui.QApplication.translate("Phase10PlayerWidget","Winner"))
        self.roundPhaseClearedCheckbox.setText(QtGui.QApplication.translate("Phase10PlayerWidget","Completed"))
            
    def updateDisplay(self,points,completed_phases,remaining_phases):
        
        if len(remaining_phases)==0:
            self.current_phase=0
        else: self.current_phase = min(remaining_phases)
        
        self.roundWinnerRadioButton.setDown(True)
        if points >= 1000: self.scoreLCD.setNumDigits(4)
        self.scoreLCD.display(points)
        self.roundScore.clear()
        self.roundPhaseClearedCheckbox.setChecked(False)
        
        phase = 1
        for label in self.phaseLabels:
            if phase == self.current_phase:
                if not label.isCurrent():label.setCurrent()
            elif phase in completed_phases:
                if not label.isPassed(): label.setPassed()
            else:
                if not label.isRemaining(): label.setRemaining()
            phase += 1
            
    def isWinner(self):
        return self.roundWinnerRadioButton.isChecked()
 
    def getRoundPhase(self):
        return self.current_phase
    
    def isRoundCleared(self):
        return self.roundPhaseClearedCheckbox.isChecked()
            
        
    def getRoundScore(self):
        return self.roundScore.text()
    
    def switchPhasesInOrder(self,in_order):
        self.phases_in_order = (in_order==QtCore.Qt.Checked)
        if not self.phases_in_order: return
        self.phaseLabels[self.current_phase-1].setRemaining()
        for label in self.phaseLabels:
            if label.isRemaining():
                label.setCurrent()
                self.current_phase = label.getNumber()
                break
        
    def updatePhaseSelected(self,phaselabel):
        if phaselabel.isRemaining():
            self.current_phase = phaselabel.getNumber()
            for label in self.phaseLabels:
                if label.isCurrent(): label.setRemaining()
            phaselabel.setCurrent()
                              
    def updateRoundPhaseCleared(self,value):
        try:
            score = int(value)
        except:
            if not self.roundWinnerRadioButton.isChecked():
                self.roundPhaseClearedCheckbox.setChecked(False)
            return
        
        if (score %5 != 0 ): return
        
        if (score>=50): 
            self.roundWinnerRadioButton.setChecked(False)
            self.roundPhaseClearedCheckbox.setChecked(False)
        elif (score==0): 
            self.roundWinnerRadioButton.setChecked(True)
            self.roundPhaseClearedCheckbox.setChecked(True)
        else:
            self.roundWinnerRadioButton.setChecked(False) 
            self.roundPhaseClearedCheckbox.setChecked(True)
            
    def setDealer(self):
        self.setStyleSheet("QGroupBox { font-size: 18px; font-weight: bold; color: red }")
        
    def unsetDealer(self):
        self.setStyleSheet("QGroupBox { font-size: 18px; font-weight: bold; color: black }")
        
    def mousePressEvent(self, event):
        child = self.childAt(event.pos())
        if child is None: self.roundScore.setFocus()
        elif type(child) == Phase10Label and not self.phases_in_order:
            self.updatePhaseSelected(child)
        return QtGui.QGroupBox.mousePressEvent(self, event)
        
        

class Phase10Label(QtGui.QLabel):
    
    def __init__(self,number,parent=None):
        super(Phase10Label, self).__init__(parent)
        self.setText(str(number).zfill(2))
        self.setAutoFillBackground(False)
        self.setRemaining()
        self.setFrameShape(QtGui.QFrame.Box)
        self.setFrameShadow(QtGui.QFrame.Raised)
        self.setScaledContents(True)
        self.setAlignment(QtCore.Qt.AlignCenter)
        self.setWordWrap(False)
        self.setFixedSize(QtCore.QSize(25,25))
        self.number = number

    def isPassed(self):
        return self.state==1
    def isCurrent(self):
        return self.state==2
    def isRemaining(self):
        return self.state==0
    def setPassed(self):
        self.state = 1
        self.setStyleSheet("QLabel { background-color: green; font-weight: bold; color:white }")
    def setCurrent(self):
        self.state = 2
        self.setStyleSheet("QLabel { background-color: orange; font-weight: bold; color:white }")
    def setRemaining(self):
        self.state = 0
        self.setStyleSheet("QLabel { background-color: red; font-weight: bold; color:white }")          
    def getNumber(self):
        return self.number
    
class Phase10RoundsDetail(QtGui.QDialog):
    def __init__(self, engine, parent=None):
        super(Phase10RoundsDetail, self).__init__(parent)
        self.engine = engine
        self.initUI()

    def initUI(self):
        self.setWindowTitle(QtGui.QApplication.translate("Phase10RoundsDetail",'Details'))
        self.widgetLayout = QtGui.QVBoxLayout(self)
        self.table = QtGui.QTableWidget(self.engine.getNumRound()-1,len(self.engine.getPlayers()))
        self.widgetLayout.addWidget(self.table)
        roundlist = list()
        rounds = self.engine.getRounds()
        players = self.engine.getListPlayers()
        for i in range(1, len(rounds)+1):
            roundlist.append(unicode(QtGui.QApplication.translate("Phase10RoundsDetail","Round {}")).format(i))
        self.table.setVerticalHeaderLabels(roundlist)
        self.table.setHorizontalHeaderLabels(players)
        i = 0
        j = 0
        for r in rounds:
            j=0
            for player in players:
                item = QtGui.QTableWidgetItem(str(r.getPlayerScore(player)))
                item.setFlags(item.flags()^QtCore.Qt.ItemIsEditable)
                item.setTextAlignment(QtCore.Qt.AlignVCenter|QtCore.Qt.AlignRight)
                self.table.setItem(i,j,item)
                j+=1
            i+=1
        self.table.horizontalHeader().setResizeMode(QtGui.QHeaderView.Stretch)
#        self.table.resizeColumnsToContents()
        self.table.resizeRowsToContents()
        self.table.verticalHeader().setResizeMode(QtGui.QHeaderView.ResizeToContents)
        size = self.table.rowHeight(0)*(len(roundlist)+1)+len(roundlist)
        self.table.setFixedHeight(size)

