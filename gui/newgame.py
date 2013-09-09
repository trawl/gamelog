#!/usr/bin/env python
# -*- coding: utf-8 -*-

try:
    from PyQt4 import QtCore,QtGui
    QtCore.Signal = QtCore.pyqtSignal
    QtCore.Slot = QtCore.pyqtSlot
except ImportError as error:
    from PySide import QtCore,QtGui
    QtGui.QFileDialog.getOpenFileNameAndFilter = QtGui.QFileDialog.getOpenFileName

import datetime

from controllers.db import db
from controllers.resumeengine import ResumeEngine
from gui.tab import Tab
from gui.gamewidgetfactory import GameWidgetFactory
from gui.newplayer import NewPlayerDialog
from gui.gamestatsfactory import QSBoxFactory


class NewGameWidget(Tab):
    def __init__(self, parent=None):
        super(NewGameWidget, self).__init__(parent)
        self.parent = parent
        self.initUI()   

    def initUI(self):

        #Setup Layouts
        self.widgetLayout = QtGui.QHBoxLayout(self)
        self.leftColumnLayout = QtGui.QVBoxLayout()
        self.rightColumnLayout =  QtGui.QVBoxLayout()
        self.widgetLayout.addLayout(self.leftColumnLayout)
        self.widgetLayout.addLayout(self.rightColumnLayout)

        # Game GroupBox
        self.gameGroupBox = QtGui.QGroupBox(self)
        self.leftColumnLayout.addWidget(self.gameGroupBox)
        self.widgetLayout.setStretchFactor(self.leftColumnLayout,3)
        self.populateGamesGroupBox()

        #Players GroupBox
        self.playersGroupBox = QtGui.QGroupBox(self)
        self.rightColumnLayout.addWidget(self.playersGroupBox)
        self.widgetLayout.setStretchFactor(self.rightColumnLayout,1)
        self.populatePlayersGroupBox()
        
        self.retranslateUI()
    
    def retranslateUI(self):
        self.gameGroupBox.setTitle(QtGui.QApplication.translate("NewGameWidget","Games"))
        self.updateGameInfo()
        self.playersGroupBox.setTitle(QtGui.QApplication.translate("NewGameWidget","Players"))
        self.availablePlayersGroup.setTitle(QtGui.QApplication.translate("NewGameWidget","Available Players"))
        self.newPlayerButton.setText(QtGui.QApplication.translate("NewGameWidget","New Player"))
        self.inGameGroup.setTitle(QtGui.QApplication.translate("NewGameWidget","Selected Players"))
        self.startGameButton.setText(QtGui.QApplication.translate("NewGameWidget","Play!"))
        self.resumeGroup.retranslateUI()
        self.gameStatsBox.retranslateUI()
        
    def populateGamesGroupBox(self):

        self.gameGroupBoxLayout = QtGui.QVBoxLayout(self.gameGroupBox)
        self.gameComboBox = QtGui.QComboBox(self.gameGroupBox)
        self.gameGroupBoxLayout.addWidget(self.gameComboBox)
        self.gameDescriptionLabel = QtGui.QLabel(self.gameGroupBox)
        self.resumeGroup = ResumeBox(self.parent)
#        self.gameRulesBrowser = QtGui.QTextBrowser(self.gameGroupBox)
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
            
        self.gameStatsBox = QSBoxFactory.createQSBox(self.gameComboBox.currentText(),self)
        self.gameGroupBoxLayout.addWidget(self.gameStatsBox)            
            
        self.updateGameInfo()
        
        self.gameComboBox.currentIndexChanged.connect(self.updateGameInfo)

    def updateGameInfo(self,foo=0):
        game = str(self.gameComboBox.currentText())
        description = "2 - {} {}\n\n{}".format(self.games[game]['maxPlayers'],QtGui.QApplication.translate("NewGameWidget",'players'),self.games[game]['description'])
        self.gameDescriptionLabel.setText(description)
