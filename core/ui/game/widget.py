"""Main game-tab widget: score input, clock, player boxes and match controls."""

from __future__ import annotations

import logging
from typing import cast

from PySide6 import QtCore, QtGui
from PySide6.QtCore import QCoreApplication, QFile, QTextStream
from PySide6.QtGui import QColor, QShortcut
from PySide6.QtWidgets import (
    QApplication,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from core.engine.engine import EntryGameEngine, RoundGameEngine
from core.engine.settings import appsettings
from core.ui.game.colours import PlayerColours
from core.ui.game.input import GameInputWidget
from core.ui.game.matchedit import MatchTimesEditDialog
from core.ui.game.player import GamePlayerWidget
from core.ui.game.rounds import GameRoundsDetail
from core.ui.game.utils import SleepBlocker
from core.ui.language import LanguageButton
from core.ui.settings import SettingsDialog
from core.ui.tab import Tab
from core.ui.timers import GameClock

logger = logging.getLogger(__name__)


class GameWidget(Tab):
    """Scoreboard tab: score input, round detail, clock and match controls."""

    QCoreApplication.translate("GameWidget", "Scoreboard")

    # Subclasses set this to an appsettings key (e.g. "qwirkle_dealer_policy")
    # to have the dealer-policy checkbox initialised from and persisted to that key.
    dealer_policy_setting_key: str | None = None
    player_colours: list[QColor] = PlayerColours
    # Set to True in subclasses where colour is tied to position (e.g. Parchis).
    colour_locked: bool = False

    def __init__(
        self,
        game: str,
        players: list[str],
        engine: RoundGameEngine | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.game = game
        if engine is not None:
            self.engine: RoundGameEngine = engine
            self.players = self.engine.getListPlayers()
        else:
            self.players = players
            self.createEngine()
            for nick in players:
                self.engine.addPlayer(nick)
            self.engine.begin()
        self.engine.printStats()
        self.finished = False
        self.hideInputOnFinish = True
        self.colour_map: dict[str, int] = {p: i for i, p in enumerate(self.players)}

        self.screen_blocker = SleepBlocker()
        self.toggleScreenLock()
        self.initUI()

    def initUI(self) -> None:
        """Build the scoreboard layout, buttons, clock and player widgets."""
        self.setStyleSheet("QGroupBox { font-size: 120%; font-weight: bold; }")
        self._base_stylesheet = self.styleSheet()
        self.widgetLayout = QHBoxLayout(self)
        self.leftLayout = QVBoxLayout()
        self.rightLayout = QVBoxLayout()
        self.widgetLayout.addLayout(self.leftLayout)
        self.widgetLayout.addLayout(self.rightLayout)
        self.roundGroup = QGroupBox(self)
        self.leftLayout.addWidget(self.roundGroup)
        self.matchGroup = QGroupBox(self)
        self.matchGroup.setMinimumWidth(220)
        self.rightLayout.addWidget(self.matchGroup)

        # Round Group
        self.roundLayout = QVBoxLayout(self.roundGroup)
        self.buttonGroupLayout = QHBoxLayout()
        self.roundLayout.addLayout(self.buttonGroupLayout)

        self.cancelMatchButton = QPushButton(self.roundGroup)
        self.buttonGroupLayout.addWidget(self.cancelMatchButton, 3)
        self.cancelMatchButton.clicked.connect(self.cancelMatch)

        self.restartMatchButton = QPushButton(self.roundGroup)
        self.buttonGroupLayout.addWidget(self.restartMatchButton, 3)
        self.restartMatchButton.clicked.connect(self.restartMatch)

        self.pauseMatchButton = QPushButton(self.roundGroup)
        self.buttonGroupLayout.addWidget(self.pauseMatchButton, 3)
        self.pauseMatchButton.clicked.connect(self.pauseMatch)

        self.playerOrderButton = QPushButton(self.roundGroup)
        self.buttonGroupLayout.addWidget(self.playerOrderButton, 3)
        self.playerOrderButton.clicked.connect(self.changePlayerOrder)

        self.separator1 = QWidget(self.roundGroup)
        self.buttonGroupLayout.addWidget(self.separator1)

        self.languageButton = LanguageButton(self.roundGroup)
        self.buttonGroupLayout.addWidget(self.languageButton)

        self.settingsButton = QPushButton(self)
        self.settingsButton.setSizePolicy(
            QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Maximum
        )
        self.buttonGroupLayout.addWidget(self.settingsButton)
        self.settingsButton.clicked.connect(self.onSettings)

        self.separator2 = QWidget(self.roundGroup)
        self.buttonGroupLayout.addWidget(self.separator2)

        self.commitRoundButton = QPushButton(self.roundGroup)
        self.buttonGroupLayout.addWidget(self.commitRoundButton, 3)
        self.commitRoundButton.clicked.connect(self.commitRound)

        self.undoButton = QPushButton(self.roundGroup)
        self.buttonGroupLayout.addWidget(self.undoButton, 2)
        self.undoButton.setEnabled(
            self.engine.getNumRound() > 1 and not self.engine.getWinner()
        )
        self.undoButton.clicked.connect(self.undoCommit)

        self.finishButton = QPushButton(self.roundGroup)
        self.buttonGroupLayout.addWidget(self.finishButton, 3)
        self.finishButton.clicked.connect(self.finish)
        self.finishButton.setVisible(self.engine.requiresExplicitFinish())

        self.gameStatusLabel = QLabel(self.roundGroup)
        self.gameStatusLabel.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.roundLayout.addWidget(self.gameStatusLabel)

        # Match Group
        self.matchGroupLayout = QVBoxLayout(self.matchGroup)

        self.roundTitleLabel = QLabel(self)
        self.roundTitleLabel.setSizePolicy(
            QSizePolicy.Policy.Preferred,
            QSizePolicy.Policy.Maximum,
        )
        css = """
        QLabel {
            font-size: 18px;
            font-weight: bold;
            qproperty-alignment: AlignCenter;
        }
        """
        self.roundTitleLabel.setStyleSheet(css)
        self.matchGroupLayout.addWidget(self.roundTitleLabel)

        self.clock = GameClock(self.engine.getGameSeconds(), self)
        self.clock.setMinimumHeight(70)
        self.clock.doubleClicked.connect(self.editGameTime)
        self.clock.setSizePolicy(
            QSizePolicy.Policy.Preferred,
            QSizePolicy.Policy.Maximum,
        )
        self.matchGroupLayout.addWidget(self.clock)

        dpolicy = self.engine.getDealingPolicy()
        if dpolicy not in (self.engine.NoDealer, self.engine.StarterDealer):
            if self.dealer_policy_setting_key is not None:
                from core.engine.settings import appsettings

                saved = appsettings[self.dealer_policy_setting_key]
                if saved is not None:
                    want_winner = bool(saved)
                    self.engine.setDealingPolicy(
                        self.engine.WinnerDealer
                        if want_winner
                        else self.engine.RRDealer
                    )
            self.dealerPolicyCheckBox = QPushButton(self.matchGroup)
            self.dealerPolicyCheckBox.setCheckable(True)
            if self.engine.getDealingPolicy() == self.engine.WinnerDealer:
                self.dealerPolicyCheckBox.setChecked(True)
            else:
                self.dealerPolicyCheckBox.setChecked(False)
            self.dealerPolicyCheckBox.toggled.connect(self.changeDealingPolicy)
            self.dealerPolicyCheckBox.setDisabled(self.engine.getNumRound() > 1)
            self.dealerPolicyCheckBox.setSizePolicy(
                QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Maximum
            )
            self.dealerPolicyCheckBox.setProperty("textStateOnly", True)
            self.matchGroupLayout.addWidget(self.dealerPolicyCheckBox)

        self.gameInput = self.createGameInputWidget(self)
        self._commit_round_connection = False
        self.guardCommitButton()
        self.gameInput.changed.connect(self.guardCommitButton)
        self.focussc = QShortcut(
            QtGui.QKeySequence("Ctrl+A"), self, self.gameInput.setFocus
        )
        self.roundLayout.addWidget(self.gameInput)
        self.detailGroup = self.createRoundsDetail(self)
        self.leftLayout.addWidget(self.detailGroup)
        self.detailGroup.edited.connect(self.updatePanel)

        self.addExtraConfig()
        self.addPlayerWidgets()

        self._connectThemeStylesheet()
        self._applyGameStylesheet()

        QtCore.QTimer.singleShot(500, self.gameInput.setFocus)

    def _gameStyleSlug(self) -> str | None:
        """Package name of the concrete game (e.g. ``skullking``), or None."""
        parts = type(self).__module__.split(".")
        if len(parts) >= 2 and parts[0] == "games":
            return parts[1]
        return None

    def _currentThemeName(self) -> str:
        """Return the effective theme name, defaulting to ``light``."""
        app = QApplication.instance()
        theme_manager = getattr(app, "themeManager", None)
        if theme_manager is not None:
            return str(theme_manager.effective_theme())
        return "light"

    def _loadGameStylesheet(self, slug: str) -> str:
        """Return the game's qss for the current theme, or '' if none ships."""
        theme = self._currentThemeName()
        for candidate in (f":/styles/{slug}.{theme}.qss", f":/styles/{slug}.qss"):
            file = QFile(candidate)
            if file.open(QFile.OpenModeFlag.ReadOnly | QFile.OpenModeFlag.Text):
                text = QTextStream(file).readAll()
                file.close()
                return text
        return ""

    def _connectThemeStylesheet(self) -> None:
        """Re-apply the game stylesheet whenever the theme changes."""
        app = QApplication.instance()
        theme_manager = getattr(app, "themeManager", None)
        if theme_manager is not None:
            theme_manager.themeChanged.connect(self._applyGameStylesheet)

    def _applyGameStylesheet(self, *_args) -> None:
        """Layer the game's stylesheet on top of the widget's base styles."""
        slug = self._gameStyleSlug()
        base = getattr(self, "_base_stylesheet", "")
        if not slug:
            return
        game_qss = self._loadGameStylesheet(slug)
        self.setStyleSheet(f"{base}\n{game_qss}" if game_qss else base)

    def retranslateUI(self) -> None:
        """Refresh all button labels and titles for the current language."""
        self.setRoundTitle()
        if appsettings["text_in_buttons"]:
            self.pauseMatchButton.setText(self.tr("&Pause/Play"))
            self.cancelMatchButton.setText(self.tr("&Leave Match"))
            self.restartMatchButton.setText(self.tr("Restart &Match"))
            if isinstance(self.engine, EntryGameEngine):
                self.commitRoundButton.setText(self.tr("Commit &Entry"))
            else:
                self.commitRoundButton.setText(self.tr("Commit &Round"))
            self.undoButton.setText(self.tr("Rollback"))
            self.playerOrderButton.setText(self.tr("Player &Order"))
            self.finishButton.setText(self.tr("&Finish Game"))
        else:
            self.pauseMatchButton.setText("⏸")
            self.cancelMatchButton.setText("⎋")
            self.restartMatchButton.setText("↻")
            self.commitRoundButton.setText("⏺")
            self.undoButton.setText("⎌")
            self.playerOrderButton.setText("♟↕")
            self.finishButton.setText("⏹")
        self.settingsButton.setText("⚙")
        self.gameInput.retranslateUI()
        if self.engine.getDealingPolicy() not in (
            self.engine.NoDealer,
            self.engine.StarterDealer,
        ):
            self.changeDealingPolicy()
        self.detailGroup.retranslateUI()
        self.updateGameStatusLabel()

    def createGameInputWidget(self, parent: QWidget | None = None) -> GameInputWidget:
        """Build the score-input widget; games override for custom input."""
        return GameInputWidget(self.engine, parent)

    def createRoundsDetail(self, parent: QWidget | None = None) -> GameRoundsDetail:
        """Build the rounds/plot/stats detail panel; games may override."""
        return GameRoundsDetail(self.engine, parent)

    def onSettings(self) -> None:
        """Open the settings dialog and react to changed settings."""
        sd = SettingsDialog(parent=self)
        sd.settingChanged.connect(self.watchSettingChange)
        sd.exec()

    def watchSettingChange(self, name: str, value) -> None:
        """Apply a single changed setting (language, theme, log level, ...)."""
        from core.ui.app import GamelogApplication

        if name == "language":
            self.languageButton.changeLanguage(value)
        elif name == "theme":
            app = QApplication.instance()
            if app:
                cast(GamelogApplication, app).themeManager.set_theme(value)
        elif name == "log_level":
            from core.logging_config import set_log_level

            set_log_level(value)
        else:
            self.retranslateUI()

    def playerColour(self, player: str) -> QColor:
        """Return the colour assigned to ``player`` respecting any custom mapping."""
        idx = self.colour_map.get(player, self.players.index(player))
        return self.player_colours[idx % len(self.player_colours)]

    def orderedColours(self) -> list[QColor]:
        """Return colours in current player order, for plot series assignment."""
        return [self.playerColour(p) for p in self.engine.getListPlayers()]

    def addPlayerWidgets(self) -> None:
        """Create a per-player score box for each player in the match."""
        self.playersLayout = QVBoxLayout()
        self.matchGroupLayout.addLayout(self.playersLayout)
        self.playerGroupBox = {}
        for player in self.players:
            pw = GamePlayerWidget(player, self.playerColour(player), self.matchGroup)
            pw.updateDisplay(self.engine.getScoreFromPlayer(player))
            if player == self.engine.getDealer():
                pw.setDealer()
            self.playersLayout.addWidget(pw)
            self.playerGroupBox[player] = pw

    def addExtraConfig(self) -> None:
        """Hook for subclasses to add extra configuration widgets."""

    def updateGameStatusLabel(self) -> None:
        """Show the winner or paused banner, or clear it when playing."""
        self.gameStatusLabel.setStyleSheet(
            "QLabel { font-size: 16px; font-weight:bold; color: red;}"
        )
        winner = self.engine.getWinner()
        if winner:
            self.gameStatusLabel.setText(self.tr("{} won this match!").format(winner))
        elif self.engine.isPaused():
            self.gameStatusLabel.setText(self.tr("Game is paused"))
        else:
            self.gameStatusLabel.setText(self.tr(""))

    def cancelMatch(self) -> None:
        """Leave the match, offering to save or discard it first."""
        logger.info("User requested to cancel %s match", self.game)
        if not self.isFinished():
            tit = self.tr("Leave Match")
            msg = self.tr("Do you want to save the current {} match?")
            msg = msg.format(self.game)
            ret = QMessageBox.question(
                self,
                tit,
                msg,
                QMessageBox.StandardButton.Yes
                | QMessageBox.StandardButton.No
                | QMessageBox.StandardButton.Cancel,
                QMessageBox.StandardButton.Cancel,
            )

            if ret == QMessageBox.StandardButton.Cancel:
                return
            if ret == QMessageBox.StandardButton.No:
                self.closeMatch()
            else:
                self.saveMatch()

        self.toggleScreenLock(True)
        self.requestClose()

    def restartMatch(self) -> None:
        """Restart the match, offering to save the current one first."""
        logger.info("User requested to restart %s match", self.game)
        if not self.isFinished():
            tit = self.tr("Restart Match")
            msg = self.tr("Do you want to save the current {} match?")
            msg = msg.format(self.game)
            ret = QMessageBox.question(
                self,
                tit,
                msg,
                QMessageBox.StandardButton.Yes
                | QMessageBox.StandardButton.No
                | QMessageBox.StandardButton.Cancel,
                QMessageBox.StandardButton.Cancel,
            )

            if ret == QMessageBox.StandardButton.Cancel:
                return
            if ret == QMessageBox.StandardButton.Yes:
                self.saveMatch()
        self.toggleScreenLock(True)
        self.requestRestart()

    def pauseMatch(self) -> None:
        """Toggle the match between paused and running, updating the UI."""
        logger.debug(
            "%s match %s", self.game, "unpaused" if self.engine.isPaused() else "paused"
        )
        if self.engine.isPaused():
            self.clock.unpauseTimer()
            self.commitRoundButton.setEnabled(self.commitRoundSanityCheck())
            self.gameInput.setEnabled(True)
            self.engine.unpause()
            self.toggleScreenLock()
            if not appsettings["text_in_buttons"]:
                self.pauseMatchButton.setText("⏸")
        else:
            self.clock.pauseTimer()
            self.commitRoundButton.setDisabled(True)
            self.gameInput.setDisabled(True)
            self.engine.pause()
            self.toggleScreenLock(True)
            if not appsettings["text_in_buttons"]:
                self.pauseMatchButton.setText("▶")
        self.updateGameStatusLabel()

    def guardCommitButton(self) -> None:
        """Enable/disable the commit button per the current input validity."""
        if self.commitRoundSanityCheck() and not self.engine.getWinner():
            self.commitRoundButton.setDisabled(False)
            self.gameInput.enterPressed.connect(self.commitRound)
            self._commit_round_connection = True
        else:
            self.commitRoundButton.setDisabled(True)
            if self._commit_round_connection:
                self.gameInput.enterPressed.disconnect(self.commitRound)
                self._commit_round_connection = False

    def commitRoundSanityCheck(self, interactive: bool = False) -> bool:
        """Check a winner and valid scores/extras before committing a round."""
        winner = self.gameInput.getWinner()
        if not winner:
            msg = self.tr("No winner selected")
            if interactive:
                QMessageBox.warning(self, self.game, msg)
            else:
                logger.debug("SANITYCHECK: %s", msg)
            return False
        logger.debug("SANITYCHECK: winner=%s", winner)
        scores = self.gameInput.getScores()
        for player, score in scores.items():
            if not self.checkPlayerScore(player, score):
                msg = self.tr("{} score is not valid").format(player)
                if interactive:
                    QMessageBox.warning(self, self.game, msg)
                else:
                    logger.debug("SANITYCHECK: %s", msg)
                    return False
            extras = self.getPlayerExtraInfo(player)
            if extras is None:
                msg = self.tr("No extras")
                logger.debug("SANITYCHECK: %s", msg)
                return False
        logger.debug("SANITYCHECK: Ready to commit")
        return True

    def commitRound(self) -> None:
        """Record the current round's winner, scores and extras in the engine."""
        if not self.commitRoundSanityCheck(interactive=True):
            return
        nround = self.engine.getNumRound()
        logger.debug("Opening round %s", nround)
        self.engine.openRound(nround)
        winner = self.gameInput.getWinner()
        self.engine.setRoundWinner(winner)
        scores = self.gameInput.getScores()
        for player, score in scores.items():
            extras = self.getPlayerExtraInfo(player)
            self.engine.addRoundInfo(player, score, extras)

        self.unsetDealer()
        self.engine.commitRound()
        self.engine.printStats()
        self.updatePanel()
        if not self.engine.getWinner():
            self.setDealer()
        elif self.hideInputOnFinish:
            self.gameInput.hide()

    def undoCommit(self) -> None:
        """Roll back the last committed round after confirmation."""
        if len(self.engine.getRounds()) == 0:
            return

        title = self.tr("Rollback")
        msg = self.tr("Are you sure you want to undo the last entry?")
        ret = QMessageBox.question(
            self,
            title,
            msg,
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.Yes,
        )
        if ret == QMessageBox.StandardButton.No:
            return
        try:
            self.unsetDealer()
        except KeyError:
            pass
        self.engine.deleteRound(len(self.engine.getRounds()))
        self.updatePanel()
        try:
            self.setDealer()
        except KeyError:
            pass

    def finish(self) -> None:
        """Finish the game explicitly after confirmation."""
        logger.info("User requested to finish %s game", self.game)
        title = self.tr("Finish game")
        msg = self.tr("Are you sure you want to finish the current game?")
        ret = QMessageBox.question(
            self,
            title,
            msg,
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.Yes,
        )

        if ret == QMessageBox.StandardButton.No:
            return
        self.engine.finishGame()  # pyright: ignore[reportAttributeAccessIssue]
        self.updatePanel()

    def changeDealingPolicy(self, *args, **kwargs) -> None:
        """Switch between winner-deals and next-player-deals policies."""
        if self.dealerPolicyCheckBox.isChecked():
            self.dealerPolicyCheckBox.setText(self.tr("Winner deals"))
            self.engine.setDealingPolicy(self.engine.WinnerDealer)
            winner = True
        else:
            self.dealerPolicyCheckBox.setText(self.tr("Next player deals"))
            self.engine.setDealingPolicy(self.engine.RRDealer)
            winner = False
        logger.debug(
            "%s dealer policy changed to %s",
            self.game,
            "winner" if winner else "round-robin",
        )
        if self.dealer_policy_setting_key is not None:
            from core.engine.settings import appsettings

            appsettings.set(self.dealer_policy_setting_key, winner)

    def closeMatch(self) -> None:
        logger.info("Closing (discarding) %s match", self.game)
        self.engine.cancelMatch()

    def saveMatch(self) -> None:
        logger.info("Saving %s match", self.game)
        self.engine.save()

    def checkPlayerScore(
        self, player: str, score: int, extras: dict | None = None
    ) -> bool:
        return score >= 0

    def setRoundTitle(self) -> None:
        """Set the title label to the game name and current round number."""
        game = self.engine.getGame()
        if game is None:
            game = ""
        if isinstance(self.engine, EntryGameEngine) or not hasattr(
            self.engine, "getNumRound"
        ):
            self.roundTitleLabel.setText(game)
        else:
            nround = self.engine.getNumRound()
            self.roundTitleLabel.setText(
                self.tr("{} - Round {}").format(game, str(nround))
            )

    def updatePanel(self) -> None:
        """Refresh scores, detail, dealer and title after a state change."""
        self.updateScores()
        self.gameInput.reset()
        self.undoButton.setEnabled(
            self.engine.getNumRound() > 1 and not self.engine.getWinner()
        )
        dpolicy = self.engine.getDealingPolicy()
        if dpolicy not in (self.engine.NoDealer, self.engine.StarterDealer):
            self.dealerPolicyCheckBox.setDisabled(self.engine.getNumRound() > 1)
        if hasattr(self.detailGroup, "updateRound"):
            self.detailGroup.updateRound()  # pyright: ignore[reportAttributeAccessIssue]
        if self.engine.getWinner():
            self.setWinner()
            if hasattr(self.detailGroup, "updateStats"):
                self.detailGroup.updateStats()  # pyright: ignore[reportAttributeAccessIssue]
        else:
            self.setRoundTitle()
            self.gameInput.setFocus()
        if self.engine.getWinner() and self.engine.requiresExplicitFinish():
            self.finishButton.setDisabled(True)
        self.guardCommitButton()

    def getGameName(self) -> str:
        return self.game

    def isFinished(self) -> bool:
        return self.finished

    def createEngine(self) -> None:
        """Hook for subclasses to build and assign ``self.engine``."""

    def getPlayerExtraInfo(self, player: str) -> dict | None:
        """Return per-player extra info for a round; games override this."""
        return {}

    def unsetDealer(self) -> None:
        """Clear the dealer marker from the current dealer's score box."""
        if not hasattr(self, "playerGroupBox"):
            return
        try:
            self.playerGroupBox[self.engine.getDealer()].unsetDealer()
        except KeyError:
            pass

    def setDealer(self) -> None:
        """Mark the current dealer's score box, if per-player boxes exist."""
        if not hasattr(self, "playerGroupBox"):
            return
        try:
            self.playerGroupBox[self.engine.getDealer()].setDealer()
        except KeyError:
            pass

    def updateScores(self) -> None:
        """Push each player's current total score to their score box."""
        if not hasattr(self, "playerGroupBox"):
            return
        try:
            for player in self.players:
                score = self.engine.getScoreFromPlayer(player)
                self.playerGroupBox[player].updateDisplay(score)
        except KeyError:
            pass

    def setWinner(self) -> None:
        """Lock the board and highlight the winner once the match ends."""
        logger.info("%s match ended — winner: %s", self.game, self.engine.getWinner())
        self.finished = True
        self.pauseMatchButton.setDisabled(True)
        self.clock.stopTimer()
        self.commitRoundButton.setDisabled(True)
        self.playerOrderButton.setDisabled(True)
        self.updateGameStatusLabel()
        self.gameInput.setDisabled(True)
        if self.hideInputOnFinish:
            self.gameInput.hide()
        self.toggleScreenLock(True)
        winner = self.engine.getWinner()
        if hasattr(self, "playerGroupBox"):
            try:
                if winner in self.players:
                    self.playerGroupBox[winner].setWinner()
            except KeyError:
                pass

    def changePlayerOrder(self) -> None:
        """Open the reorder dialog and apply any new order, dealer or colours."""
        from core.ui.player import PlayerOrderDialog

        originaldealer = self.engine.getDealer()
        pod = PlayerOrderDialog(
            self.engine,
            self,
            player_colours=self.player_colours,
            colour_map=self.colour_map,
            colour_locked=self.colour_locked,
        )
        if pod.exec_():
            newdealer = pod.getNewDealer()
            neworder = pod.getNewOrder()
            new_colour_map = pod.getNewColourMap()
            order_changed = self.players != neworder
            colours_changed = new_colour_map != self.colour_map
            if order_changed:
                logger.debug("Player order changed to %s", neworder)
                self.engine.setListPlayers(neworder)
                self.players = neworder
                if self.colour_locked:
                    self.colour_map = {p: i for i, p in enumerate(neworder)}
                    colours_changed = True
            if colours_changed and not self.colour_locked:
                logger.debug("Player colours changed to %s", new_colour_map)
                self.colour_map = new_colour_map
            if order_changed or colours_changed:
                self.updatePlayerOrder()
            if originaldealer != newdealer:
                logger.debug("Dealer changed from %s to %s", originaldealer, newdealer)
                self.unsetDealer()
                self.engine.setDealer(newdealer)  # pyright: ignore[reportArgumentType]
                self.setDealer()

    def updatePlayerOrder(self) -> None:
        """Re-lay the player boxes and detail panel in the new player order."""
        try:
            for player in self.engine.getListPlayers():
                self.playersLayout.removeWidget(self.playerGroupBox[player])

            for player in self.engine.getListPlayers():
                self.playersLayout.addWidget(self.playerGroupBox[player])
                self.playerGroupBox[player].setColour(self.playerColour(player))
        except AttributeError:
            pass
        if hasattr(self.detailGroup, "updateColours"):
            self.detailGroup.updateColours(self.orderedColours())  # pyright: ignore[reportAttributeAccessIssue]
        if hasattr(self.detailGroup, "updatePlayerOrder"):
            self.detailGroup.updatePlayerOrder()  # pyright: ignore[reportAttributeAccessIssue]
        self.gameInput.updatePlayerOrder()

    def toggleScreenLock(self, on: bool = False) -> None:
        """Start/stop the sleep blocker (``on=True`` re-enables the screensaver)."""
        if not on:
            self.screen_blocker.start()
            logger.debug("Enabled screensaver")
        else:
            self.screen_blocker.stop()
            logger.debug("Disabled screensaver")

    def editGameTime(self) -> None:
        """Open the match-times editor once the game has finished."""
        if self.finished:
            mted = MatchTimesEditDialog(self.engine, self)
            mted.exec_()
            self.clock.showTime(self.engine.getGameSeconds())
