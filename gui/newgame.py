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
from controllers.resumeengine import ResumeEngine
from gui.tab import Tab
from gui.gamewidgetfactory import GameWidgetFactory
from gui.newplayer import NewPlayerDialog


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
        self.availablePlayersLabel.setText(QtGui.QApplication.translate("NewGameWidget","Available Players"))
        self.newPlayerButton.setText(QtGui.QApplication.translate("NewGameWidget","New Player"))
        self.inGameLabel.setText(QtGui.QApplication.translate("NewGameWidget","Selected Players"))
        self.startGameButton.setText(QtGui.QApplication.translate("NewGameWidget","Play!"))
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
        description = "2 - {} {}\n\n{}".format(self.games[game]['maxPlayers'],QtGui.QApplication.translate("NewGameWidget",'players'),self.games[game]['description'])
        self.gameDescriptionLabel.setText(description)
#        self.gameRulesBrowser.setText("{}".format(self.games[game]['rules']))
        self.gameStatsBox.update(game)
        self.resumeGroup.changeGame(game)

    def populatePlayersGroupBox(self):

        self.playersGroupBoxLayout = QtGui.QVBoxLayout(self.playersGroupBox)
        self.availablePlayersLabel = QtGui.QLabel(self.playersGroupBox)
        self.playersGroupBoxLayout.addWidget(self.availablePlayersLabel)
        self.playersAvailableList = PlayerList(self.playersGroupBox)
        self.playersGroupBoxLayout.addWidget(self.playersAvailableList)

        for nick in db.getPlayerNicks():
            self.playersAvailableList.model().appendRow(QtGui.QStandardItem(nick))

        self.playersButtonsLayout = QtGui.QHBoxLayout()
        self.playersGroupBoxLayout.addLayout(self.playersButtonsLayout)

        self.newPlayerButton = QtGui.QPushButton(self.playersGroupBox)
        self.newPlayerButton.clicked.connect(self.createNewPlayer)
        self.playersButtonsLayout.addWidget( self.newPlayerButton)


        self.inGameLabel = QtGui.QLabel(self.playersGroupBox)
        self.playersGroupBoxLayout.addWidget(self.inGameLabel)
        self.playersInGameList = PlayerList(self.playersGroupBox)
        self.playersGroupBoxLayout.addWidget(self.playersInGameList)
        
        #Start button
        self.startGameButton = QtGui.QPushButton(self)
        self.startGameButton.clicked.connect(self.createNewGame)
        self.playersGroupBoxLayout.addWidget(self.startGameButton)

    def createNewGame(self):
        game = str(self.gameComboBox.currentText())
        maxPlayers = self.games[game]['maxPlayers']
        players = self.playersInGameList.model().retrievePlayers()
        if len(players)<2:
            QtGui.QMessageBox.warning(self,QtGui.QApplication.translate("NewGameWidget","New Match"),QtGui.QApplication.translate("NewGameWidget","At least 2 players are needed to play"))
        elif len(players)>maxPlayers:
            QtGui.QMessageBox.warning(self,QtGui.QApplication.translate("NewGameWidget","New Match"),unicode("{} {}".format(QtGui.QApplication.translate("NewGameWidget",'The maximum number of players is'), maxPlayers)))
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
        self.playersAvailableList.model().appendRow(QtGui.QStandardItem(player))
        
    def showEvent(self, event):
        if hasattr(self, 'gameStatsBox') and hasattr(self,'gameComboBox') and self.gameComboBox.currentText(): 
            self.gameStatsBox.update(self.gameComboBox.currentText())
            self.resumeGroup.changeGame(self.gameComboBox.currentText())
        return QtGui.QWidget.showEvent(self, event)


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
        self.resumebutton = QtGui.QPushButton(self)
        self.resumebutton.clicked.connect(self.resumeGame)
        self.resumebutton.hide()
        self.widgetLayout.addWidget(self.resumebutton)
        self.emptyLabel = QtGui.QLabel(self)
        self.widgetLayout.addWidget(self.emptyLabel)
        self.retranslateUI()
        
    def retranslateUI(self):
        self.setTitle(QtGui.QApplication.translate("ResumeBox",'Saved Games'))
        self.resumebutton.setText(QtGui.QApplication.translate("ResumeBox",'Resume'))
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
            self.emptyLabel.show()
        else:
            self.emptyLabel.hide()
            for idMatch,candidate in candidates.items():
                self.matches.append(idMatch)
                msg = "{} {} ({})".format(game,candidate['finished'],candidate['elapsed'])
                item = QtGui.QListWidgetItem(msg,self.savedlist)
#                item.setStatusTip("Players: {}".format(candidates['players']))
                self.savedlist.addItem(item)
            self.savedlist.show()
            self.resumebutton.show()
                
    def resumeGame(self):
        selected = self.savedlist.selectedIndexes()
        if len(selected)>0:
            idMatch = self.matches[selected[0].row()]
            gameengine = self.engine.resume(idMatch)
            matchTab = GameWidgetFactory.resumeGameWidget(self.game,gameengine,self.parent)
            if matchTab:
                matchTab.closeRequested.connect(self.parent.removeTab)
                self.parent.newTab(matchTab,self.game)
            
