#!/usr/bin/env python
# -*- coding: utf-8 -*-

import re
import sys

try:
    from PyQt4 import QtCore,QtGui
    QtCore.Signal = QtCore.pyqtSignal
    QtCore.Slot = QtCore.pyqtSlot
except ImportError as error:
    from PySide import QtCore,QtGui
    QtGui.QFileDialog.getOpenFileNameAndFilter = QtGui.QFileDialog.getOpenFileName

from controllers.phase10engine import Phase10Engine, Phase10MasterEngine
from gui.game import GameWidget, GameInputWidget, GamePlayerWidget, ScoreSpinBox, GameRoundsDetail, GameRoundTable, GameRoundPlot, PlayerColours
from gui.plots import PlotView

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
               
        self.phasesInOrderCheckBox = QtGui.QCheckBox(self.matchGroup)
        self.phasesInOrderCheckBox.setChecked(self.engine.getPhasesInOrderFlag())
        self.phasesInOrderCheckBox.setStyleSheet("QCheckBox { font-size: 14px; font-weight: bold; }")
        self.phasesInOrderCheckBox.setDisabled(self.engine.getNumRound()>1)
        self.phasesInOrderCheckBox.stateChanged.connect(self.phasesInOrderChanged)
        self.matchGroupLayout.addWidget(self.phasesInOrderCheckBox)

        self.gameInput = Phase10InputWidget(self.engine,self)
        self.gameInput.setAutoFillBackground(True)
        self.phasesInOrderCheckBox.toggled.connect(self.gameInput.switchPhasesInOrder)
        self.gameInput.enterPressed.connect(self.commitRound)
        
        self.details = Phase10RoundsDetail(self.engine, self.gameInput, self)
        self.details.edited.connect(self.updatePanel)
        self.widgetLayout.addWidget(self.details,1,0)   

        self.extraGroup = QtGui.QGroupBox(self)
        self.extraGroup.setStyleSheet("QGroupBox { font-size: 18px; font-weight: bold; }")
        self.widgetLayout.addWidget(self.extraGroup,1,1)
        self.extraGroupLayout = QtGui.QVBoxLayout(self.extraGroup)
        
        self.phaseLabels = []
        for _ in range(len(self.getPhases())):
            self.extraGroupLayout.addSpacing(10)
            label = QtGui.QLabel(self)
            label.setStyleSheet("QLabel {font-size: 18px; font-weight: bold; }")
#             label.setScaledContents(True)
            self.phaseLabels.append(label)
            self.extraGroupLayout.addWidget(label)
        
        self.setDealer()
        self.retranslateUI()
        
    def retranslateUI(self):
        super(Phase10Widget,self).retranslateUI()
        self.phasesInOrderCheckBox.setText(QtGui.QApplication.translate("Phase10Widget","Phases in order"))
        self.gameInput.retranslateUI()
        self.details.retranslateUI()
        phaseword = QtGui.QApplication.translate("Phase10Widget","Phase")
        for number,(phase,label) in enumerate(zip(self.getPhases(),self.phaseLabels),start=1):
            label.setText("{0} {1:02}: {2}".format(phaseword,number,phase))
    
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
        super(Phase10Widget,self).updatePanel()
        self.phasesInOrderCheckBox.setEnabled(False)
        self.dealerPolicyCheckBox.setEnabled(False)
        self.gameInput.updatePanel()
        self.details.updateRound()
        if self.engine.getWinner(): self.details.updateStats()
