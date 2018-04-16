#!/usr/bin/env python
# -*- coding: utf-8 -*-

from PyQt5 import QtCore,QtWidgets
QtCore.Signal = QtCore.pyqtSignal
QtCore.Slot = QtCore.pyqtSlot


import datetime

from controllers.db import db
from controllers.resumeengine import ResumeEngine
from gui.tab import Tab
from gui.gamewidgetfactory import GameWidgetFactory
from gui.newplayer import NewPlayerDialog
from gui.gamestatsfactory import QSFactory
from gui.playerlist import PlayerList


class NewGameWidget(Tab):
    def __init__(self, parent=None):
        super(NewGameWidget, self).__init__(parent)
        self.parent = parent
        self.initUI()   

    def initUI(self):

        #Setup Layouts
        self.widgetLayout = QtWidgets.QHBoxLayout(self)
        self.leftColumnLayout = QtWidgets.QVBoxLayout()
        self.rightColumnLayout =  QtWidgets.QVBoxLayout()
        self.widgetLayout.addLayout(self.leftColumnLayout)
        self.widgetLayout.addLayout(self.rightColumnLayout)
        
        self.gameStatsBox = None
        
        #Players GroupBox
        self.playersGroupBox = QtWidgets.QGroupBox(self)
        self.rightColumnLayout.addWidget(self.playersGroupBox)
        self.widgetLayout.setStretchFactor(self.rightColumnLayout,1)
        self.populatePlayersGroupBox()
        
        # Game GroupBox
        self.gameGroupBox = QtWidgets.QGroupBox(self)
        self.leftColumnLayout.addWidget(self.gameGroupBox)
        self.widgetLayout.setStretchFactor(self.leftColumnLayout,3)
        self.populateGamesGroupBox()
        
#        self.retranslateUI()
    
    def retranslateUI(self):
        self.gameGroupBox.setTitle(QtWidgets.QApplication.translate("NewGameWidget","Games"))
        self.updateGameInfo()
        self.playersGroupBox.setTitle(QtWidgets.QApplication.translate("NewGameWidget","Players"))
        self.availablePlayersGroup.setTitle(QtWidgets.QApplication.translate("NewGameWidget","Available Players"))
        self.newPlayerButton.setText(QtWidgets.QApplication.translate("NewGameWidget","New Player"))
        self.inGameGroup.setTitle(QtWidgets.QApplication.translate("NewGameWidget","Selected Players"))
        self.startGameButton.setText(QtWidgets.QApplication.translate("NewGameWidget","Play!"))
        self.resumeGroup.retranslateUI()
        self.gameStatsBox.retranslateUI()
        
    def populateGamesGroupBox(self):

        self.gameGroupBoxLayout = QtWidgets.QVBoxLayout(self.gameGroupBox)
        self.gameComboBox = QtWidgets.QComboBox(self.gameGroupBox)
        self.gameGroupBoxLayout.addWidget(self.gameComboBox)
        self.gameDescriptionLabel = QtWidgets.QLabel(self.gameGroupBox)
        self.resumeGroup = ResumeBox(self.parent)
#        self.gameRulesBrowser = QtWidgets.QTextBrowser(self.gameGroupBox)
        self.gameGroupBoxLayout.addWidget(self.gameDescriptionLabel)
        self.gameGroupBoxLayout.addWidget(self.resumeGroup)
#        self.gameGroupBoxLayout.addWidget(self.gameRulesBrowser)

#        self.gameGroupBoxLayout.addStretch()

        self.games = db.getAvailableGames()
        for game in sorted(self.games.keys()):
            self.gameComboBox.addItem(game)
        lastgame = db.getLastGame()
        if lastgame:    
            self.gameComboBox.setCurrentIndex(self.gameComboBox.findText(lastgame))
            
        self.gameStatsBox = None       
            
#        self.updateGameInfo()
        
        self.gameComboBox.currentIndexChanged.connect(self.updateGameInfo)

    def updateGameInfo(self,foo=0):

        game = str(self.gameComboBox.currentText())
        description = "2 - {} {}\n\n{}".format(self.games[game]['maxPlayers'],QtWidgets.QApplication.translate("NewGameWidget",'players'),self.games[game]['description'])
        self.gameDescriptionLabel.setText(description)
