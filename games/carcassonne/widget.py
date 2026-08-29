"""Qt scoreboard widgets for Carcassonne: entry input, table, plot and stats."""

from __future__ import annotations

from typing import cast

from PySide6 import QtCore, QtGui
from PySide6.QtCore import QCoreApplication
from PySide6.QtGui import QKeyEvent
from PySide6.QtWidgets import (
    QButtonGroup,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QRadioButton,
    QSizePolicy,
    QTableWidgetItem,
    QWidget,
)

from core.model.base import GenericRound
from core.ui.game import (
    GameInputWidget,
    GameNotImplementedException,
    GameRoundPlot,
    GameRoundsDetail,
    GameRoundTable,
    GameWidget,
    QuickStatsTW,
    ScoreSpinBox,
)
from core.ui.gamestats import GeneralQuickStats, ParticularQuickStats, StatsTable
from games.carcassonne.engine import CarcassonneEngine, CarcassonneStatsEngine
from games.carcassonne.model import CarcassonneEntry


class CarcassonneWidget(GameWidget):
    """Scoreboard tab for Carcassonne, scored one feature entry at a time."""

    bgcolors = (0xFFCC99, 0xCCCCCC, 0xFFFF99, 0xCCFF99, 0xCCFFCC, 0xFFB6C1)

    def createEngine(self) -> None:
        if self.game != "Carcassonne":
            raise GameNotImplementedException(f"No engine for game {self.game}")
        self.engine = CarcassonneEngine()

    def initUI(self) -> None:
        """Build the scoreboard and dock the commit/undo buttons into the input."""
        super().initUI()
        if not self.gameInput:
            self.gameInput = self.createGameInputWidget(self)

        self.commitRoundButton.setSizePolicy(
            QSizePolicy.Policy.MinimumExpanding, QSizePolicy.Policy.Preferred
        )
        self.undoButton.setSizePolicy(
            QSizePolicy.Policy.MinimumExpanding, QSizePolicy.Policy.Preferred
        )
        self.gameInput.placeCommitButton(self.commitRoundButton)
        self.gameInput.placeUndoButton(self.undoButton)

        self.retranslateUI()
        QtCore.QTimer.singleShot(1000, self.gameInput.setFocus)

    def createGameInputWidget(
        self, parent: QWidget | None = None
    ) -> CarcassonneInputWidget:
        return CarcassonneInputWidget(self.engine, self.bgcolors, parent)

    def createRoundsDetail(
        self, parent: QWidget | None = None
    ) -> CarcassonneEntriesDetail:
        return CarcassonneEntriesDetail(self.engine, self.bgcolors, parent)

    # def retranslateUI(self):
    #     super().retranslateUI()
    #     self.commitRoundButton.setText("↵")
    #     self.undoButton.setText("⎌")
    #     font = self.commitRoundButton.font()
    #     font.setBold(True)
    #     self.commitRoundButton.setFont(font)
    #     self.gameInput.retranslateUI()
    #     self.detailGroup.retranslateUI()

    def getPlayerExtraInfo(self, player: str) -> dict:
        """Return the selected feature kind for the current entry, if any."""
        kind = self.gameInput.getKind()
        if kind:
            return {"kind": kind}
        else:
            return {}

    def checkPlayerScore(
        self, player: str, score: int, extras: dict | None = None
    ) -> bool:
        return score > 0

    def commitRoundSanityCheck(self, interactive: bool = False) -> bool:
        """Check that a player, a kind and a valid score are all selected."""
        player = self.gameInput.getPlayer()
        kind = self.gameInput.getKind()
        score = self.gameInput.getScore()
        if player == "":
            msg = self.tr("You must select a player")
            if interactive:
                QMessageBox.warning(self, self.game, msg)
            return False

        if kind == "":
            msg = self.tr("You must select a kind")
            if interactive:
                QMessageBox.warning(self, self.game, msg)
            return False

        if not self.checkPlayerScore(player, score):
            msg = self.tr(f"{player} score is not valid")
            if interactive:
                QMessageBox.warning(self, self.game, msg)
            return False
        return True

    def commitRound(self) -> None:
        """Record the selected player's scoring entry and refresh the board."""
        if not self.commitRoundSanityCheck(interactive=True):
            return
        player = self.gameInput.getPlayer()
        kind = self.gameInput.getKind()
        score = self.gameInput.getScore()
        try:
            self.playerGroupBox[self.engine.getDealer()].unsetDealer()
        except KeyError:
            pass
        cast("CarcassonneEngine", self.engine).addEntry(player, score, {"kind": kind})
        self.engine.printStats()
        self.updatePanel()