#         self.plot.updatePlot()
        
    def unsetDealer(self): self.gameInput.unsetDealer()
    
    def setDealer(self): self.gameInput.setDealer() 
    
    def setWinner(self):
        super(Phase10Widget,self).setWinner()
        self.gameInput.setEnabled(True)
        self.gameInput.setWinner() 
        
    def getPhases(self):
        types = {'s': {
                       '2':[
                            QtGui.QApplication.translate("Phase10Widget",'pair'),
                            QtGui.QApplication.translate("Phase10Widget",'pairs')
                            ], 
                       '3':[
                            QtGui.QApplication.translate("Phase10Widget",'three of a kind','singular'),
                            QtGui.QApplication.translate("Phase10Widget",'three of a kind','plural')
                            ], 
                       '4':[
                            QtGui.QApplication.translate("Phase10Widget",'four of a kind','singular'),
                            QtGui.QApplication.translate("Phase10Widget",'four of a kind','plural')
                            ],
                       '5':[
                            QtGui.QApplication.translate("Phase10Widget",'five of a kind','singular'),
                            QtGui.QApplication.translate("Phase10Widget",'five of a kind','plural')
                            ]
                        },
                 'c': QtGui.QApplication.translate("Phase10Widget","cards of the same colour"), 
                 'r': [
                       QtGui.QApplication.translate("Phase10Widget",'run of'),
                       QtGui.QApplication.translate("Phase10Widget", 'runs of')
                       ], 
                 'cr': [
                        QtGui.QApplication.translate("Phase10Widget",'colour run of'),
                        QtGui.QApplication.translate("Phase10Widget",'colour runs of')
                        ]
                 }
        phases = []
        for code in self.engine.getPhases():
            first = True
            phase = ""
            for part in code.split():
                m = re.match(r'(\d)([src]|cr)(\d)',part)
                if m:
                    n, tcode, cards = m.groups()
                    if int(n)>1: plural = 1
                    else: plural = 0
                    if not first: phase += " + "
                    first = False
                    if tcode == 's':
                        phase += "{} {}".format(n,types[tcode][cards][plural])
                    elif tcode == 'c':
                        phase += "{} {}".format(cards,types[tcode])
                    elif tcode in ['r', 'cr']:
                        phase += "{} {} {}".format(n,types[tcode][plural],cards)
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
        if len(players)>=4:
            players_grid = True
            self.widgetLayout =  QtGui.QGridLayout(self)
        else:
            players_grid = False
            self.widgetLayout =  QtGui.QVBoxLayout(self)
#             self.widgetLayout.addStretch()

        for np, player in enumerate(players):
            self.playerInputList[player] = Phase10PlayerWidget(player,self.engine,self.winnerButtonGroup,self)
            self.playerInputList[player].roundWinnerSet.connect(self.changedWinner)
            if players_grid: 
                self.widgetLayout.addWidget(self.playerInputList[player],np/2,np%2)
            else: 
                self.widgetLayout.addWidget(self.playerInputList[player])
            
#         if not players_grid: self.widgetLayout.addStretch()
        
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
    
    def setWinner(self):
        winner = self.engine.getWinner()
        if winner in self.engine.getListPlayers():
            self.playerInputList[winner].setWinner()
            for pi in self.playerInputList.values(): pi.finish()
            
    
class Phase10ScoreSpinBox(ScoreSpinBox):
    
    def __init__(self,parent=None):
        super(Phase10ScoreSpinBox,self).__init__(parent)
        self.setSingleStep(5)
        self.setRange(-5,200)
        self.setValue(5)
        self.clear()
        self.fixed = False
        self.editingFinished.connect(self.clearFixed)

    def validate(self,text,pos):
        self.valueChanged.emit(self.value())
        res = QtGui.QValidator.Acceptable
        if text == "": 
            res = QtGui.QValidator.Intermediate
        else:
            try: 
                score = int(text)
                self.setValidDisplay()
                if score%5 != 0: res = QtGui.QValidator.Intermediate
            except ValueError: res = QtGui.QValidator.Invalid
        if 'PySide' in sys.modules: return (res,text)
        else: return (res,text,pos)
            
    def fixup(self,inp):
        if not inp: return
        if not self.hasAcceptableInput():
            self.setValue(5)
            self.fixed = True
            
    def clearFixed(self):
        self.valueChanged.emit(self.value())
        if self.fixed:
            self.setInvalidDisplay()
            self.fixed = False
            self.clear()
            
    def setDisabled(self,disable):
        if disable: self.setValue(0)
        else: self.setValue(5)
        self.setValidDisplay()
        self.clear()
        self.valueChanged.emit(self.value())
        super(Phase10ScoreSpinBox,self).setDisabled(disable)
        
    def setEnabled(self,enable):
        if enable: self.setValue(5)
        else: self.setValue(0)
        self.setValidDisplay()
        self.clear()    
        self.valueChanged.emit(self.value())
        super(Phase10ScoreSpinBox,self).setEnabled(enable)

    def setValidDisplay(self): self.setStyleSheet("QSpinBox {}")
    
    def setInvalidDisplay(self): self.setStyleSheet("QSpinBox {background-color: #FF5E5E}")


