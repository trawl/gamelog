"""Catan scoreboard widgets: per-player holdings tracker, round table and plot."""

from __future__ import annotations

from typing import cast

from PySide6 import QtCore, QtGui
from PySide6.QtCore import QCoreApplication, QPoint
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QSizePolicy,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from core.engine.settings import appsettings
from core.ui.game import (
    GameInputWidget,
    GameNotImplementedException,
    GameRoundPlot,
    GameRoundsDetail,
    GameRoundTable,
    GameWidget,
    ScoreSpinBox,
    StatsTable,
)
from games.catan.engine import CatanEngine
from games.catan.model import CatanRound

# Holdings tracked with a counter (the rest are awards held by one player).
COUNTERS = ("settlements", "cities", "vpcards")

# Holding names, translated in the "CatanInputWidget" context.
LABELS = {
    "settlements": "Settlements",
    "cities": "Cities",
    "longestroad": "Longest road",
    "largestarmy": "Largest army",
    "vpcards": "VP cards",
}
QCoreApplication.translate("CatanInputWidget", "Settlements")
QCoreApplication.translate("CatanInputWidget", "Cities")
QCoreApplication.translate("CatanInputWidget", "Longest road")
QCoreApplication.translate("CatanInputWidget", "Largest army")
QCoreApplication.translate("CatanInputWidget", "VP cards")

# Short holding names for the round table, in the "CatanRoundTable" context.
ABBREVIATIONS = {
    "settlements": "S",
    "cities": "C",
    "longestroad": "LR",
    "largestarmy": "LA",
    "vpcards": "VP",
}
QCoreApplication.translate("CatanRoundTable", "S")
QCoreApplication.translate("CatanRoundTable", "C")
QCoreApplication.translate("CatanRoundTable", "LR")
QCoreApplication.translate("CatanRoundTable", "LA")
QCoreApplication.translate("CatanRoundTable", "VP")


def holdingLabel(key: str) -> str:
    return QCoreApplication.translate("CatanInputWidget", LABELS[key])


class CatanWidget(GameWidget):
    """Scoreboard tab for Catan, tracking every player's victory points."""

    def createEngine(self) -> None:
        if self.game != "Catan":
            raise GameNotImplementedException(f"No engine for game {self.game}")
        self.engine = CatanEngine()

    def initUI(self) -> None:
        super().initUI()
        self.retranslateUI()

    def addExtraConfig(self) -> None:
        """Add the target victory points spin box to the match panel."""
        super().addExtraConfig()
        if self.engine.getNumRound() == 1:
            saved_top = int(appsettings["catan_top_score"] or 10)
            cast("CatanEngine", self.engine).setTop(saved_top)
        self.topPointsScoreBox = ScoreSpinBox(self.matchGroup)
        self.topPointsScoreBox.setRange(3, 30)
        self.topPointsScoreBox.setValue(cast("CatanEngine", self.engine).getTop())
        self.topPointsScoreBox.lineEdit().setFocusPolicy(
            QtCore.Qt.FocusPolicy.ClickFocus
        )
        self.topPointsScoreBox.valueChanged.connect(self.changeTop)
        self.topPointsScoreBox.setSizePolicy(
            QSizePolicy.Policy.MinimumExpanding, QSizePolicy.Policy.Maximum
        )
        self.matchGroupLayout.addWidget(
            self.topPointsScoreBox, alignment=QtCore.Qt.AlignmentFlag.AlignLeft
        )

    def createGameInputWidget(self, parent: QWidget | None = None) -> CatanInputWidget:
        return CatanInputWidget(self.engine, parent)

    def createRoundsDetail(self, parent: QWidget | None = None) -> CatanRoundsDetail:
        return CatanRoundsDetail(self.engine, parent)

    def getPlayerExtraInfo(self, player: str) -> dict:
        """Return the holding changes entered for ``player``."""
        return cast("CatanInputWidget", self.gameInput).getChanges()[player]

    def checkPlayerScore(
        self, player: str, score: int, extras: dict | None = None
    ) -> bool:
        # Points can be lost (e.g. a stolen longest road), so any value goes.
        return score is not None

    def commitRoundSanityCheck(self, interactive: bool = False) -> bool:
        """Check that some holding changed and that awards have one holder."""
        gameInput = cast("CatanInputWidget", self.gameInput)
        if not gameInput.hasChanges():
            if interactive:
                QMessageBox.warning(self, self.game, self.tr("Nothing has changed"))
            return False
        states = gameInput.getStates()
        for award in cast("CatanEngine", self.engine).getAwards():
            if sum(state[award] for state in states.values()) > 1:
                msg = self.tr("Only one player can hold {}").format(holdingLabel(award))
                if interactive:
                    QMessageBox.warning(self, self.game, msg)
                return False
        return True

    def updatePanel(self) -> None:
        super().updatePanel()
        self.topPointsScoreBox.setReadOnly(self.engine.getNumRound() > 1)

    def changeTop(self, newtop: int | None) -> None:
        """Apply new target victory points and refresh the plot's limit line."""
        if newtop is None:
            return
        cast("CatanEngine", self.engine).setTop(int(newtop))
        self.detailGroup.updatePlot()