#        self.gameRulesBrowser.setText("{}".format(self.games[game]['rules']))
#         self.gameStatsBox.update(game)
        self.gameGroupBoxLayout.removeWidget(self.gameStatsBox)
        self.gameStatsBox.deleteLater()
        
        self.gameStatsBox = QSBoxFactory.createQSBox(game,self)
        self.gameGroupBoxLayout.addWidget(self.gameStatsBox)  
        
        self.resumeGroup.changeGame(game)

    def populatePlayersGroupBox(self):

        self.playersGroupBoxLayout = QtGui.QVBoxLayout(self.playersGroupBox)
        #Start button
        self.startGameButton = QtGui.QPushButton(self)
        self.startGameButton.clicked.connect(self.createNewGame)
        self.playersGroupBoxLayout.addWidget(self.startGameButton)
        
        self.inGameGroup = QtGui.QGroupBox(self)
        self.playersGroupBoxLayout.addWidget(self.inGameGroup)
        self.inGameGroupLayout = QtGui.QVBoxLayout(self.inGameGroup)
        self.playersInGameList = PlayerList(self.inGameGroup)
        self.inGameGroup.setMaximumHeight(150)
        self.inGameGroupLayout.addWidget(self.playersInGameList)
        
        self.playersButtonsLayout = QtGui.QHBoxLayout()
        self.playersGroupBoxLayout.addLayout(self.playersButtonsLayout)

        self.newPlayerButton = QtGui.QPushButton(self.playersGroupBox)
        self.newPlayerButton.clicked.connect(self.createNewPlayer)
        self.playersButtonsLayout.addWidget( self.newPlayerButton)


        self.availablePlayersGroup = QtGui.QGroupBox(self)
        self.playersGroupBoxLayout.addWidget(self.availablePlayersGroup)
        self.availablePlayersGroupLayout = QtGui.QVBoxLayout(self.availablePlayersGroup)
        self.playersAvailableList = PlayerList(self.playersGroupBox)
        self.availablePlayersGroupLayout.addWidget(self.playersAvailableList)
        
#        self.availablePlayersGroupLayout.addStretch()
        
        self.playersAvailableList.doubleclickeditem.connect(self.playersInGameList.addItem)
        self.playersInGameList.doubleclickeditem.connect(self.playersAvailableList.addItem)
        
        for p in db.getPlayers():
            if p['favourite']: self.playersInGameList.addItem(p['nick'])
            else: self.playersAvailableList.addItem(p['nick'])
        

    def createNewGame(self):
        game = str(self.gameComboBox.currentText())
        maxPlayers = self.games[game]['maxPlayers']
        players = self.playersInGameList.model().retrievePlayers()
        if len(players)<2:
            QtGui.QMessageBox.warning(self,QtGui.QApplication.translate("NewGameWidget","New Match"),QtGui.QApplication.translate("NewGameWidget","At least 2 players are needed to play"))
        elif len(players)>maxPlayers:
            QtGui.QMessageBox.warning(self,QtGui.QApplication.translate("NewGameWidget","New Match"),"{} {}".format(QtGui.QApplication.translate("NewGameWidget",'The maximum number of players is'), maxPlayers))
        else:
            matchTab = GameWidgetFactory.createGameWidget(game,players,self.parent)
            if matchTab:
                matchTab.closeRequested.connect(self.parent.removeTab)
                self.parent.newTab(matchTab,game)
            else:
                QtGui.QMessageBox.warning(self,QtGui.QApplication.translate("NewGameWidget","New Match"),QtGui.QApplication.translate("NewGameWidget","Widget not implemented"))
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
        return QtGui.QWidget.showEvent(self, event)


class PlayerList(QtGui.QListView):
    
    doubleclickeditem = QtCore.Signal(str)
    
    def __init__(self,parent):
        super(PlayerList, self).__init__(parent)
        self.setDragEnabled(True)
        self.setAcceptDrops(True)
        self.setModel(PlayerListModel())

        self.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.openMenu)

    def dropEvent(self, e):
        e.setDropAction(QtCore.Qt.MoveAction)
        QtGui.QListView.dropEvent(self,e)
            
    def addItem(self,text): self.model().addPlayer(text)

    def mouseDoubleClickEvent(self,event):
        item = self.indexAt(event.pos())
        try: player = str(item.data().toString())
        except AttributeError: player = str(item.data())
        self.doubleclickeditem.emit(player)
        self.model().removeRows(item.row(),1)
        return QtGui.QListView.mouseDoubleClickEvent(self,event)
    
    def openMenu(self,position):
        item = self.indexAt(position)
        if item.row()<0: return
        try: player = str(item.data().toString())
        except AttributeError: player = str(item.data())
        if player:
            menu = QtGui.QMenu()
            isfav =  db.isPlayerFavourite(player)
            if isfav:
                favouriteAction = QtGui.QAction(QtGui.QIcon('icons/player.png'),QtGui.QApplication.translate("PlayerList","Unset Favourite"), self)
            else:
                favouriteAction = QtGui.QAction( QtGui.QIcon('icons/fav.png'),QtGui.QApplication.translate("PlayerList","Set Favourite"), self)
            menu.addAction(favouriteAction)
            action = menu.exec_(self.mapToGlobal(position))
            if action == favouriteAction:
                isfav = not isfav
                db.setPlayerFavourite(player,isfav)
                self.model().addIcon(self.model().itemFromIndex(item),isfav)
        

