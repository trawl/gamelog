"""Qt scoreboard widgets for Parchis: entry input, table, plot and stats."""

from __future__ import annotations

import logging
from typing import cast

from PySide6 import QtCore
from PySide6.QtGui import QKeyEvent
from PySide6.QtWidgets import (
    QButtonGroup,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QMessageBox,
    QRadioButton,
    QSizePolicy,
    QWidget,
)

from core.ui.game import (
    GameInputWidget,
    GameNotImplementedException,
    GameRoundPlot,
    GameRoundsDetail,
    GameRoundTable,
    GameWidget,
    PlayerColours,
    QuickStatsTW,
    ScoreSpinBox,
)
from core.ui.gamestats import GeneralQuickStats, ParticularQuickStats
from games.parchis.engine import ParchisEngine

logger = logging.getLogger(__name__)


class ParchisWidget(GameWidget):
    """Scoreboard tab for Parchis, scored one feature entry at a time."""

    def createEngine(self) -> None:
        if self.game != "Parchis":
            raise GameNotImplementedException(f"No engine for game {self.game}")
        self.engine = ParchisEngine()

    def initUI(self) -> None:
        """Build the scoreboard and dock the commit/undo buttons into the input."""
        super().initUI()
        if not self.gameInput:
            self.gameInput = self.createGameInputWidget(self)

        self.commitRoundButton.setSizePolicy(
            QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred
        )
        self.undoButton.setSizePolicy(
            QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred
        )
        self.gameInput.placeCommitButton(self.commitRoundButton)
        self.gameInput.placeUndoButton(self.undoButton)

        self.retranslateUI()
        QtCore.QTimer.singleShot(1000, self.gameInput.setFocus)

    def createGameInputWidget(
        self, parent: QWidget | None = None
    ) -> ParchisInputWidget:
        return ParchisInputWidget(self.engine, parent)

    def createRoundsDetail(self, parent: QWidget | None = None) -> ParchisEntriesDetail:
        return ParchisEntriesDetail(self.engine, parent)

    def getPlayerExtraInfo(self, player: str) -> dict:
        """Return the selected kills for the current entry, if any."""
        kills = self.gameInput.getKills()
        if kills:
            return {"kills": kills}
        else:
            return {}

    def checkPlayerScore(
        self, player: str, score: int, extras: dict | None = None
    ) -> bool:
        return 0 <= score <= 4

    def commitRoundSanityCheck(self, interactive: bool = False) -> bool:
        """Check that a player, a kind and a valid score are all selected."""
        player = self.gameInput.getPlayer()
        score = self.gameInput.getScore()
        if player == "":
            msg = self.tr("You must select a player")
            if interactive:
                QMessageBox.warning(self, self.game, msg)
            logger.debug(f"[commitRoundSanityCheck] {msg}")
            return False

        if not self.checkPlayerScore(player, score):
            msg = self.tr(f"{player} score is not valid")
            if interactive:
                QMessageBox.warning(self, self.game, msg)
            logger.debug(f"[commitRoundSanityCheck] {msg} {score}")
            return False

        # Empty entry, no score, no kills
        if score == 0 and not self.gameInput.getKills():
            msg = self.tr("Empty entry, add at least a goal or a kill")
            if interactive:
                QMessageBox.warning(self, self.game, msg)
            logger.debug(f"[commitRoundSanityCheck] {msg}")
            return False

        logger.debug("[commitRoundSanityCheck] Ready to commit")
        return True

    def commitRound(self) -> None:
        """Record the selected player's scoring entry and refresh the board."""
        if not self.commitRoundSanityCheck(interactive=True):
            return
        player = self.gameInput.getPlayer()
        score = self.gameInput.getScore()
        try:
            self.playerGroupBox[self.engine.getDealer()].unsetDealer()
        except KeyError:
            pass
        cast("ParchisEngine", self.engine).addEntry(
            player, score, self.getPlayerExtraInfo(player)
        )
        self.engine.printStats()
        self.updatePanel()


