"""Scrabble scoreboard widgets: per-turn score input, entry table and plot."""

from __future__ import annotations

import logging
from typing import cast

from PySide6 import QtCore
from PySide6.QtWidgets import (
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QSizePolicy,
    QTableWidgetItem,
    QWidget,
)

from core.engine.settings import appsettings
from core.ui.countdown import CountdownTimer
from core.ui.game import (
    BonusButton,
    GameInputWidget,
    GameNotImplementedException,
    GameRoundPlot,
    GameRoundsDetail,
    GameRoundTable,
    GameWidget,
    PlayerColours,
    ScoreSpinBox,
)
from core.ui.gamestats import GeneralQuickStats, ParticularQuickStats, QuickStatsTW
from games.scrabble.engine import ScrabbleEngine

logger = logging.getLogger(__name__)


class ScrabbleWidget(GameWidget):
    """Scoreboard tab for Scrabble: one score entry per player turn."""

    def createEngine(self) -> None:
        if self.game != "Scrabble":
            raise GameNotImplementedException(f"No engine for game {self.game}")
        self.engine = ScrabbleEngine()

    def initUI(self) -> None:
        super().initUI()
        self.dealerPolicyCheckBox.hide()

        gi = cast("ScrabbleInputWidget", self.gameInput)
        gi.countdown.driveWith(self.clock)
        gi.placeCommitButton(self.commitRoundButton)
        gi.placeUndoButton(self.undoButton)
        for b in (self.commitRoundButton, self.undoButton):
            b.setSizePolicy(
                QSizePolicy.Policy.MinimumExpanding, QSizePolicy.Policy.Preferred
            )
        self.retranslateUI()

    def createGameInputWidget(
        self, parent: QWidget | None = None
    ) -> ScrabbleInputWidget:  # pyright: ignore[reportIncompatibleMethodOverride]
        return ScrabbleInputWidget(self.engine, parent)

    def createRoundsDetail(
        self, parent: QWidget | None = None
    ) -> ScrabbleEntriesDetail:
        return ScrabbleEntriesDetail(self.engine, parent)

    def retranslateUI(self):
        super().retranslateUI()
        if appsettings["text_in_buttons"]:
            self.turnTimeLabel.setText(self.tr("Turn (s)"))
        else:
            self.turnTimeLabel.setText("⏱")

    def checkPlayerScore(
        self, player: str, score: int, extras: dict | None = None
    ) -> bool:
        return bool(score)

    def commitRoundSanityCheck(self, interactive: bool = False) -> bool:
        """Validate that a player is selected and their score is acceptable."""
        gi = cast("ScrabbleInputWidget", self.gameInput)
        player = gi.getPlayer()
        bonuses = gi.getBonuses()
        score = gi.getScore()
        if player == "":
            msg = self.tr("You must select a player")
            if interactive:
                QMessageBox.warning(self, self.game, msg)
            else:
                logger.debug("[sanity] %s", msg)
            return False

        if not self.checkPlayerScore(cast("str", player), cast("int", score), bonuses):
            msg = self.tr("{} score is not valid").format(player)
            if interactive:
                QMessageBox.warning(self, self.game, msg)
            else:
                logger.debug("[sanity] %s", msg)
            return False
        return True

    def commitRound(self) -> None:
        """Record the current player's score and bonuses as one entry."""
        if not self.commitRoundSanityCheck(interactive=True):
            return
        # Once here, we can commit round
        self.unsetDealer()
        gi = cast("ScrabbleInputWidget", self.gameInput)
        player = gi.getPlayer()
        bonuses = gi.getBonuses()
        score = gi.getScore()
        cast("ScrabbleEngine", self.engine).addEntry(
            cast("str", player), cast("int", score), bonuses
        )
        self.engine.printStats()
        self.updatePanel()
        if not self.engine.getWinner():
            self.setDealer()
        elif self.hideInputOnFinish:
            self.gameInput.hide()

    def addExtraConfig(self) -> None:
        """Add the per-turn countdown spin box below the game clock."""
        super().addExtraConfig()
        self.turnTimeLayout = QHBoxLayout()
        self.matchGroupLayout.addLayout(self.turnTimeLayout)
        self.turnTimeLabel = QLabel("⏱", self.matchGroup)
        self.turnTimeLabel.setSizePolicy(
            QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred
        )
        self.turnTimeLayout.addWidget(self.turnTimeLabel)
        self.turnSecondsBox = ScoreSpinBox(self.matchGroup)
        self.turnSecondsBox.setRange(10, 600, 120)
        self.turnSecondsBox.setValue(120)
        self.turnSecondsBox.lineEdit().setFocusPolicy(QtCore.Qt.FocusPolicy.ClickFocus)
        self.turnSecondsBox.setSizePolicy(
            QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Maximum
        )
        self.turnSecondsBox.valueChanged.connect(self.changeTurnSeconds)
        self.turnTimeLayout.addWidget(self.turnSecondsBox)
        # self.matchGroupLayout.addWidget(
        #     self.turnSecondsBox, alignment=QtCore.Qt.AlignmentFlag.AlignLeft
        # )

    def changeTurnSeconds(self, value: int | None = None) -> None:
        """Apply the new turn duration and reset the running countdown."""
        if value is None:
            value = self.turnSecondsBox.value()
        if value is None:
            return
        gi = cast("ScrabbleInputWidget", self.gameInput)
        gi.countdown.reset(int(value))
        gi.countdown.start()

    def pauseMatch(self) -> None:
        super().pauseMatch()
        gi = cast("ScrabbleInputWidget", self.gameInput)
        if self.engine.isPaused():
            gi.countdown.pause()
        else:
            gi.countdown.resume()

    def setDealer(self) -> None:
        super().setDealer()
        self.gameInput.reset()


