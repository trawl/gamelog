#!/usr/bin/env python
# -*- coding: utf-8 -*-

try:
    from PySide import QtCore,QtGui
    QtGui.QFileDialog.getOpenFileNameAndFilter = QtGui.QFileDialog.getOpenFileName
except ImportError as error:
    from PyQt4 import QtCore,QtGui
    QtCore.Signal = QtCore.pyqtSignal
    QtCore.Slot = QtCore.pyqtSlot
    

from controllers.db import db
from controllers.statsengine import StatsEngine
from gui.message import ErrorMessage
from gui.phase10 import Phase10Widget
from gui.newplayer import NewPlayerDialog

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

            self.appendRow(QtGui.QStandardItem(text))

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
            
            
class QuickStatsBox(QtGui.QGroupBox):
    def __init__(self,parent):
        super(QuickStatsBox, self).__init__(parent)
        self.stats = StatsEngine()
        self.game = None
        self.initUI()
        self.gameStatsText = u"Último Ganador: {} ({})"
        
    def initUI(self):
        self.setTitle(u"Estadísticas")
        self.widgetLayout = QtGui.QVBoxLayout(self)
        self.gameStatsLabel = QtGui.QLabel(self)
        self.widgetLayout.addWidget(self.gameStatsLabel)
        self.matchStatsTitleLabel = QtGui.QLabel(self)
        self.widgetLayout.addWidget(self.matchStatsTitleLabel)
        self.matchStatsTitleLabel.setText("Partidas")   
        self.matchStatsTable = QtGui.QTableWidget(self)
        self.matchStatsTable.setMinimumSize(0, 10)
        self.widgetLayout.addWidget(self.matchStatsTable)
        self.playerStatsTitleLabel = QtGui.QLabel(self)
        self.widgetLayout.addWidget(self.playerStatsTitleLabel)
        self.playerStatsTitleLabel.setText("Jugadores")  
        self.playerStatsTable = QtGui.QTableWidget(self)
        self.widgetLayout.addWidget(self.playerStatsTable)
        
        
    def update(self,game=None):
        if game is not None: self.game = game
        self.stats.update()
        gamestats = self.stats.getGameStats(self.game)
        matchstats = self.stats.getMatchGameStats(self.game)
        playerstats = self.stats.getPlayerGameStats(self.game)
        
        if not gamestats:
            self.gameStatsLabel.setText("No hay estadisticas")
            return
        
        self.gameStatsLabel.setText(self.gameStatsText.format(gamestats['lastwinner'],gamestats['lastwinnerdate']))
         
        keys = ['maxduration','minduration','avgduration','maxscore','minscore','avgscore']
        headers = ['Mas Larga','Mas corta','Media','Peor','Mejor','Media']
        self.updateTable(self.matchStatsTable, matchstats, keys, 'nplayers', headers)
            
        keys = ['played','victories','victoryp','maxscore','minscore','avgscore','sumscore']
        headers = ['Jugadas','Victorias','Ratio (%)','Peor','Mejor','Media','Total']
        self.updateTable(self.playerStatsTable, playerstats, keys, 'nick', headers)
                            

    def updateTable(self,table,contents,keyorder,rowheaderkey,cheaders):
        table.clear()
        if len(contents) and len(contents[0])>1:
            displayed = contents[:4]
            table.setRowCount(len(displayed))
            table.setColumnCount(len(displayed[0])-2)
            table.setHorizontalHeaderLabels(cheaders)
            table.setVerticalHeaderLabels([ str(row[rowheaderkey]) for row in displayed])
            

            for row, i in zip(displayed,range(len(displayed))):
                keys = keyorder
                for key,j in zip(keys,range(len(keys))):
                    item = QtGui.QTableWidgetItem(str(row[key]))
                    item.setTextAlignment(QtCore.Qt.AlignVCenter|QtCore.Qt.AlignHCenter)
                    item.setFlags(item.flags()^QtCore.Qt.ItemIsEditable)
                    table.setItem(i,j,item)
                    
            table.horizontalHeader().setResizeMode(QtGui.QHeaderView.Stretch)
            table.resizeRowsToContents()
            table.verticalHeader().setResizeMode(QtGui.QHeaderView.ResizeToContents)
            size = table.rowHeight(0)*(len(displayed)+1)+len(displayed)
            table.setFixedHeight(size)          
        

