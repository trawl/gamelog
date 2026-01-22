#!/usr/bin/env python
# -*- coding: utf-8 -*-

import datetime
from typing import cast

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QAbstractItemView,
    QComboBox,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from controllers.db import db
from controllers.resumeengine import ResumeEngine
from gui.gamestatsfactory import QSFactory
from gui.gamewidgetfactory import GameWidgetFactory
from gui.newplayer import NewPlayerDialog
from gui.playerlist import PlayerList, PlayerListModel
from gui.tab import Tab


class NewGameWidget(Tab):
    def __init__(self, parent=None):
        super(NewGameWidget, self).__init__(parent)
        self._parent = parent
        self.initUI()

    def initUI(self):
        # Setup Layouts
        self.widgetLayout = QHBoxLayout(self)
        self.leftColumnLayout = QVBoxLayout()
        self.rightColumnLayout = QVBoxLayout()
        self.widgetLayout.addLayout(self.leftColumnLayout)
        self.widgetLayout.addLayout(self.rightColumnLayout)

        self.gameStatsBox = None

        # Players GroupBox
        self.playersGroupBox = QGroupBox(self)
        self.rightColumnLayout.addWidget(self.playersGroupBox)
        self.widgetLayout.setStretchFactor(self.rightColumnLayout, 1)
        self.populatePlayersGroupBox()

        # Game GroupBox
        self.gameGroupBox = QGroupBox(self)
        self.leftColumnLayout.addWidget(self.gameGroupBox)
        self.widgetLayout.setStretchFactor(self.leftColumnLayout, 4)
        self.populateGamesGroupBox()

    #        self.retranslateUI()

    def retranslateUI(self):
        self.gameGroupBox.setTitle(self.tr("Games"))
        self.updateGameInfo()
        self.playersGroupBox.setTitle(self.tr("Players"))
        self.availablePlayersGroup.setTitle(self.tr("Available Players"))
        self.newPlayerButton.setText(self.tr("New Player"))
        self.inGameGroup.setTitle(self.tr("Selected Players"))
        self.startGameButton.setText(self.tr("Play!"))
        self.resumeGroup.retranslateUI()
        if self.gameStatsBox:
            self.gameStatsBox.retranslateUI()

    def populateGamesGroupBox(self):
        self.gameGroupBoxLayout = QVBoxLayout(self.gameGroupBox)
        self.gameComboBox = QComboBox(self.gameGroupBox)
        self.gameGroupBoxLayout.addWidget(self.gameComboBox)
        self.gameDescriptionLabel = QLabel(self.gameGroupBox)
        self.resumeGroup = ResumeBox(self._parent)
        self.resumeGroup.restartRequested.connect(self.restartGame)
        #        self.gameRulesBrowser = QTextBrowser(self.gameGroupBox)
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

    def updateGameInfo(self, _foo=0):
        game = str(self.gameComboBox.currentText())
        description = "2 - {} {}\n\n{}".format(
            self.games[game]["maxPlayers"],
            self.tr("players"),
            self.games[game]["description"],
        )
        self.gameDescriptionLabel.setText(description)
        #        self.gameRulesBrowser.setText("{}".format(self.games[game]['rules']))
        #         self.gameStatsBox.update(game)
        if self.gameStatsBox is not None:
            self.gameGroupBoxLayout.removeWidget(self.gameStatsBox)
            # print("UGI deleting")
            self.gameStatsBox.deleteLater()

        self.gameStatsBox = QSFactory.createQS(game, None, self)
        self.gameGroupBoxLayout.addWidget(self.gameStatsBox)
        self.updateStats()
        self.resumeGroup.changeGame(game)

    def updateStats(self):
        if self.gameStatsBox:
            try:
                self.gameStatsBox.updateContent(
                    self.gameComboBox.currentText(),
                    cast(
                        "PlayerListModel", self.playersInGameList.model()
                    ).retrievePlayers(),
                )
            except TypeError:
                # Should not happen, but silently ignore
                pass

    def populatePlayersGroupBox(self):
        self.playersGroupBoxLayout = QVBoxLayout(self.playersGroupBox)
        # Start button
        self.startGameButton = QPushButton(self)
        self.startGameButton.clicked.connect(self.createNewGame)
        self.playersGroupBoxLayout.addWidget(self.startGameButton)
        self.playersGroupBoxLayout.addSpacing(30)

        self.inGameGroup = QGroupBox(self)
        self.playersGroupBoxLayout.addWidget(self.inGameGroup)
        self.inGameGroupLayout = QVBoxLayout(self.inGameGroup)
        self.playersInGameList = PlayerList(None, self.inGameGroup)
        # self.inGameGroup.setMaximumHeight(230)
        self.inGameGroupLayout.addWidget(self.playersInGameList)

        self.availablePlayersGroup = QGroupBox(self)
        self.playersGroupBoxLayout.addWidget(self.availablePlayersGroup)
        self.availablePlayersGroupLayout = QVBoxLayout(self.availablePlayersGroup)
        self.playersAvailableList = PlayerList(None, self.playersGroupBox)
        self.availablePlayersGroupLayout.addWidget(self.playersAvailableList)

        #        self.availablePlayersGroupLayout.addStretch()

        self.playersAvailableList.doubleclickeditem.connect(
            self.playersInGameList.addItem
        )
        self.playersInGameList.doubleclickeditem.connect(
            self.playersAvailableList.addItem
        )
        self.playersInGameList.changed.connect(self.updateStats)

        for p in db.getPlayers():
            if p["favourite"]:
                self.playersInGameList.addItem(p["nick"])
            else:
                self.playersAvailableList.addItem(p["nick"])

        self.playersButtonsLayout = QHBoxLayout()
        self.playersGroupBoxLayout.addLayout(self.playersButtonsLayout)

        self.newPlayerButton = QPushButton(self.playersGroupBox)
        self.newPlayerButton.clicked.connect(self.createNewPlayer)
        self.playersButtonsLayout.addWidget(self.newPlayerButton)

    def createNewGame(self):
        game = str(self.gameComboBox.currentText())
        maxPlayers = self.games[game]["maxPlayers"]
        players = cast(
            "PlayerListModel", self.playersInGameList.model()
        ).retrievePlayers()
        tit = self.tr("New Match")
        if len(players) < 2:
            msg = self.tr("At least 2 players are needed to play")
            QMessageBox.warning(self, tit, msg)
        elif len(players) > maxPlayers:
            msg = self.tr("The maximum number of players is")
            QMessageBox.warning(self, tit, "{} {}".format(msg, maxPlayers))
        else:
            matchTab = GameWidgetFactory.createGameWidget(game, players, self._parent)
            if matchTab:
                matchTab.restartRequested.connect(self.restartGame)
                if self._parent:
                    matchTab.closeRequested.connect(self._parent.removeTab)
                    self._parent.newTab(matchTab, game)
            else:
                QMessageBox.warning(self, tit, self.tr("Widget not implemented"))
                return

    def restartGame(self, gamewidget):
        players = gamewidget.players
        game = gamewidget.game
        if self._parent:
            self._parent.removeTab(gamewidget)
        matchTab = GameWidgetFactory.createGameWidget(game, players, self._parent)
        if matchTab:
            matchTab.restartRequested.connect(self.restartGame)
            if self._parent:
                matchTab.closeRequested.connect(self._parent.removeTab)
                self._parent.newTab(matchTab, game)
        else:
            QMessageBox.warning(self, "Warning", self.tr("Widget not implemented"))
            return

    def createNewPlayer(self):
        npd = NewPlayerDialog(self)
        npd.addedNewPlayer.connect(self.addPlayer)
        npd.exec_()

    def addPlayer(self, player):
        player = str(player)
        cast("PlayerListModel", self.playersAvailableList.model()).addPlayer(player)

    def showEvent(self, event):
        if (
            hasattr(self, "gameStatsBox")
            and hasattr(self, "gameComboBox")
            and self.gameComboBox.currentText()
        ):
            if self.gameStatsBox:
                self.gameStatsBox.updateContent(self.gameComboBox.currentText())
            self.resumeGroup.changeGame(self.gameComboBox.currentText())
        return QWidget.showEvent(self, event)