class ScrabbleInputWidget(GameInputWidget):
    """Single-player score entry with a score field and bonus buttons."""

    def __init__(self, engine, parent) -> None:
        self.active_player = engine.getDealer()
        self._turn_seconds = 120
        super().__init__(engine, parent)

    def initUI(self) -> None:
        self.setStyleSheet("QGroupBox { font-size: 18px; font-weight: bold; }")
        self.widgetLayout = QHBoxLayout(self)
        self.currentPlayerBox = QGroupBox(self)
        self.widgetLayout.addWidget(self.currentPlayerBox, 2)
        self.currentPlayerBoxLayout = QHBoxLayout(self.currentPlayerBox)
        self.countdown = CountdownTimer(
            self._turn_seconds, parent=self.currentPlayerBox
        )
        self.countdown.setFixedSize(64, 64)
        self.currentPlayerBoxLayout.addWidget(self.countdown)
        self.scoreSpinBox = ScoreSpinBox(self.currentPlayerBox)
        self.scoreSpinBox.setRange(-60, 400, 0)
        self.currentPlayerBoxLayout.addWidget(self.scoreSpinBox)
        self.scoreSpinBox.valueChanged.connect(self.changed)
        self.bonusButtons = {}
        self.createBonusButtons()
        self.reset()

    def createBonusButtons(self) -> None:
        """Build one bonus button per configured Scrabble bonus."""
        for b, maxreps in cast("ScrabbleEngine", self.engine).getBonuses().items():
            bb = BonusButton(
                b, maxreps, colour=None, size=32, parent=self.currentPlayerBox
            )
            self.bonusButtons[b] = bb
            self.currentPlayerBoxLayout.addWidget(bb)
            bb.bonusChanged.connect(self.changed)

    def retranslateUI(self) -> None:
        if appsettings["text_in_buttons"]:
            css = """
                QPushButton {
                    font-weight: normal;
                }
                """
        else:
            css = """
                QPushButton {
                    font-size: 48px;
                    font-weight: bold;
                }
                """
        self.commitButton.setStyleSheet(css)
        self.undoButton.setStyleSheet(css)

    def placeCommitButton(self, cb) -> None:
        # cb.setStyleSheet("""
        #     QPushButton {
        #         font-size: 48px;
        #         font-weight: bold;
        #     }
        #     """)
        self.commitButton = cb
        self.widgetLayout.addWidget(cb, 1)

    def placeUndoButton(self, ub) -> None:
        # ub.setStyleSheet("""
        #     QPushButton {
        #         font-size: 48px;
        #         font-weight: bold;
        #     }
        #     """)
        self.undoButton = ub
        self.widgetLayout.insertWidget(0, ub, 1)

    def getPlayer(self) -> str | None:
        return self.active_player

    def getBonuses(self) -> dict:
        return {b: bb.getValue() for b, bb in self.bonusButtons.items()}

    def getScore(self) -> int | None:
        return self.scoreSpinBox.value()

    def setColour(self, colour) -> None:
        css = """
            QGroupBox {{ font-size: 24px; font-weight: bold; color:rgb({},{},{});}}
            QGroupBox:focus-within {{ border: 2px solid #0078d7; background-color: #e6f1fb;}}
            QGroupBox::title {{
                    subcontrol-origin: margin;
                    subcontrol-position: top center;
                    padding: 0 10px;
                    background-color: transparent;
            }}
        """
        self.currentPlayerBox.setStyleSheet(
            css.format(colour.red(), colour.green(), colour.blue())
        )
        self.countdown.setColor(colour)
        self.scoreSpinBox.setColour(colour)
        for bb in self.bonusButtons.values():
            bb.setColour(colour)

    def reset(self) -> None:
        """Reset the entry to the current dealer with a cleared score field."""
        self.active_player = self.engine.getDealer()
        colour = PlayerColours[
            self.engine.getListPlayers().index(cast("str", self.active_player))
        ]
        self.setColour(colour)
        self.currentPlayerBox.setTitle(f"{self.active_player}")
        self.scoreSpinBox.reset()
        for bb in self.bonusButtons.values():
            bb.setChecked(False)
        self.countdown.reset()
        self.countdown.start()
        self.scoreSpinBox.setFocus()

    def updatePlayerOrder(self) -> None:
        self.reset()

    # def keyPressEvent(self, event):
    #     if event.key() == QtCore.Qt.Key.Key_Return:
    #         self.enterPressed.emit()
    #         event.accept()
    #     return super().keyPressEvent(event)