class CatanInputWidget(GameInputWidget):
    """Holdings tracker: one box per player, pre-filled with their holdings."""

    def initUI(self) -> None:
        self.widgetLayout = QGridLayout(self)
        for player in self.engine.getListPlayers():
            piw = CatanPlayerInputWidget(
                player,
                cast("CatanEngine", self.engine),
                self.playerColour(player),
                self,
            )
            self.playerInputList[player] = piw
            piw.changed.connect(self.changed)
            piw.awardClaimed.connect(self.awardClaimed)
        self.placePlayerInputs()
        self.reset()

    def placePlayerInputs(self) -> None:
        """Lay the player boxes out in one row, or two rows for 5+ players."""
        players = self.engine.getListPlayers()
        columns = 3 if len(players) > 4 else len(players)
        for i, player in enumerate(players):
            self.widgetLayout.addWidget(
                self.playerInputList[player], i // columns, i % columns
            )

    def retranslateUI(self) -> None:
        for piw in self.playerInputList.values():
            piw.retranslateUI()

    def reset(self) -> None:
        """Load every player's committed holdings into their box.

        Before the first round the boxes start with the setup-phase holdings,
        so committing it records each player's initial settlements.
        """
        engine = cast("CatanEngine", self.engine)
        for player, piw in self.playerInputList.items():
            committed = engine.getPlayerState(player)
            current = dict(committed)
            if engine.getNumRound() == 1:
                current = engine.getInitialState()
            piw.setState(committed, current)
        self.changed.emit()

    def awardClaimed(self, award: str, player: str) -> None:
        """Take ``award`` away from everyone but ``player``."""
        for other, piw in self.playerInputList.items():
            if other != player:
                piw.releaseAward(award)

    def getStates(self) -> dict[str, dict[str, int]]:
        return {p: piw.getState() for p, piw in self.playerInputList.items()}

    def getChanges(self) -> dict[str, dict[str, int]]:
        return {p: piw.getChanges() for p, piw in self.playerInputList.items()}

    def hasChanges(self) -> bool:
        return any(piw.hasChanges() for piw in self.playerInputList.values())

    # Nobody may have gained points, so this widens the base return to None.
    def getWinner(self) -> str | None:  # pyright: ignore[reportIncompatibleMethodOverride]
        """Return the player gaining the most points this round, if any."""
        winner = None
        maxscore = 0
        for player, score in self.getScores().items():
            if score > maxscore:
                winner = player
                maxscore = score
        return winner

    def updatePlayerOrder(self) -> None:
        for piw in self.playerInputList.values():
            self.widgetLayout.removeWidget(piw)
            piw.setColour(self.playerColour(piw.getPlayer()))
        self.placePlayerInputs()