class NewGameWidget(QtGui.QWidget):
    def __init__(self, parent=None):
        super(NewGameWidget, self).__init__(parent)
        self.parent = parent
#        self.com = Communicator()
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
        self.gameStatsBox = QuickStatsBox(self)
        self.gameGroupBoxLayout.addWidget(self.gameStatsBox)
        self.gameGroupBoxLayout.addStretch()

        self.games = db.getAvailableGames()
        for game in sorted(self.games.keys()):
            self.gameComboBox.addItem(game)
        self.updateGameInfo()
        
        self.gameComboBox.currentIndexChanged.connect(self.updateGameInfo)

    def updateGameInfo(self,foo=0):
        game = str(self.gameComboBox.currentText())
        description = "De 2 a {} jugadores\n\n{}".format(self.games[game]['maxPlayers'],self.games[game]['description'])
        self.gameDescriptionLabel.setText(description)
        self.gameRulesBrowser.setText("{}".format(self.games[game]['rules']))
        self.gameStatsBox.update(game)

    def populatePlayersGroupBox(self):
        self.playersGroupBox.setTitle("Jugadores")
        self.playersGroupBoxLayout = QtGui.QVBoxLayout(self.playersGroupBox)

        self.availablePlayersLabel = QtGui.QLabel(self.playersGroupBox)
        self.availablePlayersLabel.setText("Jugadores Disponibles")
        self.playersGroupBoxLayout.addWidget(self.availablePlayersLabel)
        self.playersAvailableList = PlayerList(self.playersGroupBox)
        self.playersGroupBoxLayout.addWidget(self.playersAvailableList)

        for nick in db.getPlayerNicks():
            self.playersAvailableList.model().appendRow(QtGui.QStandardItem(nick))

        self.playersButtonsLayout = QtGui.QHBoxLayout()
        self.playersGroupBoxLayout.addLayout(self.playersButtonsLayout)

        self.newPlayerButton = QtGui.QPushButton(self.playersGroupBox)
        self.newPlayerButton.setText("Nuevo Jugador")
        self.newPlayerButton.clicked.connect(self.createNewPlayer)
        self.playersButtonsLayout.addWidget( self.newPlayerButton)


        self.inGameLabel = QtGui.QLabel(self.playersGroupBox)
        self.inGameLabel.setText("Jugadores seleccionados")
        self.playersGroupBoxLayout.addWidget(self.inGameLabel)
        self.playersInGameList = PlayerList(self.playersGroupBox)
        self.playersGroupBoxLayout.addWidget(self.playersInGameList)
        
        #Start button
        self.startGameButton = QtGui.QPushButton(self)
        self.startGameButton.setText("A Jugar!")
        self.startGameButton.clicked.connect(self.createNewGame)
        self.playersGroupBoxLayout.addWidget(self.startGameButton)

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
            matchTab = Phase10Widget(game, players,self.parent)
            self.parent.newTab(matchTab,game)

    def createNewPlayer(self):
        npd = NewPlayerDialog(self)
        npd.addedNewPlayer.connect(self.addPlayer)
    
    def addPlayer(self,player):
        player = str(player)
        self.playersAvailableList.model().appendRow(QtGui.QStandardItem(player))
        
    def showEvent(self, event):
        if hasattr(self, 'gameStatsBox') and hasattr(self,'gameComboBox') and self.gameComboBox.currentText(): 
            self.gameStatsBox.update(self.gameComboBox.currentText())
        return QtGui.QWidget.showEvent(self, event)
        