class ScrabbleEntriesDetail(GameRoundsDetail):
    """Entries detail panel for Scrabble, defaulting to the plot tab."""

    def __init__(self, engine, parent=None) -> None:
        super().__init__(engine, parent)
        self.setCurrentWidget(self.plot)

    def createRoundTable(self, engine, parent=None) -> ScrabbleRoundTable:
        return ScrabbleRoundTable(self.engine, parent)

    def createRoundPlot(self, engine, parent=None) -> ScrabbleEntriesPlot:
        return ScrabbleEntriesPlot(self.engine, self)

    def createQSBox(self, parent=None) -> ScrabbleQSTW:
        # getGame() is typed str | None; a live engine always has a game name.
        return ScrabbleQSTW(
            self.engine.getGame(),  # pyright: ignore[reportArgumentType]
            self.engine.getListPlayers(),
            self,
        )


class ScrabbleRoundTable(GameRoundTable):
    """Grid of scoring entries, one column per player, marking bonus turns."""

    def insertRound(self, entry) -> None:
        """Place ``entry``'s score (and bonus stars) in its player's column."""
        players = self.engine.getListPlayers()
        i = (entry.getNumRound() - 1) // len(players)
        j = players.index(entry.getPlayer())
        if self.rowCount() <= i:
            self.insertRow(i)
            for col, _ in enumerate(self.engine.getListPlayers()):
                item = QTableWidgetItem()
                item.setFlags(item.flags() ^ QtCore.Qt.ItemFlag.ItemIsEditable)
                item.setTextAlignment(
                    QtCore.Qt.AlignmentFlag.AlignVCenter
                    | QtCore.Qt.AlignmentFlag.AlignCenter
                )
                item.setText("")
                self.setItem(i, col, item)

        item = self.item(i, j)
        if item:
            text = "{} {}".format(
                entry.getPlayerScore(), "*" * sum(entry.getBonuses().values())
            )
            if entry.getBonuses():
                font = item.font()
                font.setBold(True)
                item.setFont(font)
            item.setText(text)
        self.scrollToBottom()

    def openTableMenu(self, position) -> None:
        # Use Undo to remove
        return
        # players = self.engine.getListPlayers()
        # index = self.indexAt(position)
        # item = self.itemAt(position)
        # nentry = (index.row()) * len(players) + index.column()
        # print(f"right click on nentry {nentry}")
        # if nentry <= 0 or self.engine.getWinner():
        #     return

        # menu = QMenu()
        # ic = QtGui.QIcon(":/icons/delete.png")
        # msg = self.tr("Delete Entry")
        # deleteEntryAction = QAction(ic, msg, self)
        # menu.addAction(deleteEntryAction)
        # action = menu.exec_(self.mapToGlobal(position))
        # if action == deleteEntryAction:
        #     title = self.tr("Delete Entry")
        #     msg = self.tr("Are you sure you want to delete this entry?")
        #     ret = QMessageBox.question(
        #         self,
        #         title,
        #         msg,
        #         QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        #         QMessageBox.StandardButton.Yes,
        #     )
        #     if ret == QMessageBox.StandardButton.No:
        #         return
        #     self.engine.deleteRound(nentry)
        #     if item:
        #         item.setText("")
        #     self.edited.emit()


