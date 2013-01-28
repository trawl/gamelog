#!/usr/bin/env python
# -*- coding: utf-8 -*-

import re

try:
    from PySide import QtCore,QtGui
    QtGui.QFileDialog.getOpenFileNameAndFilter = QtGui.QFileDialog.getOpenFileName
except ImportError as error:
    from PyQt4 import QtCore,QtGui
    QtCore.Signal = QtCore.pyqtSignal
    QtCore.Slot = QtCore.pyqtSlot

from controllers.phase10engine import Phase10Engine,Phase10MasterEngine
from gui.game import GameWidget,GameInputWidget, ScoreSpinBox

class Phase10Widget(GameWidget):

    def createEngine(self):
        if self.game == 'Phase10Master':
            self.engine = Phase10MasterEngine()
        elif self.game == 'Phase10':
            self.engine = Phase10Engine()
        else:
            raise Exception("No engine for game {}".format(self.game))
            return

    def initUI(self):
        super(Phase10Widget,self).initUI()
         
        self.detailMatchButton = QtGui.QPushButton(self.roundGroup)
        self.detailMatchButton.setEnabled(self.engine.getNumRound()>1)
        self.buttonGroupLayout.insertWidget(2,self.detailMatchButton)
        self.detailMatchButton.clicked.connect(self.showDetails)
               
        self.phasesInOrderCheckBox = QtGui.QCheckBox(self.matchGroup)
        self.phasesInOrderCheckBox.setChecked(self.engine.getPhasesInOrderFlag())
        self.phasesInOrderCheckBox.setStyleSheet("QCheckBox { font-size: 14px; font-weight: bold; }")
        self.phasesInOrderCheckBox.setDisabled(self.engine.getNumRound()>1)
        self.phasesInOrderCheckBox.stateChanged.connect(self.phasesInOrderChanged)
        self.matchGroupLayout.addWidget(self.phasesInOrderCheckBox)

        self.gameInput = Phase10InputWidget(self.engine,self.matchGroup)
        self.phasesInOrderCheckBox.toggled.connect(self.gameInput.switchPhasesInOrder)
        self.widgetLayout.addWidget(self.gameInput,1,0)
    
        self.extraGroup = QtGui.QGroupBox(self)
        self.extraGroup.setStyleSheet("QGroupBox { font-size: 18px; font-weight: bold; }")
        self.widgetLayout.addWidget(self.extraGroup,1,1)
        self.extraGroupLayout = QtGui.QVBoxLayout(self.extraGroup)
        
        self.phaseLabels = []
        for _ in range(len(self.getPhases())):
            self.extraGroupLayout.addSpacing(10)
            label = QtGui.QLabel(self)
            label.setStyleSheet("QLabel {font-size: 16px; font-weight: bold; }")
            self.phaseLabels.append(label)
            self.extraGroupLayout.addWidget(label)
        
        self.setDealer()
        self.retranslateUI()
        
    def retranslateUI(self):
        super(Phase10Widget,self).retranslateUI()
        self.phasesInOrderCheckBox.setText(QtGui.QApplication.translate("Phase10Widget","Phases in order"))
        self.extraGroup.setTitle(QtGui.QApplication.translate("Phase10Widget","Phases"))
        self.detailMatchButton.setText(QtGui.QApplication.translate("Phase10Widget","&Details..."))
        self.gameInput.retranslateUI()        
        phaseword = unicode(QtGui.QApplication.translate("Phase10Widget","Phase"))
        for number,(phase,label) in enumerate(zip(self.getPhases(),self.phaseLabels),start=1):
            label.setText(unicode(u"{0} {1:02}: {2}".format(phaseword,number,phase)))
    
    def checkPlayerScore(self,player,score): 
        return super(Phase10Widget,self).checkPlayerScore(self,score) \
            and not (score%5!=0 or (score<50 and not self.gameInput.hasPlayerCleared(player)))
            
    def getPlayerExtraInfo(self,player):  
        cleared = self.gameInput.hasPlayerCleared(player)
        a_phase = self.gameInput.getPlayerAimedPhase(player)
        if a_phase: return {'aimedPhase':a_phase, 'isCompleted':cleared}
        else: return {}

    def changeDealingPolicy(self, *args, **kwargs):
        if self.dealerPolicyCheckBox.isChecked():
            self.engine.setDealingPolicy(self.engine.WinnerDealer)
        else:
            self.engine.setDealingPolicy(self.engine.RRDealer)

    def updatePanel(self):        
        self.detailMatchButton.setEnabled(True)
        self.phasesInOrderCheckBox.setEnabled(False)
        self.dealerPolicyCheckBox.setEnabled(False)
        self.gameInput.updatePanel()
        super(Phase10Widget,self).updatePanel()
        
    def unsetDealer(self): self.gameInput.unsetDealer()
    
    def setDealer(self): self.gameInput.setDealer() 
    
    def showDetails(self): Phase10RoundsDetail(self.engine).exec_()
        
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

    def phasesInOrderChanged(self,state):
        if state == QtCore.Qt.Unchecked:
            self.engine.setPhasesInOrderFlag(False)
        elif state == QtCore.Qt.Checked:
            self.engine.setPhasesInOrderFlag(True)

