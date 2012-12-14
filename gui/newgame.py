#!/usr/bin/env python
# -*- coding: utf-8 -*-

try:
    from PySide import QtCore,QtGui
    QtGui.QFileDialog.getOpenFileNameAndFilter = QtGui.QFileDialog.getOpenFileName
except ImportError as error:
    from PyQt4 import QtCore,QtGui
    QtCore.Signal = QtCore.pyqtSignal
    QtCore.Slot = QtCore.pyqtSlot
    

from controllers.db import *
from gui.message import *
from gui.phase10 import *

class PlayerListModel(QtGui.QStandardItemModel):

    def __init__(self, parent = None):
        super(PlayerListModel, self).__init__( parent)

    def dropMimeData(self, data, action, row, column, parent):

        if data.hasFormat('application/x-qabstractitemmodeldatalist'):
            bytearray = data.data('application/x-qabstractitemmodeldatalist')
            data_items = self.decode_data(bytearray)

            # Assuming that we get at least one item, and that it defines
            # text that we can display.
            try:
                text = data_items[0][QtCore.Qt.DisplayRole].toString()
            except AttributeError:
                text = str(data_items[0][QtCore.Qt.DisplayRole])

            self.appendRow(QtGui.QStandardItem(text))

            return True
        else:
            return QtGui.QStandardItemModel.dropMimeData(self, data, action, row, column, parent)

    def decode_data(self, bytearray):
        data = []
        item = {}
        ds = QtCore.QDataStream(bytearray)
        while not ds.atEnd():
            row = ds.readInt32()
            column = ds.readInt32()
            map_items = ds.readInt32()
            for i in range(map_items):
                key = ds.readInt32()
                try:
                    value = QtCore.QVariant()
                    ds >> value
                except AttributeError:
                    value = ds.readQVariant()
                item[QtCore.Qt.ItemDataRole(key)] = value
            data.append(item)
        return data

    def retrievePlayers(self):
        players = list()
        for i in range(self.rowCount()):
            nick =str(self.item(i).text())
            players.append(nick)
        return players


class PlayerList(QtGui.QListView):
    def __init__(self,parent):
        super(PlayerList, self).__init__(parent)
        self.setDragEnabled(True)
        self.setAcceptDrops(True)
        self.setModel(PlayerListModel())

    def dropEvent(self, e):
        if e.source()==self:
            e.ignore()
        else:
            e.setDropAction(QtCore.Qt.MoveAction)
            QtGui.QListView.dropEvent(self,e)


class NewGameWidget(QtGui.QWidget):
    #TODO: If more than one game, signals & slots to change desc and rules if game is changed.
    def __init__(self, parent=None):
        super(NewGameWidget, self).__init__(parent)
        self.openedGames = list()
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
        self.populateGamesGroupBox()

        #Start button
        self.startGameButton = QtGui.QPushButton(self)
        self.startGameButton.setText("A Jugar!")
        self.startGameButton.clicked.connect(self.createNewGame)
        self.leftColumnLayout.addWidget(self.startGameButton)

        #Players GroupBox
        self.playersGroupBox = QtGui.QGroupBox(self)
        self.rightColumnLayout.addWidget(self.playersGroupBox)
        self.populatePlayersGroupBox()


    def populateGamesGroupBox(self):
        self.gameGroupBox.setTitle("Juegos")
        self.gameGroupBoxLayout = QtGui.QVBoxLayout(self.gameGroupBox)
        self.gameComboBox = QtGui.QComboBox(self.gameGroupBox)
        self.gameGroupBoxLayout.addWidget(self.gameComboBox)
        self.gameDescriptionLabel = QtGui.QLabel(self.gameGroupBox)
        self.gameRulesBrowser = QtGui.QTextBrowser(self.gameGroupBox)
        self.gameGroupBoxLayout.addWidget(self.gameDescriptionLabel)
        self.gameGroupBoxLayout.addWidget(self.gameRulesBrowser)

        cur = db.execute("Select name,maxPlayers,description,rules from Game")
        self.games=dict()
        for row in cur:
            self.games[row['name']]=dict()
            self.games[row['name']]['maxPlayers']=row['maxPlayers']
            self.games[row['name']]['description']=row['description']
            self.games[row['name']]['rules']=row['rules']
            self.gameComboBox.addItem(row['name'])
        self.updateGameInfo()

        QtCore.QObject.connect(self.gameComboBox, QtCore.SIGNAL('currentIndexChanged(int)'), self.updateGameInfo )

    def updateGameInfo(self,foo=0):
        game = str(self.gameComboBox.currentText())
        description = "De 2 a {} jugadores\n\n{}".format(self.games[game]['maxPlayers'],self.games[game]['description'])
        self.gameDescriptionLabel.setText(description)
        self.gameRulesBrowser.setText("{}".format(self.games[game]['rules']))

    def populatePlayersGroupBox(self):
        self.playersGroupBox.setTitle("Jugadores")
        self.playersGroupBoxLayout = QtGui.QVBoxLayout(self.playersGroupBox)

        self.availablePlayersLabel = QtGui.QLabel(self.playersGroupBox)
        self.availablePlayersLabel.setText("Jugadores Disponibles")
        self.playersGroupBoxLayout.addWidget(self.availablePlayersLabel)
        self.playersAvailableList = PlayerList(self.playersGroupBox)
        self.playersGroupBoxLayout.addWidget(self.playersAvailableList)

        cur = db.execute("Select nick from Player")
        for row in cur:
            self.playersAvailableList.model().appendRow(QtGui.QStandardItem(row['nick']))

        self.playersButtonsLayout = QtGui.QHBoxLayout()
        self.playersGroupBoxLayout.addLayout(self.playersButtonsLayout)

        self.newPlayerButton = QtGui.QPushButton(self.playersGroupBox)
        self.newPlayerButton.setText("Nuevo Jugador")
        self.playersButtonsLayout.addWidget( self.newPlayerButton)


        self.inGameLabel = QtGui.QLabel(self.playersGroupBox)
        self.inGameLabel.setText("Jugadores seleccionados")
        self.playersGroupBoxLayout.addWidget(self.inGameLabel)
        self.playersInGameList = PlayerList(self.playersGroupBox)
        self.playersGroupBoxLayout.addWidget(self.playersInGameList)

    def createNewGame(self):
        game = str(self.gameComboBox.currentText())
        maxPlayers = self.games[game]['maxPlayers']
        players = self.playersInGameList.model().retrievePlayers()
        print "Now I would create a new {} game".format(game)
        print "Players in game (max {}):".format(maxPlayers)
        print players
        if len(players)<2:
            ErrorMessage("Se necesitan al menos 2 jugadores para jugar a {}".format(game),"Nueva Partida").exec_()
            #print "At least 2 players needed!"
        elif len(players)>maxPlayers:
            ErrorMessage("El máximo número de jugadores para {} es {}".format(game, maxPlayers),"Nueva Partida").exec_()

        else:
            parent = self.nativeParentWidget()
            matchTab = Phase10Widget(game, players,parent)
            self.openedGames.append(matchTab)
            idx = parent.tabWidget.addTab(matchTab, game)
            parent.tabWidget.setCurrentIndex(idx)
            
    def closeMatches(self):
        for game in self.openedGames:
            game.closeMatch()