class CatanCounter(QWidget):
    """A value between a decrement and an increment button."""

    stepped = QtCore.Signal(int)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.layout_ = QHBoxLayout(self)
        self.layout_.setContentsMargins(0, 0, 0, 0)
        self.downButton = QPushButton("−", self)
        self.valueLabel = QLabel("0", self)
        self.upButton = QPushButton("+", self)
        for button in (self.downButton, self.upButton):
            button.setFixedWidth(32)
            button.setFocusPolicy(QtCore.Qt.FocusPolicy.NoFocus)
        self.valueLabel.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.valueLabel.setMinimumWidth(24)
        self.layout_.addWidget(self.downButton)
        self.layout_.addWidget(self.valueLabel)
        self.layout_.addWidget(self.upButton)
        self.downButton.clicked.connect(lambda: self.stepped.emit(-1))
        self.upButton.clicked.connect(lambda: self.stepped.emit(1))

    def setValue(self, value: int, pending: bool = False) -> None:
        """Show ``value``, emphasised when it differs from the committed one."""
        self.valueLabel.setText(str(value))
        weight = "bold" if pending else "normal"
        self.valueLabel.setStyleSheet(f"font-size: 20px; font-weight: {weight};")

    def setStepsEnabled(self, down: bool, up: bool) -> None:
        self.downButton.setEnabled(down)
        self.upButton.setEnabled(up)