class Phase10InputWidget(GameInputWidget):
    
    def __init__(self,engine,parent=None):
        super(Phase10InputWidget,self).__init__(engine,parent)
        self.initUI()
    
    def initUI(self):
        self.winnerButtonGroup=QtGui.QButtonGroup()
        self.nobodyWinnerRadioButton = QtGui.QRadioButton(self)
        self.nobodyWinnerRadioButton.hide()
        self.nobodyWinnerRadioButton.setChecked(True)
        self.winnerButtonGroup.addButton(self.nobodyWinnerRadioButton)
        
        players = self.engine.getListPlayers()
        if len(players)>4:
            players_grid = True
            self.widgetLayout =  QtGui.QGridLayout(self)
        else:
            players_grid = False
            self.widgetLayout =  QtGui.QVBoxLayout(self)
            self.widgetLayout.addStretch()

        for np, player in enumerate(players):
            self.playerInputList[player] = Phase10PlayerWidget(player,self.engine,self.winnerButtonGroup,self)
            self.playerInputList[player].winnerSet.connect(self.changedWinner)
            if players_grid: 
                self.widgetLayout.addWidget(self.playerInputList[player],np/2,np%2)
            else: 
                self.widgetLayout.addWidget(self.playerInputList[player])
            
        if not players_grid: self.widgetLayout.addStretch()
        
    def retranslateUI(self):
        for piw in self.playerInputList.values():
            piw.retranslateUI()
        
    def switchPhasesInOrder(self, in_order):
        for player in self.engine.getListPlayers():
            self.playerInputList[player].switchPhasesInOrder(in_order)
            
    def hasPlayerCleared(self,player):
        return self.playerInputList[player].isRoundCleared()
    
    def getPlayerAimedPhase(self,player):
        return self.playerInputList[player].getRoundPhase()
    
    def updatePanel(self):
        self.nobodyWinnerRadioButton.setChecked(True)
        for player in self.engine.getListPlayers():
            score = self.engine.getScoreFromPlayer(player)
            completed = self.engine.getCompletedPhasesFromPlayer(player)
            remaining = self.engine.getRemainingPhasesFromPlayer(player)
            self.playerInputList[player].updateDisplay(score,completed,remaining)
            
    def unsetDealer(self): self.playerInputList[self.engine.getDealer()].unsetDealer()
    
    def setDealer(self): self.playerInputList[self.engine.getDealer()].setDealer() 
    
class Phase10ScoreSpinBox(ScoreSpinBox):
    
    def __init__(self,parent=None):
        super(Phase10ScoreSpinBox,self).__init__(parent)
        self.setSingleStep(5)
        self.setRange(-5,200)
        self.setValue(0)
        self.clear()

    def validate(self,text,pos):
        try: score = int(text)
        except ValueError: return (QtGui.QValidator.Invalid,text)
        if score%5 != 0: return (QtGui.QValidator.Intermediate,text)
        else: return (QtGui.QValidator.Acceptable,text)