class QuickStatsBox(QtGui.QGroupBox):
    
    def __init__(self,parent):
        super(QuickStatsBox, self).__init__(parent)
        self.stats = StatsEngine()
        self.game = None
        self.initUI()

        sp = QtGui.QSizePolicy(QtGui.QSizePolicy.Preferred,QtGui.QSizePolicy.Expanding)
        self.setSizePolicy(sp)
        
    def initUI(self):
        self.widgetLayout = QtGui.QVBoxLayout(self)
        self.gameStatsLabel = QtGui.QLabel(self)
        self.widgetLayout.addWidget(self.gameStatsLabel)
        self.matchStatsTitleLabel = QtGui.QLabel(self)
        self.widgetLayout.addWidget(self.matchStatsTitleLabel)

        self.matchStatsTable = QtGui.QTableWidget(self)
        self.matchStatsTable.setMinimumSize(0, 10)
        self.widgetLayout.addWidget(self.matchStatsTable)
        self.playerStatsTitleLabel = QtGui.QLabel(self)
        self.widgetLayout.addWidget(self.playerStatsTitleLabel)
        self.playerStatsTable = QtGui.QTableWidget(self)
        self.widgetLayout.addWidget(self.playerStatsTable)
        self.retranslateUI()
        
    def retranslateUI(self):
        self.gameStatsText = unicode(QtGui.QApplication.translate("QuickStatsBox",'Last winner') + ": {} ({})")
        self.setTitle(QtGui.QApplication.translate("QuickStatsBox",'Statistics'))
        self.matchStatsTitleLabel.setText(QtGui.QApplication.translate("QuickStatsBox","Matches"))
        self.playerStatsTitleLabel.setText(QtGui.QApplication.translate("QuickStatsBox","Players"))
        self.update()
        
    def update(self,game=None):
        if game is not None: self.game = game
        self.stats.update()
        gamestats = self.stats.getGameStats(self.game)
        matchstats = self.stats.getMatchGameStats(self.game)
        playerstats = self.stats.getPlayerGameStats(self.game)
        
        if not gamestats:
            self.gameStatsLabel.setText(QtGui.QApplication.translate("QuickStatsBox","No statistics found"))
            self.playerStatsTitleLabel.hide()
            self.matchStatsTitleLabel.hide()
        else:
            self.gameStatsLabel.setText(self.gameStatsText.format(gamestats['lastwinner'],gamestats['lastwinnerdate']))
            self.playerStatsTitleLabel.show()
            self.matchStatsTitleLabel.show()
        keys = ['maxduration','minduration','avgduration','maxscore','minscore','avgscore']
        headers = [QtGui.QApplication.translate("QuickStatsBox",'Longest'),QtGui.QApplication.translate("QuickStatsBox",'Shortest'),QtGui.QApplication.translate("QuickStatsBox",'Average'),QtGui.QApplication.translate("QuickStatsBox",'Highest'),QtGui.QApplication.translate("QuickStatsBox",'Lowest'),QtGui.QApplication.translate("QuickStatsBox",'Average')]
        self.updateTable(self.matchStatsTable, matchstats, keys, 'nplayers', headers)
            
        keys = ['played','victories','victoryp','maxscore','minscore','avgscore','sumscore']
        headers = [QtGui.QApplication.translate("QuickStatsBox",'Played'),QtGui.QApplication.translate("QuickStatsBox",'Victories'),QtGui.QApplication.translate("QuickStatsBox",'Ratio (%)'),QtGui.QApplication.translate("QuickStatsBox",'Highest'),QtGui.QApplication.translate("QuickStatsBox",'Lowest'),QtGui.QApplication.translate("QuickStatsBox",'Average'),QtGui.QApplication.translate("QuickStatsBox",'Total')]
        self.updateTable(self.playerStatsTable, playerstats, keys, 'nick', headers)
                            

    def updateTable(self,table,contents,keyorder,rowheaderkey,cheaders):
        table.clear()
        if len(contents) and len(contents[0])>1:
            table.show()
            displayed = contents[:4]
            table.setRowCount(len(displayed))
            table.setColumnCount(len(displayed[0])-2)
            table.setHorizontalHeaderLabels(cheaders)
            table.setVerticalHeaderLabels([ str(row[rowheaderkey]) for row in displayed])
            

            for i, row in enumerate(displayed):
                keys = keyorder
                for j, key in enumerate(keys):
                    item = QtGui.QTableWidgetItem(str(row[key]))
                    item.setTextAlignment(QtCore.Qt.AlignVCenter|QtCore.Qt.AlignHCenter)
                    item.setFlags(item.flags()^QtCore.Qt.ItemIsEditable)
                    table.setItem(i,j,item)
                    
            table.horizontalHeader().setResizeMode(QtGui.QHeaderView.Stretch)
            size = table.rowHeight(0)*(len(displayed)+1)+(len(displayed)+1)*2
            table.setFixedHeight(size)      
        else:
            table.hide()
