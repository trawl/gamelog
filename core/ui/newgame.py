import datetime
from typing import cast

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QAbstractItemView,
    QApplication,
    QComboBox,
    QFrame,
    QGroupBox,
    QHBoxLayout,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from core.engine.db import db
from core.engine.resume import ResumeEngine
from core.engine.settings import appsettings
from core.registry import registry
from core.ui.gamelogapplication import GamelogApplication
from core.ui.languagechooser import LanguageButton
from core.ui.newplayer import NewPlayerDialog
from core.ui.playerlist import PlayerList, PlayerListModel
from core.ui.settings import SettingsDialog
from core.ui.tab import Tab


class NewGameWidget(Tab):
    def __init__(self, parent=None):
        super().__init__(parent)
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
        self.updateGameInfo()
        # self.playersGroupBox.setTitle(self.tr("Players"))
        self.startGameButton.setText("▶")
        self.settingsButton.setText("⚙")
        if appsettings["text_in_buttons"]:
            self.availablePlayersGroup.setTitle(self.tr("Available Players"))
            self.newPlayerButton.setText(self.tr("New Player"))
        else:
            self.availablePlayersGroup.setTitle("♟♟♟...")
            self.newPlayerButton.setText("+")
        self.resumeGroup.retranslateUI()
        if self.gameStatsBox:
            self.gameStatsBox.retranslateUI()

    def populateGamesGroupBox(self):
        self.gameGroupBoxLayout = QVBoxLayout(self.gameGroupBox)
        self.gameNameLayout = QHBoxLayout()
        self.gameGroupBoxLayout.addLayout(self.gameNameLayout)
        self.gameGroupBoxLayout.setStretchFactor(self.gameNameLayout, 1)
        self.gameComboBox = QComboBox(self.gameGroupBox)
        self.gameComboBox.setSizePolicy(
            QSizePolicy.Policy.Preferred, QSizePolicy.Policy.MinimumExpanding
        )

        self.gameComboBox.setStyleSheet("""
            QComboBox {
                font-size: 24px;
                font-weight: bold;
            }
        """)
        # self.gameComboBox.setSizePolicy(
        #     QSizePolicy.Policy.Preferred, QSizePolicy.Policy.MinimumExpanding
        # )
        self.gameNameLayout.addWidget(self.gameComboBox)

        self.settingsGroup = QFrame(self)
        self.settingsGroup.setSizePolicy(
            QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Preferred
        )
        self.gameNameLayout.addWidget(self.settingsGroup)

        self.settingsLayout = QVBoxLayout(self.settingsGroup)
        self.settingsLayout.addStretch()
        self.languageChooser = LanguageButton(self)
        self.languageChooser.setSizePolicy(
            QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Maximum
        )
        self.settingsLayout.addWidget(self.languageChooser)

        self.settingsButton = QPushButton(self)
        self.settingsButton.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
        )
        self.settingsButton.clicked.connect(self.onSettings)
        self.settingsLayout.addWidget(self.settingsButton)
        self.settingsLayout.addStretch()
        self.startGameButton = QPushButton(self)
        self.startGameButton.setSizePolicy(
            QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Preferred
        )
        self.startGameButton.setStyleSheet("""
            QPushButton {
                font-size: 48px;
                font-weight: bold;
            }
            """)
        self.startGameButton.clicked.connect(self.onPlay)
        self.gameNameLayout.addWidget(self.startGameButton)

        # self.gameDescriptionLabel.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.resumeGroup = ResumeBox(self._parent)
        self.resumeGroup.restartRequested.connect(self.restartGame)
        self.resumeGroup.savedGameSelected.connect(self.inGameGroup.setDisabled)
        self.resumeGroup.savedGameSelected.connect(
            self.availablePlayersGroup.setDisabled
        )
        #        self.gameRulesBrowser = QTextBrowser(self.gameGroupBox)
        self.gameGroupBoxLayout.addWidget(self.resumeGroup)
        self.gameGroupBoxLayout.setStretchFactor(self.resumeGroup, 1)
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
        max_players = self.games[game]["maxPlayers"]
        self.playersInGameList.setMaxPlayers(max_players)
        if appsettings["text_in_buttons"]:
            self.inGameGroup.setTitle(
                self.tr("Selected Players (max {})").format(max_players)
            )
        else:
            self.inGameGroup.setTitle(f"{self.games[game]['maxPlayers']} ♟")
        #        self.gameRulesBrowser.setText("{}".format(self.games[game]['rules']))
        #         self.gameStatsBox.update(game)
        if self.gameStatsBox is not None:
            self.gameGroupBoxLayout.removeWidget(self.gameStatsBox)
            # print("UGI deleting")
            self.gameStatsBox.deleteLater()

        self.gameStatsBox = registry.create_quick_stats(game, None, self)
        self.gameGroupBoxLayout.addWidget(self.gameStatsBox)
        self.gameGroupBoxLayout.setStretchFactor(self.gameStatsBox, 10)
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

        self.inGameGroup = QGroupBox(self)
        self.playersGroupBoxLayout.addWidget(self.inGameGroup)
        self.inGameGroupLayout = QVBoxLayout(self.inGameGroup)
        self.playersInGameList = PlayerList(None, self.inGameGroup)
        self.playersInGameList.setMinimumWidth(120)
        # self.inGameGroup.setMaximumHeight(230)
        self.inGameGroupLayout.addWidget(self.playersInGameList)

        self.availablePlayersGroup = QGroupBox(self)
        self.playersGroupBoxLayout.addWidget(self.availablePlayersGroup)
        self.availablePlayersGroupLayout = QVBoxLayout(self.availablePlayersGroup)
        self.playersAvailableList = PlayerList(None, self.playersGroupBox)
        self.playersAvailableList.setMinimumWidth(120)
        self.availablePlayersGroupLayout.addWidget(self.playersAvailableList)

        #        self.availablePlayersGroupLayout.addStretch()

        self.playersAvailableList.setTwinList(self.playersInGameList)
        self.playersInGameList.setTwinList(self.playersAvailableList)
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

    def onPlay(self):
        if self.resumeGroup.getSelectedSavedGame() == 0:
            self.createNewGame()
        else:
            self.resumeGroup.resumeGame()

    def onSettings(self):
        sd = SettingsDialog(parent=self)
        sd.settingChanged.connect(self.watchSettingChange)
        # sd.settingChanged.connect(self.retranslateUI)
        sd.exec()

    def watchSettingChange(self, name, value):
        if name == "language":
            self.languageChooser.changeLanguage(value)
        elif name == "theme":
            app = QApplication.instance()
            if app:
                cast(GamelogApplication, app).themeManager.set_theme(value)
        elif name == "log_level":
            from core.logging_config import set_log_level

            set_log_level(value)
        else:
            self.retranslateUI()

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
            QMessageBox.warning(self, tit, f"{msg} {maxPlayers}")
        else:
            matchTab = registry.create_widget(game, players, None, self._parent)
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
        matchTab = registry.create_widget(game, players, None, self._parent)
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
    savedGameSelected = Signal(bool)

    def __init__(self, parent):
        super().__init__(parent)
        self.engine = None
        self.game = None
        self._parent = parent
        self.matches = []
        self.initUI()

    def initUI(self):
        self.widgetLayout = QHBoxLayout(self)
        self.savedlist = QListWidget(self)
        self.savedlist.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.savedlist.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Maximum
        )
        self.widgetLayout.addWidget(self.savedlist)
        self.savedlist.itemSelectionChanged.connect(self.onSelectionChange)
        self.buttonLayout = QVBoxLayout()
        self.widgetLayout.addLayout(self.buttonLayout)
        # self.resumebutton = QPushButton(self)
        # self.resumebutton.clicked.connect(self.resumeGame)
        # self.resumebutton.hide()
        # self.buttonLayout.addWidget(self.resumebutton)
        # self.buttonLayout.addStretch()
        self.cancelbutton = QPushButton(self)
        self.cancelbutton.setSizePolicy(
            QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Expanding
        )
        self.cancelbutton.clicked.connect(self.deleteGame)
        self.cancelbutton.hide()
        self.buttonLayout.addWidget(self.cancelbutton)
        # self.buttonLayout.addStretch()
        self.retranslateUI()

    def retranslateUI(self):
        # self.setTitle(self.tr("Saved Games"))
        # self.resumebutton.setText(self.tr("Resume"))
        # self.cancelbutton.setText(self.tr("Delete"))
        # self.resumebutton.setText(self.tr("▶"))
        if appsettings["text_in_buttons"]:
            self.cancelbutton.setText(self.tr("Delete"))
        else:
            self.cancelbutton.setText("⌫")

    def changeGame(self, game):
        self.game = game
        self.engine = ResumeEngine(game)
        self.savedlist.clear()
        self.matches = []
        candidates = self.engine.getCandidates()
        if not candidates:
            self.hide()
            # self.resumebutton.hide()
            self.cancelbutton.hide()
        else:
            item = QListWidgetItem(self.tr("Start a new game..."), self.savedlist)
            self.savedlist.addItem(item)
            self.matches.append(0)
            item.setSelected(True)
            for idMatch, candidate in candidates.items():
                self.matches.append(idMatch)
                try:
                    savedtime = (
                        datetime.datetime.strptime(
                            candidate["started"], "%Y-%m-%d %H:%M:%S.%f"
                        )
                        .replace(tzinfo=datetime.UTC)
                        .astimezone()
                    )
                except ValueError:
                    savedtime = datetime.datetime.strptime(
                        candidate["started"], "%Y-%m-%d %H:%M:%S.%f%z"
                    ).astimezone()

                strtime = savedtime.strftime("%Y-%m-%d %H:%M")
                hours, remainder = divmod(int(candidate["elapsed"]), 3600)
                minutes, _ = divmod(remainder, 60)
                strelapsed = f"{hours:02}:{minutes:02}"
                msg = f"{strtime} | {strelapsed} | {', '.join(candidate['players'])}"
                item = QListWidgetItem(msg, self.savedlist)
                self.savedlist.addItem(item)
            self.show()
            # self.resumebutton.show()
            self.cancelbutton.show()

    def getSelectedSavedGame(self):
        selected = self.savedlist.selectedIndexes()
        if not selected:
            return 0
        else:
            return self.savedlist.selectedIndexes()[0].row()

    def onSelectionChange(self):
        is_saved_match_selected = self.getSelectedSavedGame() != 0
        self.cancelbutton.setEnabled(is_saved_match_selected)
        self.savedGameSelected.emit(is_saved_match_selected)

    def resumeGame(self):
        selected = self.savedlist.selectedIndexes()
        if len(selected) > 0:
            idMatch = self.matches[selected[0].row()]
            gameengine = self.engine
            if self.engine:
                gameengine = self.engine.resume(idMatch)
            matchTab = registry.create_widget(self.game, None, gameengine, self._parent)
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