class ParchisInputWidget(GameInputWidget):
    """Player/kind/score selectors for entering a single Parchis score."""

    enterPressed = QtCore.Signal()

    def __init__(self, engine, parent) -> None:
        super().__init__(engine, parent)

    def initUI(self) -> None:
        """Lay out the player, kind and score selector groups."""
        self.setStyleSheet("QGroupBox { font-size: 18px; font-weight: bold; }")
        self.widgetLayout = QHBoxLayout(self)
        self.playerGroup = QGroupBox(self)
        self.widgetLayout.addWidget(self.playerGroup)
        self.playerButtonGroup = QButtonGroup(self)
        self.playerGroupLayout = QGridLayout(self.playerGroup)

        b = QRadioButton("", self.playerGroup)
        #        self.playerGroupLayout.addWidget(b)
        self.playerButtonGroup.addButton(b, 0)
        self.playerButtons = [b]
        b.hide()
        for i, player in enumerate(self.engine.getListPlayers(), 1):
            b = QRadioButton(f"{i}. {player}", self.playerGroup)
            if len(self.engine.getListPlayers()) > 2:
                self.playerGroupLayout.addWidget(b, (i - 1) % 2, (i - 1) // 2)
            else:
                self.playerGroupLayout.addWidget(b, 0, (i - 1) % 2)
            self.playerButtonGroup.addButton(b, i)
            self.playerButtons.append(b)

        self.playerButtonGroup.idToggled.connect(self.changed)

        self.goalsSpinBox = ScoreSpinBox(self)
        self.goalsSpinBox.setRange(0, 4, 0)
        self.goalsSpinBox.setHideMinimum(False)
        self.goalsSpinBox.setSizePolicy(
            QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Preferred
        )
        self.goalsSpinBox.valueChanged.connect(self.changed)

        self.goalsGroup = QGroupBox(self)
        self.widgetLayout.addWidget(self.goalsGroup)
        self.goalsGroupLayout = QHBoxLayout(self.goalsGroup)

        self.goalsGroupLayout.addWidget(self.goalsSpinBox)

        self.killsGroup = QGroupBox(self)
        self.widgetLayout.addWidget(self.killsGroup)
        self.killsGroupLayout = QGridLayout(self.killsGroup)
        self.killBoxes = []
        for i, _ in enumerate(self.engine.getListPlayers()):
            ksb = ScoreSpinBox(self)
            ksb.setRange(0, 4, 0)
            ksb.setHideMinimum(False)
            ksb.setSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Preferred)
            ksb.valueChanged.connect(self.changed)
            if len(self.engine.getListPlayers()) > 2:
                self.killsGroupLayout.addWidget(ksb, (i) % 2, (i) // 2)
            else:
                self.killsGroupLayout.addWidget(ksb, 0, (i) % 2)
            self.killBoxes.append(ksb)

        self.reset()
        self.retranslateUI()

    def retranslateUI(self) -> None:
        self.playerGroup.setTitle(self.tr("Select Player"))
        self.goalsGroup.setTitle(self.tr("Select number of goals"))
        self.killsGroup.setTitle(self.tr("Select Kills"))

    def placeCommitButton(self, cb) -> None:
        self.widgetLayout.addWidget(cb, 2)

    def placeUndoButton(self, ub) -> None:
        self.widgetLayout.addWidget(ub, 1)

    def getPlayer(self) -> str:
        """Return the selected player's name, or ``""`` if none is selected."""
        pid = self.playerButtonGroup.checkedId()
        if not pid:
            return ""
        player = self.engine.getListPlayers()[pid - 1]
        return str(player)

    def getKills(self) -> list[str]:
        """Return the sequence of kills"""
        kills = []
        for p, bsk in enumerate(self.killBoxes):
            for _ in range(0, bsk.value()):
                kills.append(self.engine.getListPlayers()[p])
        return kills

    def getScore(self) -> int:
        return cast("int", self.goalsSpinBox.value())

    def reset(self) -> None:
        """Clear the player/kind selection and reset the score to zero."""
        self.playerButtons[0].setChecked(True)
        self.goalsSpinBox.setValue(0)
        for i, ksb in enumerate(self.killBoxes):
            ksb.setColour(PlayerColours[i])
            ksb.setValue(0)
        self.changed.emit()
        self.setFocus()

    def keyPressEvent(self, event: QKeyEvent) -> None:
        """Route number keys to the player then kind selection, Return commits."""
        numberkeys = [
            QtCore.Qt.Key.Key_1,
            QtCore.Qt.Key.Key_2,
            QtCore.Qt.Key.Key_3,
            QtCore.Qt.Key.Key_4,
            QtCore.Qt.Key.Key_5,
            QtCore.Qt.Key.Key_6,
        ]
        try:
            number = numberkeys.index(cast("QtCore.Qt.Key", event.key())) + 1
        except ValueError:
            number = 0
        if event.key() == QtCore.Qt.Key.Key_Return:
            self.enterPressed.emit()
        elif number:
            if not self.getPlayer():
                if number <= len(self.engine.getPlayers()):
                    self.changed.emit()
                    self.playerButtons[number].setChecked(True)

        return super().keyPressEvent(event)

    def updatePlayerOrder(self) -> None:
        """Rebuild the player radio buttons in the current player order."""
        trash = QWidget()
        trash.setLayout(self.playerGroupLayout)

        self.playerButtonGroup = QButtonGroup(self)
        self.playerGroupLayout = QGridLayout(self.playerGroup)
        b = QRadioButton("", self.playerGroup)
        self.playerButtonGroup.addButton(b, 0)
        self.playerButtons = [b]
        b.hide()

        for i, player in enumerate(self.engine.getListPlayers(), 1):
            b = QRadioButton(f"{i}. {player}", self.playerGroup)
            if len(self.engine.getListPlayers()) > 2:
                self.playerGroupLayout.addWidget(b, (i - 1) % 2, (i - 1) // 2)
            else:
                self.playerGroupLayout.addWidget(b, 0, (i - 1) % 2)
            self.playerButtonGroup.addButton(b, i)
            self.playerButtons.append(b)

        self.reset()


class ParchisEntriesDetail(GameRoundsDetail):
    """Rounds-detail panel for Parchis, adding a killer summary table."""

    def __init__(self, engine, parent: QWidget | None = None) -> None:
        super().__init__(engine, parent)
        # self.setStyleSheet("""
        #     QTableView::item:hover {
        #         background: transparent;
        #     }
        #     QTableView::item:selected {
        #         background: transparent;
        #     }
        # """)

    # def initUI(self) -> None:
    #     """Build the base tabs plus the per-kind totals table."""
    #     super().initUI()
    #     self.totalsLabel = QLabel("", self)
    #     self.tableContainerLayout.addWidget(self.totalsLabel)
    #     self.totals = StatsTable(
    #         len(cast("ParchisEngine", self.engine).getEntryKinds()),
    #         len(self.engine.getPlayers()),
    #     )
    #     self.tableContainerLayout.addWidget(self.totals)
    #     self.totals.setHorizontalHeaderLabels(self.engine.getListPlayers())
    #     self.totals.setMaximumHeight(self.totals.sizeHint().height())

    # def retranslateUI(self) -> None:
    #     self.totals.setVerticalHeaderLabels(
    #         [
    #             QCoreApplication.translate("ParchisInputWidget", kind)
    #             for kind in cast("ParchisEngine", self.engine).getEntryKinds()
    #         ]
    #     )
    #     self.totalsLabel.setText(self.tr("Totals"))
    #     super().retranslateUI()
    #     self.updateRound()

    # def resetTotals(self) -> None:
    #     """Clear the totals table back to zeroes with per-kind row colours."""
    #     self.totals.setHorizontalHeaderLabels(self.engine.getListPlayers())
    #     self.totals.clearContents()
    #     for row in range(len(cast("ParchisEngine", self.engine).getEntryKinds())):
    #         # background = self.bgcolors[row]
    #         for col in range(len(self.engine.getListPlayers())):
    #             item = QTableWidgetItem()
    #             item.setFlags(item.flags() ^ QtCore.Qt.ItemFlag.ItemIsEditable)
    #             item.setTextAlignment(
    #                 QtCore.Qt.AlignmentFlag.AlignVCenter
    #                 | QtCore.Qt.AlignmentFlag.AlignCenter
    #             )
    #             item.setBackground(QtGui.QBrush(QtGui.QColor(background)))
    #             item.setForeground(QtGui.QBrush(QtGui.QColor(0, 0, 0)))
    #             item.setText("0")
    #             self.totals.setItem(row, col, item)

    # def updateRound(self) -> None:
    #     """Rebuild the base table and recompute the per-kind totals."""
    #     super().updateRound()
    #     self.resetTotals()
    #     for r in self.engine.getRounds():
    #         self.updateTotal(r)
    #     self.recomputeMaxTotals()

    # def updateTotal(self, entry) -> None:
    #     """Fold one entry's score into its player/kind totals cell."""
    #     kinds = cast("ParchisEngine", self.engine).getEntryKinds()
    #     players = self.engine.getListPlayers()
    #     totalItem = self.totals.item(
    #         kinds.index(entry.getKind()), players.index(entry.getPlayer())
    #     )
    #     if totalItem:
    #         totalItem.setText(str(int(totalItem.text()) + entry.getPlayerScore()))

    # def recomputeMaxTotals(self) -> None:
    #     """Bold the leading player's cell in each kind's totals row."""
    #     kinds = cast("ParchisEngine", self.engine).getEntryKinds()
    #     players = self.engine.getListPlayers()
    #     for row in range(len(kinds)):
    #         maxvalue = 1
    #         for col in range(len(players)):
    #             item = self.totals.item(row, col)
    #             if item:
    #                 total = int(item.text())
    #                 maxvalue = max(maxvalue, total)

    #         for col in range(len(players)):
    #             item = self.totals.item(row, col)
    #             if item:
    #                 font = item.font()
    #                 font.setBold(int(item.text()) == maxvalue)
    #                 item.setFont(font)

    def createRoundTable(self, engine, parent: QWidget | None = None):
        return ParchisRoundTable(self.engine, parent)

    def createRoundPlot(self, engine, parent: QWidget | None = None):
        return ParchisEntriesPlot(self.engine, self)

    def createQSBox(self, parent: QWidget | None = None):
        return ParchisQSTW(
            self.engine.getGame(),  # pyright: ignore[reportArgumentType]
            self.engine.getListPlayers(),
            self,
        )


class ParchisRoundTable(GameRoundTable):
    """Entry-by-entry score table for Parchis, coloured by feature kind."""

    def __init__(self, engine, parent: QWidget | None = None) -> None:
        super().__init__(engine, parent)

    # def insertRound(self, entry: GenericRound) -> None:
    #     """Append a row for ``entry``, highlighting the scoring player's cell."""
    #     centry = cast("ParchisEntry", entry)
    #     kind = cast("str", centry.getKind())
    #     kinds = self.engine.getEntryKinds()
    #     # background = self.bgcolors[kinds.index(kind)]
    #     kind = QCoreApplication.translate("ParchisInputWidget", kind)
    #     i = centry.getNumRound() - 1
    #     self.insertRow(i)
    #     for j, player in enumerate(self.engine.getListPlayers()):
    #         item = QTableWidgetItem()
    #         item.setFlags(item.flags() ^ QtCore.Qt.ItemFlag.ItemIsEditable)
    #         item.setTextAlignment(
    #             QtCore.Qt.AlignmentFlag.AlignVCenter
    #             | QtCore.Qt.AlignmentFlag.AlignCenter
    #         )
    #         item.setBackground(QtGui.QBrush(QtGui.QColor(background)))
    #         item.setForeground(QtGui.QBrush(QtGui.QColor(0, 0, 0)))

    #         if player == centry.getPlayer():
    #             text = f"{centry.getPlayerScore()} ({kind})"
    #             font = item.font()
    #             font.setBold(True)
    #             item.setFont(font)
    #         else:
    #             text = ""
    #         item.setText(text)
    #         self.setItem(i, j, item)
    #     self.scrollToBottom()


class ParchisEntriesPlot(GameRoundPlot):
    """Cumulative score-over-entries plot for Parchis."""

    def updatePlot(self) -> None:
        """Redraw the running-total series, one line per player."""
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
                else:
                    entryscore = 0
                accumscore = scores[player][-1] + entryscore
                scores[player].append(accumscore)

        self.canvas.clearPlotContents()

        for player in self.engine.getListPlayers():
            self.canvas.addSeries(scores[player], player)

        self.canvas._scene.update()


class ParchisQSTW(QuickStatsTW):
    """Quick-stats tab set for Parchis."""

    def initStatsWidgets(self) -> None:
        self.gs = ParchisQSBox(self)
        self.ps = ParchisPQSBox(self)


class ParchisQSBox(GeneralQuickStats):
    """General quick-stats page adding max-kills and max-combo columns."""

    def __init__(self, parent=None) -> None:
        self.game = "Parchis"
        super().__init__(self.game, parent)
        self.matchStatsKeys.append("max_kills")
        self.matchStatsHeaders.append(self.tr("Max Kills"))
        self.matchStatsKeys.append("max_combo")
        self.matchStatsHeaders.append(self.tr("Max Combo"))

        self.playerStatsKeys.append("max_kills")
        self.playerStatsHeaders.append(self.tr("Max Kills"))
        self.playerStatsKeys.append("max_combo")
        self.playerStatsHeaders.append(self.tr("Max Combo"))


class ParchisPQSBox(ParchisQSBox, ParticularQuickStats):
    """Player-filtered variant of the Parchis quick-stats page."""