class Phase10PlayerWidget(QtGui.QGroupBox):
    
    winnerSet = QtCore.Signal(str)
    
    def __init__(self, nick, engine, bgroup = None, parent=None):
        super(Phase10PlayerWidget,self).__init__(parent)
        self.setStyleSheet("QGroupBox { font-size: 18px; font-weight: bold; }")
        self.setTitle(nick)
        self.nick = nick
        self.bgroup = bgroup
        self.engine = engine
        self.current_phase = min(self.engine.getRemainingPhasesFromPlayer(self.nick))
        self.phases_in_order = self.engine.getPhasesInOrderFlag()
        self.initUI()

    def initUI(self):
        self.widgetLayout = QtGui.QHBoxLayout(self)
        self.leftLayout = QtGui.QHBoxLayout()
        self.middleLayout = QtGui.QGridLayout()
        self.middleLayout.setSpacing(5)
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
        self.scoreLCD.display(self.engine.getScoreFromPlayer(self.nick))
        
        #Middle part - Phase list
        self.phaseLabels=list()
        for phase in range(1,11):
            label = Phase10Label(phase,self)
            if phase == self.current_phase:
                label.setCurrent()
            elif self.engine.hasPhaseCompleted(self.nick, phase):
                label.setPassed()
            self.phaseLabels.append(label)
            self.middleLayout.addWidget(label,(phase-1)/5,(phase-1)%5,1,1)
            
        #Middle part - Inputs
        self.roundWinnerRadioButton = QtGui.QRadioButton()
        self.bgroup.addButton(self.roundWinnerRadioButton)
        self.rightLayout.addWidget(self.roundWinnerRadioButton,0,0)
        
        self.roundScore=Phase10ScoreSpinBox(self)
        self.roundScore.setFixedWidth(60)
        self.roundScore.valueChanged.connect(self.updateRoundPhaseCleared)
        self.rightLayout.addWidget(self.roundScore,0,1)

        self.roundPhaseClearedCheckbox = QtGui.QCheckBox(self)
        self.rightLayout.addWidget(self.roundPhaseClearedCheckbox,1,0)
        
        self.roundWinnerRadioButton.toggled.connect(self.roundScore.setDisabled)
        self.roundWinnerRadioButton.toggled.connect(self.roundPhaseClearedCheckbox.setDisabled)
        self.roundWinnerRadioButton.toggled.connect(self.roundPhaseClearedCheckbox.setChecked)
        self.roundWinnerRadioButton.toggled.connect(self.winnerSetAction)
        
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
        self.roundScore.setValue(5)
        self.roundScore.clear()
        self.roundPhaseClearedCheckbox.setChecked(False)
        
        for phase, label in enumerate(self.phaseLabels,start=1):
            if phase == self.current_phase:
                if not label.isCurrent():label.setCurrent()
            elif phase in completed_phases:
                if not label.isPassed(): label.setPassed()
            else:
                if not label.isRemaining(): label.setRemaining()
            
    def getScore(self):
        if self.isWinner(): return 0
        else: return self.roundScore.value()
    
    def switchPhasesInOrder(self,in_order):
        self.phases_in_order = in_order
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
        score = value
        if score < 0:
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
            
    def mousePressEvent(self, event):
        child = self.childAt(event.pos())
        if child is None: self.roundScore.setFocus()
        elif type(child) == Phase10Label and not self.phases_in_order:
            self.updatePhaseSelected(child)
        return QtGui.QGroupBox.mousePressEvent(self, event)
            
    def setDealer(self):
        self.setStyleSheet("QGroupBox { font-size: 18px; font-weight: bold; color: red }")
        
    def unsetDealer(self):
        self.setStyleSheet("QGroupBox { font-size: 18px; font-weight: bold; color: black }")
        
    def isWinner(self):
        return self.roundWinnerRadioButton.isChecked()
 
    def getRoundPhase(self):
        return self.current_phase
    
    def isRoundCleared(self):
        return self.roundPhaseClearedCheckbox.isChecked()
    
    def winnerSetAction(self,isset):
        if isset: self.winnerSet.emit(self.nick)
        
    def reset(self): pass
        

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