class ResumeBox(QGroupBox):
    restartRequested = Signal(QWidget)

    def __init__(self, parent):
        super(ResumeBox, self).__init__(parent)
        self.engine = None
        self.game = None
        self._parent = parent
        self.matches = []
        self.initUI()

    def initUI(self):
        self.widgetLayout = QHBoxLayout(self)
        self.savedlist = QListWidget(self)
        self.savedlist.setStyleSheet("""
        QListView {
            background: transparent;
        }
        QListView::viewport {
            background: transparent;
        }
        QListView::item {
            padding: 5px 5px;
        }
        QListView::item:selected {
            background: rgba(255,255,255,100);
            border-radius: 6px;
        }
        """)
        self.savedlist.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.savedlist.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Maximum
        )
        self.savedlist.hide()
        self.widgetLayout.addWidget(self.savedlist)
        self.buttonLayout = QVBoxLayout()
        self.widgetLayout.addLayout(self.buttonLayout)
        self.resumebutton = QPushButton(self)
        self.resumebutton.clicked.connect(self.resumeGame)
        self.resumebutton.hide()
        self.buttonLayout.addWidget(self.resumebutton)
        self.cancelbutton = QPushButton(self)
        self.cancelbutton.clicked.connect(self.deleteGame)
        self.cancelbutton.hide()
        self.buttonLayout.addWidget(self.cancelbutton)
        self.buttonLayout.addStretch()
        self.emptyLabel = QLabel(self)
        self.widgetLayout.addWidget(self.emptyLabel)
        self.retranslateUI()

    def retranslateUI(self):
        self.setTitle(self.tr("Saved Games"))
        self.resumebutton.setText(self.tr("Resume"))
        self.cancelbutton.setText(self.tr("Delete"))
        self.emptyLabel.setText(self.tr("No matches to be resumed"))

    def changeGame(self, game):
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
            for idMatch, candidate in candidates.items():
                self.matches.append(idMatch)
                savedtime = datetime.datetime.strptime(
                    candidate["started"], "%Y-%m-%d %H:%M:%S.%f"
                )
                strtime = savedtime.strftime("%Y-%m-%d %H:%M")
                hours, remainder = divmod(int(candidate["elapsed"]), 3600)
                minutes, _ = divmod(remainder, 60)
                strelapsed = "{0:02}:{1:02}".format(hours, minutes)
                msg = f"{strtime} | {strelapsed} | {', '.join(candidate['players'])}"
                item = QListWidgetItem(msg, self.savedlist)
                self.savedlist.addItem(item)
            self.savedlist.show()
            self.resumebutton.show()
            self.cancelbutton.show()

    def resumeGame(self):
        selected = self.savedlist.selectedIndexes()
        if len(selected) > 0:
            idMatch = self.matches[selected[0].row()]
            gameengine = self.engine
            if self.engine:
                gameengine = self.engine.resume(idMatch)
            matchTab = GameWidgetFactory.resumeGameWidget(
                self.game, gameengine, self._parent
            )
            if matchTab:
                matchTab.restartRequested.connect(self.restartGame)
                if self._parent:
                    matchTab.closeRequested.connect(self._parent.removeTab)
                    self._parent.newTab(matchTab, self.game)

    def restartGame(self, gamewidget):
        self.restartRequested.emit(gamewidget)

    def deleteGame(self):
        selected = self.savedlist.selectedIndexes()
        if len(selected) > 0:
            idMatch = self.matches[selected[0].row()]
            tit = self.tr("Cancel Saved Game")
            msg = self.tr("Are you sure you want to cancel saved game?")
            reply = QMessageBox.question(
                self,
                tit,
                msg,
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No,
            )

            if reply == QMessageBox.StandardButton.No:
                return False
            if self.engine:
                gameengine = self.engine.resume(idMatch)
                if gameengine:
                    gameengine.cancelMatch()
            self.changeGame(self.game)
