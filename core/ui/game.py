"""Qt scoreboard widgets: the game tab, score input, plots and helper widgets."""

from __future__ import annotations

import ctypes
import logging
import shutil
import subprocess
import sys
from typing import cast

from PySide6 import QtCore, QtGui
from PySide6.QtCore import (
    QCoreApplication,
    QEasingCurve,
    QEvent,
    QFile,
    QObject,
    QPropertyAnimation,
    QRectF,
    QSize,
    QTextStream,
)
from PySide6.QtGui import (
    QAction,
    QColor,
    QFont,
    QImage,
    QKeyEvent,
    QMouseEvent,
    QPainter,
    QPainterPath,
    QPaintEvent,
    QShortcut,
    QWheelEvent,
)
from PySide6.QtSvg import QSvgRenderer
from PySide6.QtWidgets import (
    QApplication,
    QFrame,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLCDNumber,
    QLineEdit,
    QMenu,
    QMessageBox,
    QPushButton,
    QSizePolicy,
    QStackedLayout,
    QTableWidget,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from core.engine.base import EntryGameEngine, RoundGameEngine
from core.engine.settings import appsettings
from core.model.base import GenericRound
from core.ui.clock import GameClock
from core.ui.gamelogapplication import GamelogApplication
from core.ui.gamestats import QuickStatsTW
from core.ui.languagechooser import LanguageButton
from core.ui.matchedit import MatchTimesEditDialog
from core.ui.playerlist import PlayerOrderDialog
from core.ui.plots import PlotView
from core.ui.settings import SettingsDialog
from core.ui.tab import Tab

# i18n = QApplication.translate

logger = logging.getLogger(__name__)

PlayerColours = [
    QtGui.QColor(237, 44, 48),
    #  QtGui.QColor(23, 89, 169),
    QtGui.QColor(123, 164, 218),
    QtGui.QColor(0, 140, 70),
    QtGui.QColor(243, 124, 33),
    QtGui.QColor(147, 112, 219),
    #  QtGui.QColor(101, 43, 145),
    #  QtGui.QColor(161, 29, 33),
    QtGui.QColor(255, 0, 255),
    QtGui.QColor(0, 200, 200),  # Cyan / Teal
    QtGui.QColor(255, 215, 0),  # Gold / Yellow
    QtGui.QColor(0, 255, 127),  # Spring Green
    QtGui.QColor(255, 105, 180),  # Hot Pink
    QtGui.QColor(173, 216, 230),  # Light Blue
    QtGui.QColor(255, 165, 79),  # Light Orange
]


class GameWidget(Tab):
    """Scoreboard tab: score input, round detail, clock and match controls."""

    QCoreApplication.translate("GameWidget", "Scoreboard")

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

        self.screen_blocker = SleepBlocker()
        self.toggleScreenLock()
        self.initUI()

    def initUI(self) -> None:
        """Build the scoreboard layout, buttons, clock and player widgets."""
        # Set up the main grid
        self.setStyleSheet("QGroupBox { font-size: 120%; font-weight: bold; }")
        self._base_stylesheet = self.styleSheet()
        # self.widgetLayout = QGridLayout(self)
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
        # self.commitRoundButton.setMinimumWidth(64)
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
        # self.gameStatusLabel.hide()
        self.roundLayout.addWidget(self.gameStatusLabel)

        # Match Group
        # self.matchGroup.setTitle(self.tr("Game Time"))
        self.matchGroupLayout = QVBoxLayout(self.matchGroup)

        self.roundTitleLabel = QLabel(self)
        self.roundTitleLabel.setSizePolicy(
            QSizePolicy.Policy.Preferred,  # horizontal
            QSizePolicy.Policy.Maximum,  # vertical
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
        # self.clock.setMinimumWidth(200)
        self.clock.setSizePolicy(
            QSizePolicy.Policy.Preferred,  # horizontal
            QSizePolicy.Policy.Maximum,  # vertical
        )
        # Set size policy to Fixed in the vertical direction
        # size_policy = self.matchGroup.sizePolicy()
        # size_policy.setVerticalPolicy(QSizePolicy.Policy.Fixed)
        # self.matchGroup.setSizePolicy(size_policy)
        self.matchGroupLayout.addWidget(self.clock)

        dpolicy = self.engine.getDealingPolicy()
        if dpolicy not in (self.engine.NoDealer, self.engine.StarterDealer):
            # self.dealerPolicyCheckBox = QCheckBox(self.matchGroup)
            self.dealerPolicyCheckBox = QPushButton(self.matchGroup)
            self.dealerPolicyCheckBox.setCheckable(True)
            if self.engine.getDealingPolicy() == self.engine.WinnerDealer:
                self.dealerPolicyCheckBox.setChecked(True)
            else:
                self.dealerPolicyCheckBox.setChecked(False)
            # self.dealerPolicyCheckBox.stateChanged.connect(self.changeDealingPolicy)
            self.dealerPolicyCheckBox.toggled.connect(self.changeDealingPolicy)
            self.dealerPolicyCheckBox.setDisabled(self.engine.getNumRound() > 1)
            # self.dealerPolicyCheckBox.setSizePolicy(
            #     QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed
            # )
            self.dealerPolicyCheckBox.setSizePolicy(
                QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Maximum
            )
            self.dealerPolicyCheckBox.setProperty("textStateOnly", True)

            # self.dealerPolicyCheckBox.setStyleSheet("""
            #     QPushButton {
            #         border: 2px solid #888;
            #         border-radius: 6px;
            #         padding: 6px 6px;
            #         background: transparent;
            #         color: white;
            #     }

            #     /* Checked (enabled) */
            #     QPushButton:checked:enabled {
            #         background: #888;
            #     }

            #     /* Unchecked (enabled) */
            #     QPushButton:!checked:enabled {
            #         background: transparent;
            #     }

            #     /* Disabled but checked */
            #     QPushButton:checked:disabled {
            #         background: #666;
            #         border-color: #666;
            #     }

            #     /* Disabled and unchecked */
            #     QPushButton:disabled:!checked {
            #         border-color: #555;
            #     }
            #     """)
            self.matchGroupLayout.addWidget(
                self.dealerPolicyCheckBox,
                # alignment=QtCore.Qt.AlignmentFlag.AlignHCenter,
            )
        self.gameInput = self.createGameInputWidget(self)
        self._commit_round_connection = False
        self.guardCommitButton()
        self.gameInput.changed.connect(self.guardCommitButton)
        self.focussc = QShortcut(
            QtGui.QKeySequence("Ctrl+A"), self, self.gameInput.setFocus
        )
        self.roundLayout.addWidget(self.gameInput)
        self.detailGroup = self.createRoundsDetail(self)
        # self.widgetLayout.addWidget(self.detailGroup, 1, 0)
        self.leftLayout.addWidget(self.detailGroup)
        self.detailGroup.edited.connect(self.updatePanel)

        self.addExtraConfig()
        self.addPlayerWidgets()

        self._connectThemeStylesheet()
        self._applyGameStylesheet()

        QtCore.QTimer.singleShot(500, self.gameInput.setFocus)

    def _gameStyleSlug(self) -> str | None:
        """Package name of the concrete game (e.g. ``skullking``), or None.

        Derived from the widget's module so a game needs no extra metadata:
        ``games.skullking.widget`` -> ``skullking``.  The generic base widget
        (``core.ui.game``) has no game slug and gets no per-game stylesheet.
        """
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
        """Return the game's qss for the current theme, or '' if none ships.

        Prefers a theme-specific ``<slug>.<theme>.qss`` and falls back to a
        theme-agnostic ``<slug>.qss``.
        """
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
        """Layer the game's stylesheet on top of the widget's base styles.

        Scoped to this game widget (and its children), so it augments the
        global theme without affecting other open game tabs.  Re-applied on
        theme changes.
        """
        slug = self._gameStyleSlug()
        base = getattr(self, "_base_stylesheet", "")
        if not slug:
            return
        game_qss = self._loadGameStylesheet(slug)
        self.setStyleSheet(f"{base}\n{game_qss}" if game_qss else base)

    def retranslateUI(self) -> None:
        """Refresh all button labels and titles for the current language."""
        self.setRoundTitle()
        # self.matchGroup.setTitle(self.tr("Game Time"))
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
        # sd.settingChanged.connect(self.retranslateUI)
        sd.exec()

    def watchSettingChange(self, name: str, value) -> None:
        """Apply a single changed setting (language, theme, log level, ...)."""
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

    def addPlayerWidgets(self) -> None:
        """Create a per-player score box for each player in the match."""
        self.playersLayout = QVBoxLayout()
        self.matchGroupLayout.addLayout(self.playersLayout)
        self.playerGroupBox = {}
        for i, player in enumerate(self.players):
            pw = GamePlayerWidget(player, PlayerColours[i], self.matchGroup)
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
            # self.gameStatusLabel.show()
            self.gameStatusLabel.setText(self.tr("{} won this match!").format(winner))
        elif self.engine.isPaused():
            self.gameStatusLabel.setText(self.tr("Game is paused"))
            # self.gameStatusLabel.show()
        else:
            self.gameStatusLabel.setText(self.tr(""))
            # self.gameStatusLabel.hide()

    def cancelMatch(self) -> None:
        """Leave the match, offering to save or discard it first."""
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

        # Everything ok so far, let's confirm
        # tit = self.tr('Commit Round')
        # msg = i18n(
        #     "GameWidget", "Are you sure you want to commit the current round?")
        # ret = QMessageBox.question(self, tit, msg,
        #                            QMessageBox.Yes | QMessageBox.No,
        #                            QMessageBox.Yes)

        # if ret == QMessageBox.No:
        #     return

        # Once here, we can commit round
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
        # finishGame() exists only on EntryGameEngine; the finish button is
        # shown only for engines that require an explicit finish.
        self.engine.finishGame()  # pyright: ignore[reportAttributeAccessIssue]
        self.updatePanel()

    def changeDealingPolicy(self, *args, **kwargs) -> None:
        """Switch between winner-deals and next-player-deals policies."""
        if self.dealerPolicyCheckBox.isChecked():
            self.dealerPolicyCheckBox.setText(self.tr("Winner deals"))
            self.engine.setDealingPolicy(self.engine.WinnerDealer)
        else:
            self.dealerPolicyCheckBox.setText(self.tr("Next player deals"))
            self.engine.setDealingPolicy(self.engine.RRDealer)

    def closeMatch(self) -> None:
        self.engine.cancelMatch()

    def saveMatch(self) -> None:
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
            # updateStats is optional on the detail widget; call it only when
            # present so a real error inside it is not silently swallowed.
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

    # To be implemented in subclasses
    def createEngine(self) -> None:
        """Hook for subclasses to build and assign ``self.engine``."""

    def getPlayerExtraInfo(self, player: str) -> dict | None:
        """Return per-player extra info for a round; games override this."""
        return {}

    def unsetDealer(self) -> None:
        """Clear the dealer marker from the current dealer's score box."""
        # Some widgets (e.g. Phase10) don't use per-player boxes.
        if not hasattr(self, "playerGroupBox"):
            return
        # KeyError: there may be no current dealer (e.g. dealer-less games).
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
        """Open the reorder dialog and apply any new order or dealer."""
        originaldealer = self.engine.getDealer()
        pod = PlayerOrderDialog(self.engine, self)
        #         pod.dealerChanged.connect(self.changedDealer)
        if pod.exec_():
            newdealer = pod.getNewDealer()
            neworder = pod.getNewOrder()
            if self.players != neworder:
                # Do something
                self.engine.setListPlayers(neworder)
                self.players = neworder
                self.updatePlayerOrder()
            if originaldealer != newdealer:
                self.unsetDealer()
                # getNewDealer() may return None; setDealer ignores unknown players.
                self.engine.setDealer(newdealer)  # pyright: ignore[reportArgumentType]
                self.setDealer()

    def updatePlayerOrder(self) -> None:
        """Re-lay the player boxes and detail panel in the new player order."""
        try:
            for player in self.engine.getListPlayers():
                self.playersLayout.removeWidget(self.playerGroupBox[player])

            for i, player in enumerate(self.engine.getListPlayers()):
                self.playersLayout.addWidget(self.playerGroupBox[player])
                self.playerGroupBox[player].setColour(PlayerColours[i])
        except AttributeError:
            pass
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


class GameInputWidget(QWidget):
    """Base score-input widget; games subclass it for their own controls."""

    enterPressed = QtCore.Signal()
    changed = QtCore.Signal()

    def __init__(self, engine: RoundGameEngine, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.engine = engine
        self.winnerSelected = ""
        self.playerInputList: dict = {}
        self.initUI()

    def initUI(self) -> None:
        """Build the input controls; overridden by concrete games."""

    def retranslateUI(self) -> None:
        """Refresh input labels for the current language; overridden."""

    def getWinner(self) -> str:
        """Return the player with the highest current input score."""
        maxScore = -1000000
        for player, score in self.getScores().items():
            if score > maxScore:
                maxScore = score
                self.winnerSelected = player
        return self.winnerSelected

    def getScores(self) -> dict[str, int]:
        """Return the current per-player score map from the input widgets."""
        scores = {}
        for player, piw in self.playerInputList.items():
            scores[player] = piw.getScore()
        return scores

    def reset(self) -> None:
        """Clear the selected winner and reset every player's input."""
        self.winnerSelected = ""
        for piw in self.playerInputList.values():
            piw.reset()

    def changedWinner(self, winner: str) -> None:
        """Record a newly selected winner, resetting the previous one."""
        logger.debug("Changing winner to %s", winner)
        winner = str(winner)
        if self.winnerSelected != "":
            self.playerInputList[self.winnerSelected].reset()
        self.winnerSelected = winner

    def keyPressEvent(self, event: QKeyEvent) -> None:
        if event.key() in (QtCore.Qt.Key.Key_Return, QtCore.Qt.Key.Key_Enter):
            self.enterPressed.emit()
            event.accept()
        return super().keyPressEvent(event)

    def mousePressEvent(self, event: QMouseEvent) -> None:
        self.setFocus()
        return super().mousePressEvent(event)

    def updatePlayerOrder(self) -> None:
        """Rebuild the input controls in the new player order; overridden."""


class GamePlayerWidget(QGroupBox):
    """Per-player score box with an LCD readout and dealer/winner overlay."""

    def __init__(
        self, nick: str, colour: QColor | None = None, parent: QWidget | None = None
    ) -> None:
        if not colour:
            colour = QtGui.QColor()
        super().__init__(parent)
        self.player = nick
        self.pcolour = colour
        self.initUI()

    def initUI(self) -> None:
        """Build the LCD score display and load the overlay pixmaps."""
        self.setTitle(self.player)
        #        self.setMinimumWidth(300)
        self.mainLayout = QHBoxLayout(self)
        #         self.mainLayout.addStretch()
        self.scoreLCD = QLCDNumber(self)
        self.scoreLCD.setSegmentStyle(QLCDNumber.SegmentStyle.Flat)
        self.scoreLCD.setFrameStyle(QFrame.Shape.NoFrame)
        self.mainLayout.addWidget(self.scoreLCD)
        self.scoreLCD.setDigitCount(3)
        # self.scoreLCD.setFixedSize(75, 45)
        # self.scoreLCD.setMaximumHeight(60)
        # self.scoreLCD.setMinimumHeight(30)
        self.scoreLCD.setMinimumWidth(50)
        self.scoreLCD.display(0)
        self.title_size = 28
        self.css = """
            QGroupBox {{ font-size: {3}px; font-weight: bold; color:rgb({0},{1},{2});}}

            QGroupBox[ko="true"] {{
                color: rgba({0},{1},{2},70);   /* lower alpha */
            }}

            QGroupBox::title {{
                subcontrol-origin: margin;
                subcontrol-position: top center;
                padding: 0 {4}px;
                background-color: transparent;
            }}
            QGroupBox QLCDNumber {{ color:rgb({0},{1},{2});}}
        """
        self.setColour(self.pcolour)

        self.dealerPixmap = QtGui.QPixmap(":/icons/cards.png")
        self.nonDealerPixmap = QtGui.QPixmap()
        self.winnerPixmap = QtGui.QPixmap(":/icons/winner.png")

        self.background = None
        self.bg_opacity = 1
        self.bg_size = 40
        self.unsetDealer()

    def updateDisplay(self, points: int) -> None:
        """Display ``points``, widening the LCD for 4-digit values."""
        if points >= 1000 or points <= -100:
            self.scoreLCD.setDigitCount(4)
        else:
            self.scoreLCD.setDigitCount(3)
        self.scoreLCD.display(points)

    def setDealer(self) -> None:
        self.background = self.dealerPixmap
        self.update()

    def unsetDealer(self) -> None:
        self.background = None
        self.update()

    def setWinner(self) -> None:
        self.background = self.winnerPixmap
        self.update()

    def setColour(self, colour: QColor | None = None) -> None:
        """Recolour the box (title, LCD and dimmed-out state)."""
        if colour:
            self.pcolour = colour
        self.setStyleSheet(
            self.css.format(
                self.pcolour.red(),
                self.pcolour.green(),
                self.pcolour.blue(),
                self.title_size,
                self.title_size,
            )
        )

    def paintEvent(self, event: QPaintEvent) -> None:
        super().paintEvent(event)
        if not self.background:
            return
        painter = QPainter(self)
        painter.setOpacity(self.bg_opacity)

        scaled = self.background.scaled(
            max(self.bg_size, min(self.height() // 4, self.width() // 4)),
            max(self.bg_size, min(self.height() // 4, self.width() // 4)),
            QtCore.Qt.AspectRatioMode.KeepAspectRatio,
            QtCore.Qt.TransformationMode.SmoothTransformation,
        )

        # x = (self.width() - scaled.width()) // 2
        painter.drawPixmap(0, 0, scaled)


class GameRoundsDetail(QTabWidget):
    """Tabbed detail panel: rounds table, score plot and quick statistics."""

    edited = QtCore.Signal()

    def __init__(self, engine: RoundGameEngine, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.engine = engine
        self.initUI()

    def initUI(self) -> None:
        """Build the table, plot and statistics tabs."""
        self.setStyleSheet("QGroupBox { font-size: 18px; font-weight: bold; }")
        self.widgetLayout = QVBoxLayout(self)

        self.tableContainer = QFrame(self)
        self.tableContainerLayout = QVBoxLayout(self.tableContainer)
        # self.tableContainer.setAutoFillBackground(True)
        self.addTab(self.tableContainer, "")

        self.table = self.createRoundTable(self.engine, self)
        self.tableContainerLayout.addWidget(self.table, stretch=1)
        self.table.edited.connect(self.updateRound)
        self.table.edited.connect(self.edited.emit)

        self.plot = self.createRoundPlot(self.engine, self)
        # self.plot.setAutoFillBackground(True)
        self.addTab(self.plot, "")

        self.gamestats = self.createQSBox()
        self.addTab(self.gamestats, "")

    def retranslateUI(self) -> None:
        """Refresh tab labels and child widgets for the current language."""
        # self.setTitle(i18n("GameRoundsDetail",'Details'))
        if appsettings["text_in_buttons"]:
            self.setTabText(self.indexOf(self.tableContainer), self.tr("Table"))
            self.setTabText(self.indexOf(self.plot), self.tr("Plot"))
            self.setTabText(self.indexOf(self.gamestats), self.tr("Statistics"))
        else:
            self.setTabText(self.indexOf(self.tableContainer), "☷")
            self.setTabText(self.indexOf(self.plot), "∿")
            self.setTabText(self.indexOf(self.gamestats), "σ")
        self.gamestats.retranslateUI()
        self.plot.retranslateUI()
        self.updateRound()
        # self.updateStats()

    def updatePlot(self) -> None:
        self.plot.updatePlot()

    def updateRound(self) -> None:
        """Rebuild the rounds table from the engine and refresh the plot."""
        self.table.resetClear()
        for r in self.engine.getRounds():
            self.table.insertRound(r)
        self.updatePlot()

    def updateStats(self) -> None:
        """Refresh the quick-stats tab, never letting a failure crash the board."""
        try:
            self.gamestats.updateContent(
                self.engine.getGame(), self.engine.getListPlayers()
            )
        except Exception:
            # Defensive: a stats refresh must never take down the board.
            logger.warning("Stats update failed", exc_info=True)
            self.gamestats.update()

    def deleteRound(self, _nround: int) -> None:
        self.plot.updatePlot()

    # Implement in subclasses if necessary
    def createRoundTable(
        self, _engine: RoundGameEngine, parent: QWidget | None
    ) -> GameRoundTable:
        """Build the rounds table widget; games override for their columns."""
        return GameRoundTable(self, parent)

    def createRoundPlot(
        self, _engine: RoundGameEngine, parent: QWidget | None
    ) -> GameRoundPlot:
        """Build the score-plot widget; games override for their plots."""
        return GameRoundPlot(self, parent)

    def createQSBox(self) -> QuickStatsTW:
        """Build the quick-statistics tab for this game and its players."""
        # getGame() is typed str | None; a live engine always has a game name.
        return QuickStatsTW(
            self.engine.getGame(),  # pyright: ignore[reportArgumentType]
            self.engine.getListPlayers(),
            self,
        )

    def updatePlayerOrder(self) -> None:
        self.updateRound()


class GameRoundTable(QTableWidget):
    """Base rounds table: one column per player; games fill in the rows."""

    edited = QtCore.Signal()

    def __init__(self, engine, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.engine = engine
        self.setColumnCount(len(self.engine.getListPlayers()))
        self.initUI()

    def initUI(self) -> None:
        """Set up the header labels and custom context menu."""
        self.setHorizontalHeaderLabels(self.engine.getListPlayers())
        self.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.setContextMenuPolicy(QtCore.Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self.openTableMenu)

    def resetClear(self) -> None:
        """Clear all rows and reset the header to the current player order."""
        self.setHorizontalHeaderLabels(self.engine.getListPlayers())
        self.clearContents()
        self.setRowCount(0)

    def openTableMenu(self, position: QtCore.QPoint) -> None:
        """Show the right-click menu to delete the entry at ``position``."""
        item = self.indexAt(position)
        nentry = item.row() + 1
        if nentry <= 0 or self.engine.getWinner():
            return

        menu = QMenu()
        ic = QtGui.QIcon(":/icons/delete.png")
        msg = self.tr("Delete Entry")
        deleteEntryAction = QAction(ic, msg, self)
        menu.addAction(deleteEntryAction)
        action = menu.exec_(self.mapToGlobal(position))
        if action == deleteEntryAction:
            title = self.tr("Delete Entry")
            msg = self.tr("Are you sure you want to delete this entry?")
            ret = QMessageBox.question(
                self,
                title,
                msg,
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.Yes,
            )
            if ret == QMessageBox.StandardButton.No:
                return
            self.engine.deleteRound(nentry)
            self.removeRow(item.row())
            self.edited.emit()

    # ReImplement in subclasses
    def insertRound(self, _rnd: GenericRound) -> None:
        """Append a table row for ``_rnd``; implemented by subclasses."""


class GameRoundPlot(QWidget):
    """Base score-plot widget wrapping a line-plot canvas."""

    def __init__(self, engine, parent: QWidget | None) -> None:
        super().__init__(parent)
        self.plotinited = False
        self.engine = engine
        # Deliberately shadows QObject.parent with the passed-in widget.
        self.parent = parent  # pyright: ignore[reportAttributeAccessIssue]
        self.axiswidth = 0
        self.initUI()

    def initUI(self) -> None:
        """Create the plot canvas and add its line plot."""
        self.widgetLayout = QHBoxLayout(self)
        self.canvas = PlotView(PlayerColours, self)
        self.canvas.setBackground(self.palette().color(self.backgroundRole()))
        self.canvas.addLinePlot()
        self.widgetLayout.addWidget(self.canvas)
        self.plotinited = True

    def paintEvent(self, event: QPaintEvent) -> None:
        self.canvas.setBackground(self.palette().color(self.backgroundRole()))
        super().paintEvent(event)
        self.canvas.viewport().repaint()

    def retranslateUI(self) -> None:
        self.retranslatePlot()

    def isPlotInited(self) -> bool:
        return self.plotinited

    def updatePlot(self) -> None:
        """Redraw the plot from current data; implemented by subclasses."""

    def retranslatePlot(self) -> None:
        """Refresh plot labels for the current language; overridden."""


class SpaceFilter(QtCore.QObject):
    """Event filter that turns a Space key press into a ``spacePressed`` signal."""

    spacePressed = QtCore.Signal()

    def eventFilter(self, obj: QObject, event) -> bool:
        if (
            event.type() == QtCore.QEvent.Type.KeyPress
            and event.key() == QtCore.Qt.Key.Key_Space
        ):
            self.spacePressed.emit()
            return True  # swallow the event
        return False


class ScoreSpinBox(QWidget):
    """A digits-only score field with up/down steppers and space handling."""

    valueChanged = QtCore.Signal(object)
    spacePressed = QtCore.Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._value: int | None = 0
        self._minimum = 0
        self._maximum = 200
        self._start = 0
        self._step = 1
        self._hideMinimum = True
        self.pcolour: QColor | None = None
        self.initUI()

    def initUI(self) -> None:
        """Build the line edit, stepper buttons, validator and styling."""
        self.line_edit = QLineEdit()
        self.line_edit.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.line_edit.setInputMethodHints(QtCore.Qt.InputMethodHint.ImhDigitsOnly)
        self.line_edit.setMinimumWidth(40)
        self.line_edit.setSizePolicy(
            QSizePolicy.Policy.MinimumExpanding, QSizePolicy.Policy.Preferred
        )
        # self.line_edit.installEventFilter(self)
        # self.line_edit.setMaximumWidth(120)

        self._validator = QtGui.QIntValidator(self._minimum, self._maximum, self)
        self.line_edit.setValidator(self._validator)

        self.space_filter = SpaceFilter()
        self.line_edit.installEventFilter(self.space_filter)
        self.space_filter.spacePressed.connect(self.onSpacePressed)

        self.up_button = QPushButton()
        self.down_button = QPushButton()
        self.up_button.setSizePolicy(
            QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred
        )
        self.down_button.setSizePolicy(
            QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred
        )
        # self.down_button.setMaximumWidth(120)
        # self.up_button.setMaximumWidth(120)

        self.up_button.setText("▲")
        self.down_button.setText("▼")

        self.up_button.setAutoRepeat(True)
        self.down_button.setAutoRepeat(True)

        group = QHBoxLayout()
        group.setSpacing(4)
        group.setContentsMargins(0, 0, 0, 0)
        group.addWidget(self.down_button, stretch=1)
        group.addWidget(self.line_edit, stretch=2)
        group.addWidget(self.up_button, stretch=1)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        # layout.addStretch()
        layout.addLayout(group)
        # layout.addStretch()
        # ---- Styling (safe defaults) ----
        self._text_css = """
            QLineEdit {{
                font-size: 24px;
                font-weight: bold;
                padding: 2px;
                color:rgb({0},{1},{2});
            }}
            QLineEdit:focus {{
                border: 2px solid rgb({0},{1},{2}) ;   /* highlight color */
            }}
            QLineEdit:focus:hover {{
                border: 2px solid rgb({0},{1},{2}) ;   /* highlight color */
            }}
            QLineEdit:hover {{
                border: 1px solid rgba({0},{1},{2},150) ;   /* highlight color */
            }}
        """
        self._text_css_colourless = """
            QLineEdit {
                font-weight: bold;
                padding: 2px;
            }
            QLineEdit:focus {
                border: 2px solid ;   /* highlight color */
            }
            QLineEdit:focus:hover {
                border: 2px solid ;   /* highlight color */
            }
            QLineEdit:hover {
                border: 1px solid ;   /* highlight color */
            }
        """

        # self._text_css = """
        #     QLineEdit {{
        #         font-size: 24px;
        #         font-weight: bold;
        #         padding: 2px;
        #         border-radius: 6px;
        #         border: 1px solid #555555 ;
        #         background: transparent;
        #         color:rgb({0},{1},{2});
        #     }}
        #     QLineEdit:focus {{
        #         border: 2px solid rgb({0},{1},{2}) ;   /* highlight color */
        #     }}
        #     QLineEdit:focus:hover {{
        #         border: 2px solid rgb({0},{1},{2}) ;   /* highlight color */
        #     }}
        #     QLineEdit:hover {{
        #         border: 1px solid rgba({0},{1},{2},150) ;   /* highlight color */
        #     }}
        # """
        self._updateStyle()

        # self.up_button.setStyleSheet(self._button_style())
        # self.down_button.setStyleSheet(self._button_style())

        # ---- Connections ----
        self.up_button.clicked.connect(self.step_up)
        self.down_button.clicked.connect(self.step_down)
        self.line_edit.textChanged.connect(self._commit_text)
        self.line_edit.editingFinished.connect(self._snap_to_step)

        if self._value is not None:
            self.setValue(self._value)

    # ------------------------------------------------------------------
    # Styling helper
    # ------------------------------------------------------------------
    def _button_style(self) -> str:
        return """
        QToolButton {
            font-size: 18px;
            font-weight: bold;
            border: 1px solid #555555;
            border-radius: 6px;
        }
        """

    def setHideMinimum(self, hidemin: bool) -> None:
        self._hideMinimum = hidemin

    def setColour(self, colour: QColor) -> None:
        self.pcolour = colour
        self._updateStyle()

    def _updateStyle(self) -> None:
        """Apply the coloured or colourless line-edit stylesheet."""
        if self.pcolour:
            self.line_edit.setStyleSheet(
                self._text_css.format(
                    self.pcolour.red(), self.pcolour.green(), self.pcolour.blue()
                )
            )
        else:
            self.line_edit.setStyleSheet(self._text_css_colourless)

    def value(self) -> int | None:
        return self._value

    def setValue(self, value: int | None) -> None:
        """Clamp and store ``value`` (``None`` clears the field)."""
        if value is None:
            if value != self._value:
                self.valueChanged.emit(value)
            self._value = None
            self.line_edit.setText("")
        else:
            value = max(self._minimum, min(self._maximum, value))
            if value != self._value:
                self._value = value
                if self._hideMinimum and value == self._minimum:
                    self.line_edit.setText("")
                else:
                    self.line_edit.setText(str(value))
                self.valueChanged.emit(value)
        self._update_buttons()

    def setStep(self, step: int) -> None:
        self._step = step

    def setFocus(
        self, reason: QtCore.Qt.FocusReason = QtCore.Qt.FocusReason.OtherFocusReason
    ) -> None:
        self.line_edit.setFocus(reason)

    def _snap_to_step(self) -> None:
        """Round the value down to the nearest multiple of the step size."""
        if self._value is not None and self._step > 1:
            offset = self._value - self._minimum
            new_value = self._minimum + (offset // self._step) * self._step
            if self._value != new_value:
                self.setValue(new_value)

    def step_up(self) -> None:
        self.line_edit.setFocus()
        if self._value is None:
            self.setValue(self._start)
        else:
            self.setValue(self._value + self._step)

    def step_down(self) -> None:
        self.line_edit.setFocus()
        if self._value is None:
            self.setValue(self._start)
        else:
            self.setValue(self._value - self._step)

    def _commit_text(self) -> None:
        """Parse the line-edit text into the current value."""
        try:
            value = int(self.line_edit.text())
        except ValueError:
            value = self._value
        self.setValue(value)

    def setRange(self, minimum: int, maximum: int, start: int | None = None) -> None:
        """Set the allowed value range and the default start value."""
        self._minimum = minimum
        self._maximum = maximum
        self._start = minimum if start is None else start
        self._validator = QtGui.QIntValidator(self._minimum, self._maximum, self)
        self.line_edit.setValidator(self._validator)
        self.setValue(self._value)

    def setMinimum(self, minimum: int) -> None:
        self.setRange(minimum, self._maximum)

    def setMaximum(self, maximum: int) -> None:
        self.setRange(self._minimum, maximum)

    def setSingleStep(self, step: int) -> None:
        self._step = max(1, step)

    def clear(self) -> None:
        self.line_edit.clear()

    def reset(self) -> None:
        self.setValue(None)

    def setReadOnly(self, ro: bool) -> None:
        self.line_edit.setReadOnly(ro)
        self.up_button.setDisabled(ro)
        self.down_button.setDisabled(ro)

    def lineEdit(self) -> QLineEdit:
        return self.line_edit

    def _update_buttons(self) -> None:
        """Enable/disable the steppers based on the value and bounds."""
        if not self.line_edit.isReadOnly():
            self.up_button.setEnabled(
                self._value is None or self._value < self._maximum
            )
            self.down_button.setEnabled(
                self._value is None or self._value > self._minimum
            )

    def wheelEvent(self, event: QWheelEvent) -> None:
        if self.line_edit.isReadOnly():
            return
        if event.angleDelta().y() > 0:
            self.step_up()
        else:
            self.step_down()
        event.accept()

    def textChangedAction(self, text: str) -> None:
        try:
            self.valueChanged.emit(int(text))
        except ValueError:
            pass

    def onSpacePressed(self) -> None:
        self.spacePressed.emit()

    def setDisabled(self, o: bool) -> None:
        super().setDisabled(o)
        if o:
            self.setValue(self._start)


class IconLabel(QLabel):
    """A label whose enabled/disabled state is fixed (ignores toggling)."""

    #     def __init__(self,parent = None):
    #         super(IconLabel,self).__init__(parent)
    #         self._pixmap = None
    #     def setPixmap(self,pixmap):
    #         self._pixmap = pixmap
    #         super(IconLabel,self).setPixmap(pixmap)
    #     def resizeEvent(self, event):
    #         size = min(self.width(), self.height())
    #         self.setFixedSize(size,size)
    #         if self._pixmap and not self._pixmap.isNull():
    #             print(event)
    #             self.setPixmap(self._pixmap.scaled(size,
    #                            size,QtCore.Qt.KeepAspectRatio,
    #                            QtCore.Qt.SmoothTransformation))
    def setDisabled(self, b: bool) -> None:
        pass

    def setEnabled(self, b: bool) -> None:
        pass


class BonusButton(QPushButton):
    """Circular toggle button counting a per-round bonus, with SVG/PNG icon."""

    bonusChanged = QtCore.Signal(str, object)

    def __init__(
        self,
        bonus_name: str,
        maximum: int = 1,
        colour: QColor | None = None,
        size: int = 32,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)

        self.bonus_name = bonus_name
        self.maximum = maximum
        self.count = 0
        self.button_size = size
        self.highlight_colour = colour if colour else QColor(200, 0, 0)

        # Keep SVGs as SVGs and render them directly in paintEvent().
        self.svg_renderer: QSvgRenderer | None = None
        self._disabled_svg_cache: dict = {}

        svg_path = f":/icons/{bonus_name}.svg"
        png_path = f":/icons/{bonus_name}.png"

        if QFile.exists(svg_path):
            self.svg_renderer = QSvgRenderer(svg_path)

            if not self.svg_renderer.isValid():
                self.svg_renderer = None

        if self.svg_renderer is None and QFile.exists(png_path):
            original_image = QImage(png_path)

            self.image = original_image.scaled(
                self.button_size,
                self.button_size,
                QtCore.Qt.AspectRatioMode.KeepAspectRatio,
                QtCore.Qt.TransformationMode.SmoothTransformation,
            )

            self.grey_image = self.image.convertToFormat(
                QImage.Format.Format_Grayscale8
            )

        elif self.svg_renderer is None:
            # No SVG or PNG exists, so create a fallback icon.
            original_image = QImage(
                self.button_size,
                self.button_size,
                QImage.Format.Format_ARGB32_Premultiplied,
            )
            original_image.fill(QtCore.Qt.GlobalColor.transparent)

            painter = QPainter(original_image)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)

            # Light grey circle
            painter.setBrush(QColor("#D3D3D3"))
            painter.setPen(QtCore.Qt.PenStyle.NoPen)

            painter.drawEllipse(
                2,
                2,
                self.button_size - 4,
                self.button_size - 4,
            )

            # Bonus name
            painter.setPen(QColor("#333333"))
            painter.setFont(
                QFont(
                    "Arial",
                    int(self.button_size * 0.4),
                    QFont.Weight.Bold,
                )
            )

            painter.drawText(
                original_image.rect(),
                QtCore.Qt.AlignmentFlag.AlignCenter,
                bonus_name.upper(),
            )

            painter.end()

            self.image = original_image
            self.grey_image = original_image.convertToFormat(
                QImage.Format.Format_Grayscale8
            )

        self.setCheckable(True)
        self.setFlat(True)
        self.setStyleSheet("border: none;")

        self.setFixedSize(
            self.button_size,
            self.button_size,
        )

        self._fade_alpha = 0.0

        self.fade_anim = QPropertyAnimation(
            self,
            b"fade_alpha",
        )
        self.fade_anim.setDuration(400)
        self.fade_anim.setEasingCurve(QEasingCurve.Type.OutCubic)

        self.clicked.connect(self.plusone)

    def setColour(self, colour: QColor) -> None:
        self.highlight_colour = colour

    def plusone(self) -> None:
        """Advance the bonus count by one (wrapping past the maximum)."""
        old_value = self.count

        self.count = (self.count + 1) % (self.maximum + 1)

        self.setChecked(self.count > 0)

        # Transition 0 -> >0
        if old_value == 0 and self.count > 0:
            self.fade_anim.stop()
            self.fade_anim.setStartValue(0.0)
            self.fade_anim.setEndValue(1.0)
            self.fade_anim.start()

        # Transition >0 -> 0
        elif old_value > 0 and self.count == 0:
            self.fade_anim.stop()
            self.fade_anim.setStartValue(1.0)
            self.fade_anim.setEndValue(0.0)
            self.fade_anim.start()

        self.bonusChanged.emit(
            self.bonus_name,
            self,
        )
        self.update()

    def get_fade_alpha(self) -> float:
        return self._fade_alpha

    def set_fade_alpha(self, value: float) -> None:
        self._fade_alpha = float(value)
        self.update()

    fade_alpha = QtCore.Property(
        float,
        get_fade_alpha,
        set_fade_alpha,
    )

    def getValue(self) -> int:
        return self.count if self.isEnabled() else 0

    def setChecked(self, checked: bool) -> None:
        if not checked:
            self.count = 0

        super().setChecked(checked)

    def sizeHint(self) -> QSize:
        return QtCore.QSize(
            self.button_size,
            self.button_size,
        )

    def setMaximum(self, maximum: int) -> None:
        """Set the count ceiling, clamping the current count to fit."""
        self.maximum = maximum

        if self.count > self.maximum:
            self.count = self.maximum

            if self.count == 0:
                self.setChecked(False)

            self.update()

    def _disabled_svg_image(self, dpr: float) -> QImage:
        """Return a cached greyed-out rasterisation of the SVG icon."""
        key = (self.width(), self.height(), dpr)

        if key not in self._disabled_svg_cache:
            image = QImage(
                round(self.width() * dpr),
                round(self.height() * dpr),
                QImage.Format.Format_ARGB32_Premultiplied,
            )
            image.fill(QtCore.Qt.GlobalColor.transparent)

            image_painter = QPainter(image)
            image_painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            if self.svg_renderer:
                self.svg_renderer.render(image_painter, QRectF(image.rect()))

            image_painter.end()

            # Preserve the source luminance, rather than painting a single
            # flat grey. This makes different disabled icons distinguishable
            # while retaining their transparency.
            for y in range(image.height()):
                for x in range(image.width()):
                    colour = image.pixelColor(x, y)
                    grey = round(
                        0.299 * colour.red()
                        + 0.587 * colour.green()
                        + 0.114 * colour.blue()
                    )
                    colour.setRgb(grey, grey, grey, colour.alpha())
                    image.setPixelColor(x, y, colour)

            self._disabled_svg_cache[key] = image

        return self._disabled_svg_cache[key]

    def paintEvent(self, event: QPaintEvent) -> None:
        painter = QPainter(self)

        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)

        # --------------------------------------------------
        # Circular clipping
        # --------------------------------------------------

        path = QPainterPath()

        radius = (
            min(
                self.width(),
                self.height(),
            )
            / 2
        )

        center = self.rect().center()

        path.addEllipse(
            center,
            radius,
            radius,
        )

        # painter.setClipPath(path)

        # --------------------------------------------------
        # Draw icon
        # --------------------------------------------------

        if self.svg_renderer is not None:
            if self.isEnabled():
                # Render enabled SVGs directly, avoiding intermediate
                # low-resolution rasterisation.
                self.svg_renderer.render(
                    painter,
                    QRectF(self.rect()),
                )
            else:
                painter.drawImage(
                    self.rect(),
                    self._disabled_svg_image(painter.device().devicePixelRatioF()),
                )
                self.setChecked(False)

        else:
            if self.isEnabled():
                img_to_draw = self.image
            else:
                img_to_draw = self.grey_image
                self.setChecked(False)

            painter.drawImage(
                self.rect(),
                img_to_draw,
            )

        # --------------------------------------------------
        # Active outline
        # --------------------------------------------------

        if self.count > 0:
            alpha = int(255 * self._fade_alpha)

            ring_radius = radius - 2

            colour = QColor(self.highlight_colour)
            colour.setAlpha(alpha)

            pen = painter.pen()
            pen.setColor(colour)
            pen.setWidth(4)

            painter.setPen(pen)
            painter.setBrush(QtCore.Qt.BrushStyle.NoBrush)
            center.setX(center.x() + 1)
            center.setY(center.y() + 1)

            painter.drawEllipse(
                center,
                ring_radius,
                ring_radius,
            )

        # --------------------------------------------------
        # Count overlay
        # --------------------------------------------------

        if self.count >= 1 and self.maximum > 1:
            # Semi-transparent dark circle
            # behind the number.
            overlay_color = QColor(
                0,
                0,
                0,
                120,
            )

            painter.setBrush(overlay_color)
            painter.setPen(QtCore.Qt.PenStyle.NoPen)

            circle_diameter = (
                min(
                    self.width(),
                    self.height(),
                )
                * 0.45
            )

            circle_rect = QRectF(
                (self.width() - circle_diameter) / 2,
                (self.height() - circle_diameter) / 2,
                circle_diameter,
                circle_diameter,
            )

            painter.drawEllipse(circle_rect)

            # Number
            painter.setPen(self.highlight_colour)

            font = QFont(
                "Arial",
                int(circle_diameter * 0.9),
                QFont.Weight.Bold,
            )

            painter.setFont(font)

            painter.drawText(
                self.rect(),
                QtCore.Qt.AlignmentFlag.AlignCenter,
                str(self.count),
            )

        painter.end()


class SleepBlocker:
    """Cross-platform helper that keeps the screen and system awake."""

    def __init__(self) -> None:
        self.platform = sys.platform
        self.proc: subprocess.Popen | None = None
        self.active = False

        # Windows constants
        self.ES_CONTINUOUS = 0x80000000
        self.ES_SYSTEM_REQUIRED = 0x00000001
        self.ES_DISPLAY_REQUIRED = 0x00000002

    def start(self) -> None:
        """Block sleep/screensaver for the current platform."""
        if self.active:
            return

        if self.platform == "darwin":
            self._start_macos()
        elif self.platform.startswith("win"):
            self._start_windows()
        elif self.platform.startswith("linux"):
            self._start_linux()

        self.active = True

    def stop(self) -> None:
        """Release the sleep/screensaver block for the current platform."""
        if not self.active:
            return

        if self.platform == "darwin":
            self._stop_macos()
        elif self.platform.startswith("win"):
            self._stop_windows()
        elif self.platform.startswith("linux"):
            self._stop_linux()

        self.active = False

    # -------- macOS --------
    def _start_macos(self) -> None:
        self.proc = subprocess.Popen(
            ["caffeinate", "-dims"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

    def _stop_macos(self) -> None:
        if self.proc:
            self.proc.terminate()
            self.proc = None

    # -------- Windows --------
    def _start_windows(self) -> None:
        ctypes.windll.kernel32.SetThreadExecutionState(
            self.ES_CONTINUOUS | self.ES_SYSTEM_REQUIRED | self.ES_DISPLAY_REQUIRED
        )

    def _stop_windows(self) -> None:
        ctypes.windll.kernel32.SetThreadExecutionState(self.ES_CONTINUOUS)

    # -------- Linux (X11 only) --------
    def _start_linux(self) -> None:
        if shutil.which("xset"):
            subprocess.call(["xset", "s", "off"])
            subprocess.call(["xset", "-dpms"])

    def _stop_linux(self) -> None:
        if shutil.which("xset"):
            subprocess.call(["xset", "s", "on"])
            subprocess.call(["xset", "+dpms"])


class GameNotImplementedException(Exception):
    """Raised when a requested game has no concrete implementation."""


class CardWidget(QWidget):
    """A small aspect-ratio-preserving playing-card widget."""

    ASPECT_RATIO = 2.5 / 3.5
    MAX_WIDTH = 20
    MAX_HEIGHT = int(MAX_WIDTH / ASPECT_RATIO)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setMaximumSize(self.MAX_WIDTH, self.MAX_HEIGHT)
        self.reset()

    def sizeHint(self) -> QSize:
        return QSize(self.MAX_WIDTH, self.MAX_HEIGHT)

    def minimumSizeHint(self) -> QSize:
        return QSize(20, int(20 / self.ASPECT_RATIO))

    def hasHeightForWidth(self) -> bool:
        return True

    def heightForWidth(self, width: int) -> int:
        return int(width / self.ASPECT_RATIO)

    def paintEvent(self, event: QPaintEvent) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Scale everything according to the current card width.
        corner_radius = self.width() * 0.20
        font_size = self.width() * 0.90

        # Card
        painter.setBrush(self._colour)
        painter.setPen(QtCore.Qt.GlobalColor.black)
        painter.drawRoundedRect(self.rect(), corner_radius, corner_radius)

        # Character
        if self._character:
            font = QFont("Arial")
            font.setPixelSize(int(font_size))
            font.setBold(True)
            painter.setFont(font)
            painter.setPen(QtCore.Qt.GlobalColor.black)

            painter.drawText(
                self.rect(), QtCore.Qt.AlignmentFlag.AlignCenter, self._character
            )

    def getColour(self) -> QColor:
        return self._colour

    def setColour(self, colour: QColor | str) -> None:
        if isinstance(colour, str):
            self._colour = QColor(colour)
        else:
            self._colour = colour
        self.update()

    def getChar(self) -> str:
        return self._character

    def setChar(self, character: str) -> None:
        self._character = character
        self.update()

    def reset(self, colour: QColor | None = None, char: str | None = None) -> None:
        """Reset the card's colour and character (both default to blank)."""
        self._colour = colour if colour else QColor("grey")
        self._character = str(char) if char else ""
        self.update()


class ToggleGroupBox(QGroupBox):
    """A group box holding stacked screens that cycle on any child click."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        self.current = 0
        self.screens: list[QWidget] = []
        self.widgetLayout = QStackedLayout(self)

    def addScreen(self, widget: QWidget) -> None:
        """Add a screen and route clicks on it (and its children) to toggle."""
        self._install_event_filters(widget)
        self.screens.append(widget)
        self.widgetLayout.addWidget(widget)

    def _install_event_filters(self, widget: QWidget) -> None:
        """Install this filter on ``widget`` and all of its descendants."""
        widget.installEventFilter(self)

        for child in widget.findChildren(QObject):
            child.installEventFilter(self)

    def eventFilter(self, watched: QObject, event) -> bool:
        if (
            event.type() == QEvent.Type.MouseButtonPress
            and event.button() == QtCore.Qt.MouseButton.LeftButton
        ):
            self.toggle()
            return True

        return super().eventFilter(watched, event)

    def toggle(self) -> None:
        """Advance to the next stacked screen, wrapping around."""
        if len(self.screens) < 2:
            return
        self.current = (self.current + 1) % len(self.screens)
        self.widgetLayout.setCurrentIndex(self.current)
        # for i, screen in enumerate(self.screens):
        #     screen.setVisible(i == self.current)