class Phase10PlayerWidget(GamePlayerWidget):
    
    roundWinnerSet = QtCore.Signal(str)
    
    def __init__(self, nick, engine, bgroup = None, parent=None):
        self.engine = engine
        self.current_phase = min(self.engine.getRemainingPhasesFromPlayer(nick))
        self.phases_in_order = self.engine.getPhasesInOrderFlag()
        self.bgroup = bgroup
        super(Phase10PlayerWidget,self).__init__(nick,PlayerColours[self.engine.getListPlayers().index(nick)],parent)
        
    def initUI(self):
        self.setStyleSheet("QGroupBox {{ font-size: 18px; font-weight: bold; color:rgb({},{},{});}}".format(self.pcolour.red(),self.pcolour.green(),self.pcolour.blue()))
        self.setTitle(self.player)
        super(Phase10PlayerWidget,self).initUI()

        trashWidget = QtGui.QWidget()
        trashWidget.setLayout(self.mainLayout)
        
        self.mainLayout = QtGui.QHBoxLayout(self)
        self.leftLayout = QtGui.QHBoxLayout()
        self.supermiddleLayout = QtGui.QVBoxLayout()
        self.supermiddleLayout.addStretch()
        self.middleLayout = QtGui.QGridLayout()
        self.middleLayout.setSpacing(5)
        self.supermiddleLayout.addLayout(self.middleLayout)
        self.supermiddleLayout.addStretch()
        self.superrightLayout = QtGui.QVBoxLayout()
        self.superrightLayout.addStretch()
        self.rightLayout = QtGui.QGridLayout()
        self.superrightLayout.addLayout(self.rightLayout)
        self.superrightLayout.addStretch()
#         self.mainLayout.addStretch()
        self.mainLayout.addLayout(self.leftLayout)
        self.mainLayout.addLayout(self.supermiddleLayout)
        self.mainLayout.addLayout(self.superrightLayout)
#         self.mainLayout.addStretch()      
        
        #Left part - score
        self.leftLayout.addWidget(self.iconlabel)
        self.leftLayout.addWidget(self.scoreLCD)
        
        self.iconlabel.setFixedSize(60,60)

        self.scoreLCD.setMinimumWidth(100)
        self.scoreLCD.setMaximumWidth(200)
        self.scoreLCD.setMinimumHeight(30)
        self.scoreLCD.setMaximumHeight(80)
        self.scoreLCD.display(self.engine.getScoreFromPlayer(self.player))   
        
        #Middle part - Phase list
        self.phaseLabels=list()
        for phase in range(1,11):
            label = Phase10Label(phase,self)
            if phase == self.current_phase:
                label.setCurrent()
            elif self.engine.hasPhaseCompleted(self.player, phase):
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
        self.roundWinnerRadioButton.toggled.connect(self.roundWinnerSetAction)
        
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
        if self.isRoundWinner(): return 0
        try: return int(self.roundScore.value())
        except: return -1
    
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
        try: score = int(self.roundScore.text())
        except: 
            self.roundPhaseClearedCheckbox.setChecked(False)
            return
        
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
#        
    def isRoundWinner(self): return self.roundWinnerRadioButton.isChecked()
 
    def getRoundPhase(self): return self.current_phase
    
    def isRoundCleared(self): return self.roundPhaseClearedCheckbox.isChecked()
    
    def roundWinnerSetAction(self,isset):
        if isset: self.roundWinnerSet.emit(self.player)
        
    def reset(self): pass
    
    def finish(self):
        self.roundWinnerRadioButton.toggled.disconnect(self.roundScore.setDisabled)
        self.roundWinnerRadioButton.toggled.disconnect(self.roundPhaseClearedCheckbox.setDisabled)
        self.roundWinnerRadioButton.toggled.disconnect(self.roundPhaseClearedCheckbox.setChecked)
        self.roundWinnerRadioButton.toggled.disconnect(self.roundWinnerSetAction)
        self.roundWinnerRadioButton.setDisabled(True)
        self.roundPhaseClearedCheckbox.setDisabled(True)
        self.roundScore.setDisabled(True)
        