class CatanPlayerInputWidget(QGroupBox):
    """One player's holdings: counters, award toggles and a points readout."""

    changed = QtCore.Signal()
    awardClaimed = QtCore.Signal(str, str)

    def __init__(
        self,
        player: str,
        engine: CatanEngine,
        colour: QColor | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.player = player
        self.engine = engine
        self.pcolour = colour if colour else QColor(0, 0, 0)
        self.limits = engine.getLimits()
        self.committed = dict.fromkeys(engine.getComponents(), 0)
        self.state = dict(self.committed)
        self.initUI()

    def initUI(self) -> None:
        self.mainLayout = QVBoxLayout(self)

        self.headerLayout = QHBoxLayout()
        self.mainLayout.addLayout(self.headerLayout)
        self.label = QLabel(self.player, self)
        self.headerLayout.addWidget(self.label)
        self.pointsLabel = QLabel(self)
        self.pointsLabel.setAlignment(
            QtCore.Qt.AlignmentFlag.AlignRight | QtCore.Qt.AlignmentFlag.AlignVCenter
        )
        self.headerLayout.addWidget(self.pointsLabel)

        self.countersLayout = QGridLayout()
        self.mainLayout.addLayout(self.countersLayout)
        self.counterLabels: dict[str, QLabel] = {}
        self.counters: dict[str, CatanCounter] = {}
        for row, key in enumerate(COUNTERS):
            self.counterLabels[key] = QLabel(self)
            self.countersLayout.addWidget(self.counterLabels[key], row, 0)
            self.counters[key] = CatanCounter(self)
            self.counters[key].stepped.connect(
                lambda step, key=key: self.stepCounter(key, step)
            )
            self.countersLayout.addWidget(self.counters[key], row, 1)

        self.awardsLayout = QHBoxLayout()
        self.mainLayout.addLayout(self.awardsLayout)
        self.awardButtons: dict[str, QPushButton] = {}
        for key in self.engine.getAwards():
            button = QPushButton(self)
            button.setCheckable(True)
            button.setFocusPolicy(QtCore.Qt.FocusPolicy.NoFocus)
            button.toggled.connect(
                lambda checked, key=key: self.toggleAward(key, checked)
            )
            self.awardButtons[key] = button
            self.awardsLayout.addWidget(button)

        self.setColour(self.pcolour)
        self.retranslateUI()

    def retranslateUI(self) -> None:
        for key, label in self.counterLabels.items():
            label.setText(holdingLabel(key))
        for key, button in self.awardButtons.items():
            button.setText(holdingLabel(key))

    def setColour(self, colour: QColor) -> None:
        self.pcolour = colour
        r, g, b = colour.red(), colour.green(), colour.blue()
        css = f"font-size: 24px; font-weight: bold; color: rgb({r},{g},{b});"
        self.label.setStyleSheet(css)
        self.pointsLabel.setStyleSheet(css)
        for button in self.awardButtons.values():
            button.setStyleSheet(f"""
                QPushButton {{
                    font-weight: bold;
                    color: rgb({r},{g},{b});
                    border: 1px solid rgba({r},{g},{b},80);
                    border-radius: 6px;
                    padding: 6px 6px;
                    background: transparent;
                }}
                QPushButton:checked {{
                    background: rgb({r},{g},{b});
                    color: white;
                    border: 1px solid rgb({r},{g},{b});
                }}
            """)

    def setState(self, committed: dict[str, int], current: dict[str, int]) -> None:
        """Set the committed holdings and the (possibly edited) current ones."""
        self.committed = dict(committed)
        self.state = dict(current)
        self.updatePanel()

    def stepCounter(self, key: str, step: int) -> None:
        """Change a counter by ``step``; a city replaces one of the settlements."""
        if not self.canStep(key, step):
            return
        self.state[key] += step
        if key == "cities":
            self.state["settlements"] -= step
        self.updatePanel()
        self.changed.emit()

    def canStep(self, key: str, step: int) -> bool:
        """Whether a counter can change by ``step`` within the piece limits."""
        value = self.state[key] + step
        if not 0 <= value <= self.limits[key]:
            return False
        if key == "cities":
            settlements = self.state["settlements"] - step
            return 0 <= settlements <= self.limits["settlements"]
        return True

    def toggleAward(self, key: str, checked: bool) -> None:
        """Grant or drop an award, claiming it from any other holder."""
        self.state[key] = int(checked)
        if checked:
            self.awardClaimed.emit(key, self.player)
        self.updatePanel()
        self.changed.emit()

    def releaseAward(self, key: str) -> None:
        """Drop an award another player has just claimed."""
        if self.state[key]:
            self.awardButtons[key].setChecked(False)

    def updatePanel(self) -> None:
        """Refresh counters, award toggles and the points readout."""
        for key, counter in self.counters.items():
            counter.setValue(self.state[key], self.state[key] != self.committed[key])
            counter.setStepsEnabled(self.canStep(key, -1), self.canStep(key, 1))
        for key, button in self.awardButtons.items():
            button.blockSignals(True)
            button.setChecked(bool(self.state[key]))
            button.blockSignals(False)
        points = self.engine.victoryPoints(self.state)
        delta = self.getScore()
        text = str(points)
        if delta:
            text += f" ({delta:+d})"
        self.pointsLabel.setText(text)

    def getPlayer(self) -> str:
        return self.player

    def getState(self) -> dict[str, int]:
        return dict(self.state)

    def getChanges(self) -> dict[str, int]:
        return {key: value - self.committed[key] for key, value in self.state.items()}

    def hasChanges(self) -> bool:
        return self.state != self.committed

    def getScore(self) -> int:
        """Return the victory points gained (or lost) by the pending changes."""
        return self.engine.victoryPoints(self.getChanges())


class CatanRoundsDetail(GameRoundsDetail):
    """Rounds detail panel for Catan, adding a per-player holdings table."""

    def __init__(self, engine, parent: QWidget | None = None) -> None:
        self.bgcolors = [0xCCFF99, 0xFFCC99]
        super().__init__(engine, parent)

    def initUI(self) -> None:
        """Build the base tabs plus the holdings totals table."""
        super().initUI()
        self.totalsLabel = QLabel("", self)
        self.tableContainerLayout.addWidget(self.totalsLabel)
        self.totals = StatsTable(
            len(cast("CatanEngine", self.engine).getComponents()),
            len(self.engine.getPlayers()),
        )
        self.totals.setEditTriggers(StatsTable.EditTrigger.NoEditTriggers)
        self.tableContainerLayout.addWidget(self.totals)
        self.totals.setMaximumHeight(self.totals.sizeHint().height())

    def retranslateUI(self) -> None:
        self.totals.setVerticalHeaderLabels(
            [
                holdingLabel(key)
                for key in cast("CatanEngine", self.engine).getComponents()
            ]
        )
        self.totalsLabel.setText(self.tr("Totals"))
        super().retranslateUI()

    def updateRound(self) -> None:
        """Rebuild the base table and the holdings totals."""
        super().updateRound()
        engine = cast("CatanEngine", self.engine)
        players = engine.getListPlayers()
        self.totals.setHorizontalHeaderLabels(players)
        self.totals.clearContents()
        for col, player in enumerate(players):
            state = engine.getPlayerState(player)
            for row, key in enumerate(engine.getComponents()):
                if key in engine.getAwards():
                    text = "✓" if state[key] else ""
                else:
                    text = str(state[key])
                item = QTableWidgetItem(text)
                item.setTextAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
                self.totals.setItem(row, col, item)

    def createRoundTable(self, engine, parent: QWidget | None = None):
        return CatanRoundTable(self.engine, self.bgcolors, parent)

    def createRoundPlot(self, engine, parent: QWidget | None = None):
        return CatanRoundPlot(self.engine, self)


class CatanRoundTable(GameRoundTable):
    """Per-round table showing each player's point change and what caused it."""

    def __init__(self, engine, bgcolors, parent: QWidget | None = None) -> None:
        self.bgcolors = bgcolors
        super().__init__(engine, parent)

    def openTableMenu(self, position: QPoint) -> None:
        # Holdings build on each other, so only the last round can be deleted.
        if self.indexAt(position).row() != self.rowCount() - 1:
            return
        super().openTableMenu(position)

    def insertRound(self, r) -> None:
        """Append a row for round ``r`` with each player's changes."""
        rnd = cast("CatanRound", r)
        i = rnd.getNumRound() - 1
        self.insertRow(i)
        for j, player in enumerate(self.engine.getListPlayers()):
            item = QTableWidgetItem()
            item.setFlags(item.flags() ^ QtCore.Qt.ItemFlag.ItemIsEditable)
            item.setTextAlignment(
                QtCore.Qt.AlignmentFlag.AlignVCenter
                | QtCore.Qt.AlignmentFlag.AlignCenter
            )
            changes = rnd.getChanges(player)
            parts = [
                f"{QCoreApplication.translate('CatanRoundTable', ABBREVIATIONS[key])}"
                f"{value:+d}"
                for key, value in changes.items()
                if value
            ]
            score = rnd.getPlayerScore(player)
            text = ""
            if parts:
                text = f"{score:+d} ({' '.join(parts)})"
                item.setToolTip(
                    "\n".join(
                        f"{holdingLabel(key)}: {value:+d}"
                        for key, value in changes.items()
                        if value
                    )
                )
            if score:
                background = self.bgcolors[0] if score > 0 else self.bgcolors[1]
                item.setBackground(QtGui.QBrush(QtGui.QColor(background)))
                item.setForeground(QtGui.QBrush(QtGui.QColor(0, 0, 0)))
            item.setText(text)
            self.setItem(i, j, item)
        self.scrollToBottom()


class CatanRoundPlot(GameRoundPlot):
    """Victory points plot with the target points drawn as a limit line."""

    def updatePlot(self) -> None:
        super().updatePlot()
        if not self.isPlotInited():
            return
        scores = {}
        for player in self.engine.getPlayers():
            scores[player] = [0]

        for rnd in self.engine.getRounds():
            for player in self.engine.getPlayers():
                accumscore = scores[player][-1] + rnd.getPlayerScore(player)
                scores[player].append(accumscore)

        self.canvas.clearPlotContents()
        self.canvas.addLimit(self.engine.getTop())
        for player in self.engine.getListPlayers():
            self.canvas.addSeries(scores[player], player)