#        self.gameRulesBrowser.setText("{}".format(self.games[game]['rules']))
#         self.gameStatsBox.update(game)
        if self.gameStatsBox is not None:
            self.gameGroupBoxLayout.removeWidget(self.gameStatsBox)
            print("UGI deleting")
            self.gameStatsBox.deleteLater()
        
        self.gameStatsBox = QSFactory.createQS(game,None,self)
        self.gameGroupBoxLayout.addWidget(self.gameStatsBox)  
        self.updateStats()
        self.resumeGroup.changeGame(game)
        
        
    def updateStats(self):
        if self.gameStatsBox:
            try:
                self.gameStatsBox.update(self.gameComboBox.currentText(), self.playersInGameList.model().retrievePlayers())
            except TypeError:
                # Should not happen, but silently ignore
                pass


    def populatePlayersGroupBox(self):

        self.playersGroupBoxLayout = QtWidgets.QVBoxLayout(self.playersGroupBox)
        #Start button
        self.startGameButton = QtWidgets.QPushButton(self)
        self.startGameButton.clicked.connect(self.createNewGame)
        self.playersGroupBoxLayout.addWidget(self.startGameButton)
        
        self.inGameGroup = QtWidgets.QGroupBox(self)
        self.playersGroupBoxLayout.addWidget(self.inGameGroup)
        self.inGameGroupLayout = QtWidgets.QVBoxLayout(self.inGameGroup)
        self.playersInGameList = PlayerList(None,self.inGameGroup)
        self.inGameGroup.setMaximumHeight(280)
        self.inGameGroupLayout.addWidget(self.playersInGameList)
        
        self.playersButtonsLayout = QtWidgets.QHBoxLayout()
        self.playersGroupBoxLayout.addLayout(self.playersButtonsLayout)

        self.newPlayerButton = QtWidgets.QPushButton(self.playersGroupBox)
        self.newPlayerButton.clicked.connect(self.createNewPlayer)
        self.playersButtonsLayout.addWidget( self.newPlayerButton)


        self.availablePlayersGroup = QtWidgets.QGroupBox(self)
        self.playersGroupBoxLayout.addWidget(self.availablePlayersGroup)
        self.availablePlayersGroupLayout = QtWidgets.QVBoxLayout(self.availablePlayersGroup)
        self.playersAvailableList = PlayerList(None, self.playersGroupBox)
        self.availablePlayersGroupLayout.addWidget(self.playersAvailableList)
        
#        self.availablePlayersGroupLayout.addStretch()
        
        self.playersAvailableList.doubleclickeditem.connect(self.playersInGameList.addItem)
        self.playersInGameList.doubleclickeditem.connect(self.playersAvailableList.addItem)
        self.playersInGameList.changed.connect(self.updateStats)
        
        for p in db.getPlayers():
            if p['favourite']: self.playersInGameList.addItem(p['nick'])
            else: self.playersAvailableList.addItem(p['nick'])
        

    def createNewGame(self):
        game = str(self.gameComboBox.currentText())
        maxPlayers = self.games[game]['maxPlayers']
        players = self.playersInGameList.model().retrievePlayers()
        if len(players)<2:
            QtWidgets.QMessageBox.warning(self,QtWidgets.QApplication.translate("NewGameWidget","New Match"),QtWidgets.QApplication.translate("NewGameWidget","At least 2 players are needed to play"))
        elif len(players)>maxPlayers:
            QtWidgets.QMessageBox.warning(self,QtWidgets.QApplication.translate("NewGameWidget","New Match"),"{} {}".format(QtWidgets.QApplication.translate("NewGameWidget",'The maximum number of players is'), maxPlayers))
        else:
            matchTab = GameWidgetFactory.createGameWidget(game,players,self.parent)
            if matchTab:
                matchTab.closeRequested.connect(self.parent.removeTab)
                self.parent.newTab(matchTab,game)
            else:
                QtWidgets.QMessageBox.warning(self,QtWidgets.QApplication.translate("NewGameWidget","New Match"),QtWidgets.QApplication.translate("NewGameWidget","Widget not implemented"))
                return

    def createNewPlayer(self):
        npd = NewPlayerDialog(self)
        npd.addedNewPlayer.connect(self.addPlayer)
        npd.exec_()
    
    def addPlayer(self,player):
        player = str(player)
        self.playersAvailableList.model().addPlayer(player)
        
    def showEvent(self, event):
        if hasattr(self, 'gameStatsBox') and hasattr(self,'gameComboBox') and self.gameComboBox.currentText(): 
            self.gameStatsBox.update(self.gameComboBox.currentText())
            self.resumeGroup.changeGame(self.gameComboBox.currentText())
        return QtWidgets.QWidget.showEvent(self, event)



                