class Phase10Label(QtGui.QLabel):
    
    def __init__(self,number,parent=None):
        super(Phase10Label, self).__init__(parent)
        self.setText(str(number).zfill(2))
        self.setAutoFillBackground(False)
        self.setRemaining()
        self.setFrameShape(QtGui.QFrame.StyledPanel)
#         self.setFrameShadow(QtGui.QFrame.Raised)
        self.setScaledContents(True)
        self.setAlignment(QtCore.Qt.AlignCenter)
        self.setWordWrap(False)
        self.setMinimumSize(25, 25)
        self.setSizePolicy(QtGui.QSizePolicy.MinimumExpanding,QtGui.QSizePolicy.MinimumExpanding)
#         self.setFixedSize(QtCore.QSize(40,40))
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


class Phase10RoundsDetail(GameRoundsDetail):
    
    def __init__(self, engine, iw, parent=None):
        self.iw = iw
        super(Phase10RoundsDetail, self).__init__(engine,parent)
        
    def initUI(self):
        super(Phase10RoundsDetail, self).initUI()
        self.container.insertTab(0,self.iw,"")  
        self.container.setCurrentIndex(0)
        
    def retranslateUI(self):
        self.setTitle(QtGui.QApplication.translate("GameRoundsDetail",'Details'))
        self.container.setTabText(0,QtGui.QApplication.translate("Phase10Widget","Score"))
        self.container.setTabText(1,QtGui.QApplication.translate("GameRoundsDetail","Table"))
        self.container.setTabText(2,QtGui.QApplication.translate("GameRoundsDetail","Plot"))
        self.container.setTabText(3,QtGui.QApplication.translate("GameRoundsDetail","Statistics"))
        self.gamestats.retranslateUI()
        self.plot.retranslateUI()
        self.updateRound()

    def createRoundTable(self, engine, parent=None):
        return Phase10RoundTable(self.engine, parent)
      
    def createRoundPlot(self, engine, parent=None): 
        return Phase10RoundPlot(self.engine,self)
    
    
class Phase10RoundTable(GameRoundTable):
    
    def insertRound(self,r):
        winner = r.getWinner()
        i = r.getNumRound() - 1
        self.insertRow(i)
        for j, player in enumerate(self.engine.getListPlayers()):
            item = QtGui.QTableWidgetItem()
            item.setFlags(item.flags()^QtCore.Qt.ItemIsEditable)
            item.setTextAlignment(QtCore.Qt.AlignVCenter|QtCore.Qt.AlignCenter)
            if player == winner:
                text = QtGui.QApplication.translate("Phase10RoundTable","Winner")
                font = item.font()
                font.setBold(True)
                item.setFont(font)   
            else:
                text = str(r.getPlayerScore(player))
            a_phase = r.getPlayerAimedPhase(player)
            c_phase = r.getPlayerCompletedPhase(player)
            text += QtGui.QApplication.translate("Phase10PlayerWidget", " (Phase {})").format(a_phase)
            if c_phase != 0: background = 0xCCFF99 #green
            else: background = 0xFFCC99 #red
            item.setBackground(QtGui.QBrush(QtGui.QColor(background)))
            item.setText(text)
            self.setItem(i,j,item)
        self.scrollToBottom()
        
        