class CarcassonneInputWidget(GameInputWidget):
    """Player/kind/score selectors for entering a single Carcassonne score."""

    enterPressed = QtCore.Signal()

    QCoreApplication.translate("CarcassonneInputWidget", "City")
    QCoreApplication.translate("CarcassonneInputWidget", "Road")
    QCoreApplication.translate("CarcassonneInputWidget", "Cloister")
    QCoreApplication.translate("CarcassonneInputWidget", "Field")
    QCoreApplication.translate("CarcassonneInputWidget", "Goods")
    QCoreApplication.translate("CarcassonneInputWidget", "Fair")

    def __init__(self, engine, bgcolors, parent) -> None:
        super().__init__(engine, parent)
        self.bgcolors = bgcolors

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

        self.kindGroup = QGroupBox(self)
        self.widgetLayout.addWidget(self.kindGroup)
        self.kindButtonGroup = QButtonGroup(self)
        self.kindGroupLayout = QGridLayout(self.kindGroup)

        b = QRadioButton("", self.kindGroup)
        #        self.kindGroupLayout.addWidget(b)
        self.kindButtonGroup.addButton(b, 0)
        self.kindButtons = [b]
        b.hide()

        self.scoreSpinBox = ScoreSpinBox(self)
        # self.scoreSpinBox.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        # self.scoreSpinBox.setMaximumWidth(120)
        self.scoreSpinBox.setRange(0, 300)
        self.scoreSpinBox.valueChanged.connect(self.changed)

        for i, kind in enumerate(
            cast("CarcassonneEngine", self.engine).getEntryKinds(), 1
        ):
            lbl = self.tr(kind)
            b = QRadioButton(f"{i}. {lbl}", self.kindGroup)
            self.kindGroupLayout.addWidget(b, (i - 1) % 2, (i - 1) // 2)
            self.kindButtonGroup.addButton(b, i)
            b.clicked.connect(lambda x: self.scoreSpinBox.setFocus())
            self.kindButtons.append(b)

        self.kindButtons[3].toggled.connect(self.setCloisterPoints)
        self.kindButtons[5].toggled.connect(self.setGoodsPoints)
        self.kindButtons[6].toggled.connect(self.setFairPoints)

        self.scoreGroup = QGroupBox(self)
        self.widgetLayout.addWidget(self.scoreGroup)
        self.scoreGroupLayout = QHBoxLayout(self.scoreGroup)

        self.scoreGroupLayout.addWidget(self.scoreSpinBox)

        self.reset()
        self.retranslateUI()

    def retranslateUI(self) -> None:
        self.playerGroup.setTitle(self.tr("Select Player"))
        self.kindGroup.setTitle(self.tr("Select kind of entry"))
        self.scoreGroup.setTitle(self.tr("Points"))
        for i, kind in enumerate(
            cast("CarcassonneEngine", self.engine).getEntryKinds(), 1
        ):
            text = self.tr(kind)
            self.kindButtons[i].setText(f"{i}. {text}")

    def placeCommitButton(self, cb) -> None:
        self.scoreGroupLayout.addWidget(cb, 2)

    def placeUndoButton(self, ub) -> None:
        self.scoreGroupLayout.addWidget(ub, 1)

    def getPlayer(self) -> str:
        """Return the selected player's name, or ``""`` if none is selected."""
        pid = self.playerButtonGroup.checkedId()
        if not pid:
            return ""
        player = self.engine.getListPlayers()[pid - 1]
        return str(player)

    def getKind(self) -> str:
        """Return the selected feature kind, or ``""`` if none is selected."""
        cid = self.kindButtonGroup.checkedId()
        if not cid:
            return ""
        kind = cast("CarcassonneEngine", self.engine).getEntryKinds()[cid - 1]
        return str(kind)

    def getScore(self) -> int:
        return cast("int", self.scoreSpinBox.value())

    def reset(self) -> None:
        """Clear the player/kind selection and reset the score to zero."""
        self.playerButtons[0].setChecked(True)
        self.kindButtons[0].setChecked(True)
        self.scoreSpinBox.setValue(0)
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
            QtCore.Qt.Key.Key_7,
            QtCore.Qt.Key.Key_8,
            QtCore.Qt.Key.Key_9,
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
            elif not self.getKind() and number <= len(
                cast("CarcassonneEngine", self.engine).getEntryKinds()
            ):
                self.changed.emit()
                self.kindButtons[number].setChecked(True)
                self.scoreSpinBox.setFocus()

        return super().keyPressEvent(event)

    def setCloisterPoints(self, doit: bool) -> None:
        """Preset the score to a full cloister (9) while that kind is selected."""
        self.changed.emit()
        if doit:
            self.scoreSpinBox.setValue(9)
            self.scoreSpinBox.setMaximum(9)
            # self.scoreSpinBox.lineEdit().selectAll()
        else:
            self.scoreSpinBox.setValue(0)
            self.scoreSpinBox.setMaximum(300)

    def setGoodsPoints(self, doit: bool) -> None:
        """Lock the score to the fixed Goods value (10) while selected."""
        self.changed.emit()
        if doit:
            self.scoreSpinBox.setValue(10)
            self.scoreSpinBox.setReadOnly(True)

        else:
            self.scoreSpinBox.setReadOnly(False)
            self.scoreSpinBox.setValue(0)

    def setFairPoints(self, doit: bool) -> None:
        """Lock the score to the fixed Fair value (5) while selected."""
        self.changed.emit()
        if doit:
            self.scoreSpinBox.setValue(5)
            self.scoreSpinBox.setReadOnly(True)

        else:
            self.scoreSpinBox.setReadOnly(False)
            self.scoreSpinBox.setValue(0)

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


class CarcassonneEntriesDetail(GameRoundsDetail):
    """Rounds-detail panel for Carcassonne, adding a per-kind totals table."""

    def __init__(self, engine, bgcolors, parent: QWidget | None = None) -> None:
        self.bgcolors = bgcolors
        super().__init__(engine, parent)
        self.setStyleSheet("""
            QTableView::item:hover {
                background: transparent;
            }
            QTableView::item:selected {
                background: transparent;
            }
        """)

    def initUI(self) -> None:
        """Build the base tabs plus the per-kind totals table."""
        super().initUI()
        self.totalsLabel = QLabel("", self)
        self.tableContainerLayout.addWidget(self.totalsLabel)
        self.totals = StatsTable(
            len(cast("CarcassonneEngine", self.engine).getEntryKinds()),
            len(self.engine.getPlayers()),
        )
        self.tableContainerLayout.addWidget(self.totals)
        self.totals.setHorizontalHeaderLabels(self.engine.getListPlayers())
        self.totals.setMaximumHeight(self.totals.sizeHint().height())

    def retranslateUI(self) -> None:
        self.totals.setVerticalHeaderLabels(
            [
                QCoreApplication.translate("CarcassonneInputWidget", kind)
                for kind in cast("CarcassonneEngine", self.engine).getEntryKinds()
            ]
        )
        self.totalsLabel.setText(self.tr("Totals"))
        super().retranslateUI()
        self.updateRound()

    def resetTotals(self) -> None:
        """Clear the totals table back to zeroes with per-kind row colours."""
        self.totals.setHorizontalHeaderLabels(self.engine.getListPlayers())
        self.totals.clearContents()
        for row in range(len(cast("CarcassonneEngine", self.engine).getEntryKinds())):
            background = self.bgcolors[row]
            for col in range(len(self.engine.getListPlayers())):
                item = QTableWidgetItem()
                item.setFlags(item.flags() ^ QtCore.Qt.ItemFlag.ItemIsEditable)
                item.setTextAlignment(
                    QtCore.Qt.AlignmentFlag.AlignVCenter
                    | QtCore.Qt.AlignmentFlag.AlignCenter
                )
                item.setBackground(QtGui.QBrush(QtGui.QColor(background)))
                item.setForeground(QtGui.QBrush(QtGui.QColor(0, 0, 0)))
                item.setText("0")
                self.totals.setItem(row, col, item)

    def updateRound(self) -> None:
        """Rebuild the base table and recompute the per-kind totals."""
        super().updateRound()
        self.resetTotals()
        for r in self.engine.getRounds():
            self.updateTotal(r)
        self.recomputeMaxTotals()

    def updateTotal(self, entry) -> None:
        """Fold one entry's score into its player/kind totals cell."""
        kinds = cast("CarcassonneEngine", self.engine).getEntryKinds()
        players = self.engine.getListPlayers()
        totalItem = self.totals.item(
            kinds.index(entry.getKind()), players.index(entry.getPlayer())
        )
        if totalItem:
            totalItem.setText(str(int(totalItem.text()) + entry.getPlayerScore()))

    def recomputeMaxTotals(self) -> None:
        """Bold the leading player's cell in each kind's totals row."""
        kinds = cast("CarcassonneEngine", self.engine).getEntryKinds()
        players = self.engine.getListPlayers()
        for row in range(len(kinds)):
            maxvalue = 1
            for col in range(len(players)):
                item = self.totals.item(row, col)
                if item:
                    total = int(item.text())
                    maxvalue = max(maxvalue, total)

            for col in range(len(players)):
                item = self.totals.item(row, col)
                if item:
                    font = item.font()
                    font.setBold(int(item.text()) == maxvalue)
                    item.setFont(font)

    def createRoundTable(self, engine, parent: QWidget | None = None):
        return CarcassonneRoundTable(self.engine, self.bgcolors, parent)

    def createRoundPlot(self, engine, parent: QWidget | None = None):
        return CarcassonneEntriesPlot(self.engine, self)

    def createQSBox(self, parent: QWidget | None = None):
        return CarcassonneQSTW(
            self.engine.getGame(),  # pyright: ignore[reportArgumentType]
            self.engine.getListPlayers(),
            self,
        )


class CarcassonneRoundTable(GameRoundTable):
    """Entry-by-entry score table for Carcassonne, coloured by feature kind."""

    def __init__(self, engine, bgcolors, parent: QWidget | None = None) -> None:
        self.bgcolors = bgcolors
        super().__init__(engine, parent)

    def insertRound(self, entry: GenericRound) -> None:
        """Append a row for ``entry``, highlighting the scoring player's cell."""
        centry = cast("CarcassonneEntry", entry)
        kind = cast("str", centry.getKind())
        kinds = self.engine.getEntryKinds()
        background = self.bgcolors[kinds.index(kind)]
        kind = QCoreApplication.translate("CarcassonneInputWidget", kind)
        i = centry.getNumRound() - 1
        self.insertRow(i)
        for j, player in enumerate(self.engine.getListPlayers()):
            item = QTableWidgetItem()
            item.setFlags(item.flags() ^ QtCore.Qt.ItemFlag.ItemIsEditable)
            item.setTextAlignment(
                QtCore.Qt.AlignmentFlag.AlignVCenter
                | QtCore.Qt.AlignmentFlag.AlignCenter
            )
            item.setBackground(QtGui.QBrush(QtGui.QColor(background)))
            item.setForeground(QtGui.QBrush(QtGui.QColor(0, 0, 0)))

            if player == centry.getPlayer():
                text = f"{centry.getPlayerScore()} ({kind})"
                font = item.font()
                font.setBold(True)
                item.setFont(font)
            else:
                text = ""
            item.setText(text)
            self.setItem(i, j, item)
        self.scrollToBottom()


class CarcassonneEntriesPlot(GameRoundPlot):
    """Cumulative score-over-entries plot for Carcassonne."""

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


class CarcassonneQSTW(QuickStatsTW):
    """Quick-stats tab set for Carcassonne."""

    def initStatsWidgets(self) -> None:
        self.gs = CarcassonneQSBox(self)
        self.ps = CarcassonnePQSBox(self)


class CarcassonneQSBox(GeneralQuickStats):
    """General quick-stats page adding Carcassonne single/match kind records."""

    def __init__(self, parent=None) -> None:
        self.game = "Carcassonne"
        super().__init__(self.game, parent)

    def initUI(self) -> None:
        """Insert the individual- and match-record tables into the layout."""
        self.singleRecordsLabel = QLabel(self)
        self.singleRecordsTable = StatsTable(self)
        self.matchRecordsLabel = QLabel(self)
        self.matchRecordsTable = StatsTable(self)

        super().initUI()
        index = self.widgetLayout.count() - 1
        self.widgetLayout.insertWidget(index, self.singleRecordsLabel)
        self.widgetLayout.insertWidget(index + 1, self.singleRecordsTable)
        self.widgetLayout.insertWidget(index + 2, self.matchRecordsLabel)
        self.widgetLayout.insertWidget(index + 3, self.matchRecordsTable)
        self.singleRecordsLabel.setStyleSheet(self.titlecss)
        self.matchRecordsLabel.setStyleSheet(self.titlecss)

    def retranslateUI(self) -> None:
        self.singleRecordsLabel.setText(self.tr("Individual Records"))
        self.matchRecordsLabel.setText(self.tr("Match Records"))
        super().retranslateUI()

    def updateContent(self, game=None) -> None:
        """Reload and localise the per-kind record tables from the stats engine."""
        super().updateContent(self.game)
        singleRecordStats = cast(
            "CarcassonneStatsEngine", self.stats
        ).getSingleKindRecords()
        matchRecordStats = cast(
            "CarcassonneStatsEngine", self.stats
        ).getMatchKindRecords()  # pyright: ignore[reportAttributeAccessIssue]

        if not singleRecordStats:
            self.singleRecordsLabel.hide()
        else:
            self.singleRecordsLabel.show()

        if not matchRecordStats:
            self.matchRecordsLabel.hide()
        else:
            self.matchRecordsLabel.show()

        for row in singleRecordStats:
            row["record"] = self.tr(row["record"])

        for row in matchRecordStats:
            row["record"] = self.tr(row["record"])

        keys = ["points", "player", "date"]
        headers = [
            self.tr("Record"),
            self.tr("Player"),
            self.tr("Date"),
        ]
        self.updateTable(
            self.singleRecordsTable, singleRecordStats, keys, "record", headers
        )
        self.updateTable(
            self.matchRecordsTable, matchRecordStats, keys, "record", headers
        )


class CarcassonnePQSBox(CarcassonneQSBox, ParticularQuickStats):
    """Player-filtered variant of the Carcassonne quick-stats page."""