class ResumeBox(QtWidgets.QGroupBox):
    
    def __init__(self,parent):
        super(ResumeBox,self).__init__(parent)
        self.engine = None
        self.game = None
        self.parent = parent
        self.matches = []
        self.initUI()
        
    def initUI(self):
        self.widgetLayout = QtWidgets.QVBoxLayout(self)
        self.savedlist = QtWidgets.QListWidget(self)
        self.savedlist.setSelectionMode(QtWidgets.QAbstractItemView.SingleSelection)
        self.savedlist.hide()
        self.widgetLayout.addWidget(self.savedlist)
        self.buttonLayout = QtWidgets.QHBoxLayout()
        self.widgetLayout.addLayout(self.buttonLayout)
        self.resumebutton = QtWidgets.QPushButton(self)
        self.resumebutton.clicked.connect(self.resumeGame)
        self.resumebutton.hide()
        self.buttonLayout.addWidget(self.resumebutton)
        self.cancelbutton = QtWidgets.QPushButton(self)
        self.cancelbutton.clicked.connect(self.deleteGame)
        self.cancelbutton.hide()
        self.buttonLayout.addWidget(self.cancelbutton)
        self.emptyLabel = QtWidgets.QLabel(self)
        self.widgetLayout.addWidget(self.emptyLabel)
        self.retranslateUI()
        
    def retranslateUI(self):
        self.setTitle(QtWidgets.QApplication.translate("ResumeBox",'Saved Games'))
        self.resumebutton.setText(QtWidgets.QApplication.translate("ResumeBox",'Resume'))
        self.cancelbutton.setText(QtWidgets.QApplication.translate("ResumeBox",'Cancel'))
        self.emptyLabel.setText(QtWidgets.QApplication.translate("ResumeBox",'No matches to be resumed'))
    
    def changeGame(self,game):
        self.game = game
        self.engine = ResumeEngine(game)
        self.savedlist.clear()
        self.matches = []
        candidates = self.engine.getCandidates()
        if not candidates:
            self.savedlist.hide()
            self.resumebutton.hide()
            self.cancelbutton.hide()
            self.emptyLabel.show()
        else:
            self.emptyLabel.hide()
            for idMatch,candidate in candidates.items():
                self.matches.append(idMatch)
                savedtime = datetime.datetime.strptime(candidate['started'],"%Y-%m-%d %H:%M:%S.%f")
                strtime = savedtime.strftime("%Y-%m-%d %H:%M:%S")
                hours, remainder = divmod(int(candidate['elapsed']), 3600)
                minutes, seconds = divmod(remainder,60)
                strelapsed =  "{0:02}:{1:02}:{2:02}".format(hours,minutes,seconds)
                msg = QtWidgets.QApplication.translate("ResumeBox",'Saved on {}. Time played: {}').format(strtime,strelapsed)
                item = QtWidgets.QListWidgetItem(msg,self.savedlist)
                playerlist =""
                for player in candidate['players']:
                    playerlist += "\n  " + player
                item.setToolTip(QtWidgets.QApplication.translate("ResumeBox","Players: {}").format(playerlist))
                self.savedlist.addItem(item)
            self.savedlist.show()
            self.resumebutton.show()
            self.cancelbutton.show()
                
    def resumeGame(self):
        selected = self.savedlist.selectedIndexes()
        if len(selected)>0:
            idMatch = self.matches[selected[0].row()]
            gameengine = self.engine.resume(idMatch)
            matchTab = GameWidgetFactory.resumeGameWidget(self.game,gameengine,self.parent)
            if matchTab:
                matchTab.closeRequested.connect(self.parent.removeTab)
                self.parent.newTab(matchTab,self.game)
                
    def deleteGame(self):
        selected = self.savedlist.selectedIndexes()
        if len(selected)>0:
            idMatch = self.matches[selected[0].row()]
            reply = QtWidgets.QMessageBox.question(self, QtWidgets.QApplication.translate("ResumeBox",'Cancel Saved Game'),
                QtWidgets.QApplication.translate("ResumeBox","Are you sure you want to cancel saved game?"), QtWidgets.QMessageBox.Yes | 
                QtWidgets.QMessageBox.No, QtWidgets.QMessageBox.No)

            if reply == QtWidgets.QMessageBox.No: return False
            gameengine = self.engine.resume(idMatch)
            gameengine.cancelMatch()
            self.changeGame(self.game)
        
            
