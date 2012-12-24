#!/usr/bin/env python
# -*- coding: utf-8 -*-

import random

try:
    from PySide import QtCore,QtGui
    QtGui.QFileDialog.getOpenFileNameAndFilter = QtGui.QFileDialog.getOpenFileName
except ImportError as error:
    from PyQt4 import QtCore,QtGui
    QtCore.Signal = QtCore.pyqtSignal
    QtCore.Slot = QtCore.pyqtSlot
    
from controllers.db import db
from controllers.phase10engine import Phase10Engine
from model.phase10 import Phase10Round
from gui.message import ErrorMessage
from gui.clock import GameClock

class Phase10Widget(QtGui.QWidget):

    def __init__(self, game, players, parent=None):
        super(Phase10Widget, self).__init__(parent)

        self.game = game
        self.players=players
        self.phases = dict()
        self.phases["key"] = list()
        self.phases["desc"] = list()
        self.phases["key"].append("") # Empty phase (0)
        self.phases["desc"].append("") # Empty phase (0)
        self.engine = Phase10Engine()
        for nick in players:
            self.engine.addPlayer(nick)
        self.engine.begin(self.game)
        self.engine.printStats()

        cur = db.execute("Select key,value from GameExtras where Game_name='"+self.game+"' and key like'Phase %'")
        for row in cur:
            self.phases["key"].append(row['key'])
            self.phases["desc"].append(row['value'])
        self.initUI()


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
        
        self.clock = GameClock(self)
        self.clock.setMinimumHeight(100)
        self.widgetLayout.addWidget(self.clock,0,1)
        
        
        self.phasesInOrderCheckBox = QtGui.QCheckBox(self)
        self.phasesInOrderCheckBox.setText("Seguir las fases en orden")
        self.phasesInOrderCheckBox.setChecked(True)
        self.phasesInOrderCheckBox.setStyleSheet("QCheckBox { font-size: 14px; font-weight: bold; }")
        
        self.miscElementsLayout.addWidget(self.phasesInOrderCheckBox)
        
        self.extraGroup = QtGui.QGroupBox(self)
        self.extraGroup.setTitle("Phases")
        self.extraGroup.setStyleSheet("QGroupBox { font-size: 18px; font-weight: bold; }")
        self.miscElementsLayout.addWidget(self.extraGroup)
        self.extraGroupLayout = QtGui.QVBoxLayout(self.extraGroup)
        
        text =""
        for phase in range(1,len(self.phases["key"])):
            text = self.phases["key"][phase] + ": " + self.phases["desc"][phase] +"\n"
            label = QtGui.QLabel(text,self)
            label.setStyleSheet("QLabel {font-size: 14px; font-weight: bold; }")
            self.extraGroupLayout.addWidget(label)
   
        self.buttonGroup=QtGui.QGroupBox(self)
        self.buttonGroup.setTitle("Ronda {}".format(str(self.engine.getNumRound())))
        self.buttonGroup.setStyleSheet("QGroupBox { font-size: 18px; font-weight: bold; }")
        
        self.widgetLayout.addWidget(self.buttonGroup,0,0)
        self.buttonGroupLayout= QtGui.QHBoxLayout(self.buttonGroup)

        self.cancelMatchButton = QtGui.QPushButton("&Finalizar Partida", self.buttonGroup)
        self.buttonGroupLayout.addWidget(self.cancelMatchButton)
        self.cancelMatchButton.clicked.connect(self.cancelMatch)

        self.detailMatchButton = QtGui.QPushButton("&Detalles...", self.buttonGroup)
        self.detailMatchButton.setDisabled(True)
        self.buttonGroupLayout.addWidget(self.detailMatchButton)
        self.detailMatchButton.clicked.connect(self.showDetails)

        self.commitRoundButton = QtGui.QPushButton("Cerrar &Ronda", self.buttonGroup)
        self.buttonGroupLayout.addWidget(self.commitRoundButton)
        self.commitRoundButton.clicked.connect(self.commitRound)

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
            self.playerGroupBox[player] = Phase10PlayerWidget(player, self.phases,self.winnerButtonGroup,self)
            QtCore.QObject.connect(self.phasesInOrderCheckBox, QtCore.SIGNAL('stateChanged(int)'), self.playerGroupBox[player].switchPhasesInOrder)
            if players_grid: 
                self.playerGroupsLayout.addWidget(self.playerGroupBox[player],np/2,np%2)
            else: self.playerGroupsLayout.addWidget(self.playerGroupBox[player])    
            np += 1
            
        if not players_grid: self.playerGroupsLayout.addStretch()
        
        self.shuffler = random.choice(range(0,len(self.players)))
        self.playerGroupBox[self.players[self.shuffler]].setShuffler()
        

                
    def commitRound(self):

        #Check Round parameters
        rnd = Phase10Round()
        winner=None
        for player in self.players:
            pw = self.playerGroupBox[player]
            a_phase = pw.getRoundPhase()
            cleared =  pw.isRoundCleared()
            if pw.isWinner():
                winner = player
                score = 0
                if not cleared:
                    ErrorMessage(u"Ninguna Phase seleccionada para el ganador ({})".format(player)).exec_()
                    return

            else:
                try:
                    score = int(pw.getRoundScore())
                except ValueError:
                    ErrorMessage(u"La puntuación de {} no es válida".format(player)).exec_()
                    return
                if score%5!=0 or (score<50 and not cleared):
                    ErrorMessage(u"La puntuación {} de {} no es válida".format(str(score), player)).exec_()
                    return
            rnd.addRoundInfo(player,score,a_phase,cleared)
        if not winner:
            ErrorMessage("Debe haber un ganador").exec_()
            return

        #Everything ok so far, let's confirm
        ret = QtGui.QMessageBox.question(self, 'Cerrar Ronda',
        u"Estás seguro que quieres cerrar la ronda actual?", QtGui.QMessageBox.Yes | 
        QtGui.QMessageBox.No, QtGui.QMessageBox.Yes)
        
        if ret == QtGui.QMessageBox.No:
            print "Commit Cancelled"
            return

        # Once here, we can commit round...
                    
        self.playerGroupBox[self.players[self.shuffler]].unsetShuffler() 
        
        self.engine.addRound(rnd)
        self.engine.printStats()
        
        self.updatePanel()
        winner = self.engine.getWinner()
        if winner:
            for player in self.players:
                self.playerGroupBox[player].setDisabled(True)
                self.clock.stopTimer()
                self.commitRoundButton.setDisabled(True)
                self.phasesInOrderCheckBox.setDisabled(True)
                
            if winner=="Dani":
                ErrorMessage("{} ha ganado la partida. Ya era hora!!!!!".format(winner),"Fin de la partida").exec_()
            else:
                ErrorMessage("{} ha ganado la partida.".format(winner),"Fin de la partida").exec_()

        else:
            self.shuffler = (self.shuffler + 1)%len(self.players)            
            self.playerGroupBox[self.players[self.shuffler]].setShuffler() 
            


    def updatePanel(self):
        
        self.detailMatchButton.setEnabled(True)
        self.phasesInOrderCheckBox.setDisabled(True)
        if not self.engine.getWinner():
            self.buttonGroup.setTitle("Ronda {}".format(str(self.engine.getNumRound())))
            
        self.nobodyWinnerRadioButton.setChecked(True)
        for player in self.players:
            score = self.engine.getScoreFromPlayer(player)
            completed = self.engine.getCompletedPhasesFromPlayer(player)
            remaining = self.engine.getRemainingPhasesFromPlayer(player)
            self.playerGroupBox[player].updateDisplay(score,completed,remaining)


    def cancelMatch(self):
        
        ret = QtGui.QMessageBox.question(self, 'Finalizar partida',
        u"Estás seguro que quieres finalizar la partida?", QtGui.QMessageBox.Yes | 
        QtGui.QMessageBox.No, QtGui.QMessageBox.No)
        
        if ret == QtGui.QMessageBox.No:
            print "Cancel aborted"
            return
        self.closeMatch()

    def closeMatch(self):
        self.engine.cancelMatch()
        parent = self.nativeParentWidget()
        parent.tabWidget.removeTab(parent.tabWidget.indexOf(self))
        

    def showDetails(self):
        Phase10RoundsDetail(self.engine).exec_()