class PlayerListModel(QtGui.QStandardItemModel):
    
    def __init__(self, parent = None):
        super(PlayerListModel, self).__init__( parent)

    def dropMimeData(self, data, action, row, column, parent):

        if data.hasFormat('application/x-qabstractitemmodeldatalist'):
            barray = data.data('application/x-qabstractitemmodeldatalist')
            data_items = self.decode_data(barray)

            # Assuming that we get at least one item, and that it defines
            # text that we can display.
            try:
                text = data_items[0][QtCore.Qt.DisplayRole].toString()
            except AttributeError:
                text = str(data_items[0][QtCore.Qt.DisplayRole])

#            self.appendRow(QtGui.QStandardItem(text))
            self.addPlayer(text,row)
            return True
        else:
            return QtGui.QStandardItemModel.dropMimeData(self, data, action, row, column, parent)

    def decode_data(self, barray):
        data = []
        item = {}
        ds = QtCore.QDataStream(barray)
        while not ds.atEnd():
            ds.readInt32() #Row 
            ds.readInt32() #Column
            map_items = ds.readInt32()
            for _ in range(map_items):
                key = ds.readInt32()
                try:
                    value = QtCore.QVariant()
                    ds >> value
                except AttributeError:
                    value = ds.readQVariant()
                item[QtCore.Qt.ItemDataRole(key)] = value
            data.append(item)
        return data
    
    def addPlayer(self,player,row=None):
        item = QtGui.QStandardItem(player)
        item.setEditable(False)
        item.setDropEnabled(False)
        font = item.font()
        font.setPixelSize(14)
        item.setFont(font)
        self.addIcon(item,db.isPlayerFavourite(player))
        if row is not None and row>=0:
            self.insertRow(row,item)
        else:        
            self.appendRow(item)
        
    def addIcon(self,item,isfav):
        if isfav: icon = QtGui.QIcon('icons/fav.png')
        else: icon = QtGui.QIcon('icons/player.png')
        item.setIcon(icon)

    def retrievePlayers(self):
        players = list()
        for i in range(self.rowCount()):
            nick =str(self.item(i).text())
            players.append(nick)
        return players
                
class ResumeBox(QtGui.QGroupBox):
    
    def __init__(self,parent):
        super(ResumeBox,self).__init__(parent)
        self.engine = None
        self.game = None
        self.parent = parent
        self.matches = []
        self.initUI()
        
    def initUI(self):
        self.widgetLayout = QtGui.QVBoxLayout(self)
        self.savedlist = QtGui.QListWidget(self)
        self.savedlist.setSelectionMode(QtGui.QAbstractItemView.SingleSelection)
        self.savedlist.hide()
        self.widgetLayout.addWidget(self.savedlist)
        self.buttonLayout = QtGui.QHBoxLayout()
        self.widgetLayout.addLayout(self.buttonLayout)
        self.resumebutton = QtGui.QPushButton(self)
        self.resumebutton.clicked.connect(self.resumeGame)
        self.resumebutton.hide()
        self.buttonLayout.addWidget(self.resumebutton)
        self.cancelbutton = QtGui.QPushButton(self)
        self.cancelbutton.clicked.connect(self.deleteGame)
        self.cancelbutton.hide()
        self.buttonLayout.addWidget(self.cancelbutton)
        self.emptyLabel = QtGui.QLabel(self)
        self.widgetLayout.addWidget(self.emptyLabel)
        self.retranslateUI()
        
    def retranslateUI(self):
        self.setTitle(QtGui.QApplication.translate("ResumeBox",'Saved Games'))
        self.resumebutton.setText(QtGui.QApplication.translate("ResumeBox",'Resume'))
        self.cancelbutton.setText(QtGui.QApplication.translate("ResumeBox",'Cancel'))
        self.emptyLabel.setText(QtGui.QApplication.translate("ResumeBox",'No matches to be resumed'))
    
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
                msg = QtGui.QApplication.translate("ResumeBox",'Saved on {}. Time played: {}').format(strtime,strelapsed)
                item = QtGui.QListWidgetItem(msg,self.savedlist)
                playerlist =""
                for player in candidate['players']:
                    playerlist += "\n  " + player
                item.setToolTip(QtGui.QApplication.translate("ResumeBox","Players: {}").format(playerlist))
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
            reply = QtGui.QMessageBox.question(self, QtGui.QApplication.translate("ResumeBox",'Cancel Saved Game'),
                QtGui.QApplication.translate("ResumeBox","Are you sure you want to cancel saved game?"), QtGui.QMessageBox.Yes | 
                QtGui.QMessageBox.No, QtGui.QMessageBox.No)

            if reply == QtGui.QMessageBox.No: return False
            gameengine = self.engine.resume(idMatch)
            gameengine.cancelMatch()
            self.changeGame(self.game)
        
            