class Phase10RoundPlot(GameRoundPlot):
    
    def initUI(self):
        super(Phase10RoundPlot,self).initUI()
        self.setStyleSheet("QLabel {font-size: 18px; }")
        QtGui.QWidget().setLayout(self.layout())
        self.widgetLayout = QtGui.QGridLayout()
        self.setLayout(self.widgetLayout)

        self.phasesLabel = QtGui.QLabel("",self)
        self.widgetLayout.addWidget(self.phasesLabel,0,0)
        self.scoreLabel = QtGui.QLabel("",self)
        self.widgetLayout.addWidget(self.scoreLabel,0,1)
        self.playersTitleLabel = QtGui.QLabel("",self)
        self.widgetLayout.addWidget(self.playersTitleLabel,0,2)
        
        self.canvas = PlotView(PlayerColours,self)
        self.canvas.setBackground(self.palette().color(self.backgroundRole()))
        self.canvas.addLinePlot()
        self.widgetLayout.addWidget(self.canvas,1,0)
        self.scorecanvas = PlotView(PlayerColours,self)
        self.scorecanvas.setBackground(self.palette().color(self.backgroundRole()))
        self.scorecanvas.addLinePlot()
        self.widgetLayout.addWidget(self.scorecanvas,1,1)
        
        self.playersListLayout = QtGui.QVBoxLayout()
        self.widgetLayout.addLayout(self.playersListLayout,1,2)
        
        self.playersListLayout.addStretch()
#         self.playersListLayout.addWidget(self.playersTitleLabel)
        
        for i,player in enumerate(self.engine.getListPlayers()):
            colour = PlayerColours[i]
            label = QtGui.QLabel(player)
            label.setStyleSheet("QLabel {{ font-size: 18px; font-weight: bold; color:rgb({},{},{});}}".format(colour.red(),colour.green(),colour.blue()))
            self.playersListLayout.addWidget(label)
#             self.playersListLayout.addStretch()
        
        self.playersListLayout.addStretch()

        self.retranslatePlot()
        self.updatePlot()
    
        
    def retranslatePlot(self):
        super(Phase10RoundPlot,self).retranslatePlot()
        self.phasesLabel.setText(QtGui.QApplication.translate("Phase10RoundPlot",'Phases') )
        self.scoreLabel.setText(QtGui.QApplication.translate("Phase10RoundPlot",'Scores') )
#         self.playersTitleLabel.setText(QtGui.QApplication.translate("Phase10RoundPlot",'Players') )
        
    def updatePlot(self):
        super(Phase10RoundPlot,self).updatePlot()
        if not self.isPlotInited(): return
        scores = {}
        phases = {}
        for player in self.engine.getPlayers():
            scores[player] = [0]
            phases[player] = [0]
            
        for rnd in self.engine.getRounds():
            for player in self.engine.getPlayers():
                if player not in scores: scores[player] = [0]
                rndscore = rnd.getPlayerScore(player)
                if rndscore >= 0 :
                    accumscore = scores[player][-1] + rndscore
                    scores[player].append(accumscore)
                c_phase = rnd.getPlayerCompletedPhase(player)
                if c_phase > 0: phases[player].append(phases[player][-1]+1)
                else: phases[player].append(phases[player][-1])
                
        self.canvas.clearPlotContents()
        self.scorecanvas.clearPlotContents()
        
        for player in self.engine.getListPlayers():        
            self.canvas.addSeries(phases[player],player)
            self.scorecanvas.addSeries(scores[player],player)
            
        
        