class Phase10PlayerWidget(QtGui.QGroupBox):
    def __init__(self, nick, phases, bgroup = None, parent=None):
        super(Phase10PlayerWidget,self).__init__(parent)
        self.setStyleSheet("QGroupBox { font-size: 18px; font-weight: bold; }")
        self.phases = phases
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
        self.scoreLCD.setMinimumWidth(75)
        self.scoreLCD.setMaximumHeight(100)
        
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
        self.roundWinnerRadioButton.setText("Ganador")
        self.bgroup.addButton(self.roundWinnerRadioButton)
#        layout.addWidget(self.roundWinnerRadioButton)
        self.rightLayout.addWidget(self.roundWinnerRadioButton,0,0)
        
        
        self.roundScore=QtGui.QLineEdit(self)
        self.roundScore.setFixedWidth(30)
        self.roundScore.setValidator(QtGui.QIntValidator(5,200,None))
        self.rightLayout.addWidget(self.roundScore,0,1)

        self.roundPhaseClearedCheckbox = QtGui.QCheckBox("Expuesta",self)
        self.rightLayout.addWidget(self.roundPhaseClearedCheckbox,1,0)

        QtCore.QObject.connect(self.roundWinnerRadioButton, QtCore.SIGNAL('toggled(bool)'), self.roundScore, QtCore.SLOT('setDisabled(bool)') )
        QtCore.QObject.connect(self.roundWinnerRadioButton, QtCore.SIGNAL('toggled(bool)'), self.roundPhaseClearedCheckbox,QtCore.SLOT('setDisabled(bool)'))
        QtCore.QObject.connect(self.roundWinnerRadioButton, QtCore.SIGNAL('toggled(bool)'), self.roundPhaseClearedCheckbox, QtCore.SLOT('setChecked(bool)') )
        QtCore.QObject.connect(self.roundScore, QtCore.SIGNAL('textChanged(QString)'), self.updateRoundPhaseCleared)
            
    def updateDisplay(self,points,completed_phases,remaining_phases):
        
        if len(remaining_phases)==0:
            self.current_phase=0
        else: self.current_phase = min(remaining_phases)
        
        self.roundWinnerRadioButton.setDown(True)
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
            
    def setShuffler(self):
        self.setStyleSheet("QGroupBox { font-size: 18px; font-weight: bold; color: red }")
        
    def unsetShuffler(self):
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
        self.setWindowTitle('Detalles')
        self.widgetLayout = QtGui.QVBoxLayout(self)
        self.table = QtGui.QTableWidget(self.engine.getNumRound()-1,len(self.engine.getPlayers()))
        self.widgetLayout.addWidget(self.table)
        roundlist = list()
        rounds = self.engine.getRounds()
        players = self.engine.getListPlayers()
        for i in range(1, len(rounds)+1):
            roundlist.append("Ronda {}".format(i))
        self.table.setVerticalHeaderLabels(roundlist)
        self.table.setHorizontalHeaderLabels(players)
        i = 0
        j = 0
        for r in rounds:
            j=0
            for player in players:
                item = QtGui.QTableWidgetItem(str(r.score[player]))
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