class ScrabbleEntriesPlot(GameRoundPlot):
    """Cumulative-score plot advancing only the player who scored each entry."""

    def updatePlot(self) -> None:
        if not self.isPlotInited():
            return
        super().updatePlot()
        scores = {}
        for player in self.engine.getPlayers():
            scores[player] = [0]

        for entry in self.engine.getRounds():
            for player in self.engine.getPlayers():
                if player == entry.getPlayer():
                    entryscore = entry.getPlayerScore()
                    accumscore = scores[player][-1] + entryscore
                    scores[player].append(accumscore)

        # Temporary pad for other players:
        max_len = max(len(series) for series in scores.values())
        for series in scores.values():
            series.extend([series[-1]] * (max_len - len(series)))

        self.canvas.clearPlotContents()

        for player in self.engine.getListPlayers():
            self.canvas.addSeries(scores[player], player)

        self.canvas._scene.update()


class ScrabbleQSTW(QuickStatsTW):
    """Quick-stats tab set for Scrabble."""

    def initStatsWidgets(self) -> None:
        self.gs = ScrabbleQSBox(self.game, self)
        self.ps = ScrabblePQSBox(self.game, self)


class ScrabbleQSBox(GeneralQuickStats):
    """General quick-stats page adding best-play and max-bonus columns."""

    def __init__(self, gname, parent=None) -> None:
        super().__init__(gname, parent)
        self.playerStatsKeys.append("max_round_score")
        self.playerStatsHeaders.append(self.tr("Best Play"))
        self.playerStatsKeys.append("max_bonuses")
        self.playerStatsHeaders.append(self.tr("Max Bonus"))
        for i in ("minscore", "sumscore"):
            try:
                self.playerStatsKeys.remove(i)
            except KeyError:
                pass
        for i in ("Lowest", "Total"):
            try:
                self.playerStatsHeaders.remove(i)
            except KeyError:
                pass


class ScrabblePQSBox(ScrabbleQSBox, ParticularQuickStats):
    """Player-filtered variant of the Scrabble quick-stats page."""
