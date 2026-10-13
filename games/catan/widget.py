"""Catan scoreboard widgets: per-player holdings tracker, round table and plot."""

from __future__ import annotations

from typing import cast

from PySide6 import QtCore, QtGui
from PySide6.QtCore import QCoreApplication, QPoint, QRectF
from PySide6.QtGui import (
    QColor,
    QFont,
    QPainter,
    QPen,
)
from PySide6.QtWidgets import (
    QApplication,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QStyle,
    QStyledItemDelegate,
    QStyleOptionViewItem,
    QTableWidgetItem,
    QWidget,
)

from core.ui.game import (
    ColourBonusButton,
    ColourIconHeader,
    GameInputWidget,
    GameNotImplementedException,
    GameRoundPlot,
    GameRoundsDetail,
    GameRoundTable,
    GameWidget,
    StatsTable,
    paintColourIcon,
)
from games.catan.engine import CatanEngine
from games.catan.model import CatanRound

# The colours of the pieces in the box (white drawn grey, to show on any theme).
_CATAN_COLOURS = [
    QColor(243, 124, 33),  # Orange
    QColor(150, 150, 150),  # White
    QColor(220, 30, 30),  # Red
    QColor(50, 100, 210),  # Blue
    QColor(0, 150, 60),  # Green
    QColor(140, 80, 200),  # Purple
    QColor(150, 95, 45),  # Brown
]

# Holdings tracked with a counter (the rest are awards held by one player).
COUNTERS = ("settlements", "cities", "vpcards")

# Icon of the button tracking each holding.
ICONS = {
    "settlements": "catan_settlement",
    "cities": "catan_city",
    "vpcards": "catan_vp",
    "longestroad": "catan_road",
    "largestarmy": "catan_army",
}

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


def holdingLabel(key: str) -> str:
    return QCoreApplication.translate("CatanInputWidget", LABELS[key])


class CatanWidget(GameWidget):
    """Scoreboard tab for Catan, tracking every player's victory points."""

    player_colours = _CATAN_COLOURS

    def createEngine(self) -> None:
        if self.game != "Catan":
            raise GameNotImplementedException(f"No engine for game {self.game}")
        self.engine = CatanEngine()

    def initUI(self) -> None:
        """Build the board; every edit of the holdings is committed at once."""
        super().initUI()
        self.commitRoundButton.hide()
        cast("CatanInputWidget", self.gameInput).edited.connect(self.autoCommit)
        self.retranslateUI()

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
            return False
        states = gameInput.getStates()
        awards = cast("CatanEngine", self.engine).getAwards()
        return all(sum(state[a] for state in states.values()) <= 1 for a in awards)

    def autoCommit(self) -> None:
        """Commit the holdings as soon as they are edited."""
        if self.commitRoundSanityCheck() and not self.engine.getWinner():
            self.commitRound()

    def undoCommit(self) -> None:
        """Roll back the last change without asking: edits commit instantly,
        so undoing is the everyday way to fix a slip."""
        if not self.engine.getRounds():
            return
        self.engine.deleteRound(len(self.engine.getRounds()))
        self.updatePanel()

    def setRoundTitle(self) -> None:
        # Every edit is a round, so a round number would mean nothing.
        self.roundTitleLabel.setText(self.engine.getGame() or "")


class CatanInputWidget(GameInputWidget):
    """Holdings tracker: one box per player, pre-filled with their holdings.

    ``edited`` is emitted once per user edit, after any award has changed
    hands, so the whole edit can be committed as a single round.
    """

    player_colours = _CATAN_COLOURS
    edited = QtCore.Signal()

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
            piw.edited.connect(self.edited)
            piw.awardClaimed.connect(self.awardClaimed)
        self.placePlayerInputs()
        self.reset()

    def placePlayerInputs(self) -> None:
        """Lay the player boxes out in rows of at most three, as even as possible.

        Up to 3 players share one row; 4 make two rows of 2, 5 a row of 3 and
        one of 2, and 6 two rows of 3.
        """
        players = self.engine.getListPlayers()
        rows = -(-len(players) // 3)
        columns = -(-len(players) // rows)
        for i, player in enumerate(players):
            self.widgetLayout.addWidget(
                self.playerInputList[player], i // columns, i % columns
            )

    def retranslateUI(self) -> None:
        for piw in self.playerInputList.values():
            piw.retranslateUI()

    def reset(self) -> None:
        """Load every player's committed holdings into their box."""
        engine = cast("CatanEngine", self.engine)
        for player, piw in self.playerInputList.items():
            state = engine.getPlayerState(player)
            piw.setState(state, state)
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


class CatanBonusButton(ColourBonusButton):
    """Colour bonus button showing how many of a piece a player holds.

    A left click asks for one more and a right click for one less; the owner
    decides whether the step is allowed and sets the resulting value.
    """

    stepped = QtCore.Signal(int)

    def __init__(
        self,
        bonus_name: str,
        maximum: int = 1,
        colour: QColor | None = None,
        size: int = 48,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(bonus_name, maximum, colour, size, parent)
        self.setFocusPolicy(QtCore.Qt.FocusPolicy.NoFocus)
        self.clicked.disconnect(self.plusone)
        self.clicked.connect(lambda: self.stepped.emit(1))

    def minusone(self) -> None:
        self.stepped.emit(-1)


class CatanPlayerInputWidget(QGroupBox):
    """One player's holdings: counters and award toggles, titled by the player."""

    changed = QtCore.Signal()
    edited = QtCore.Signal()
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
        self.setTitle(self.player)
        self.buttonsLayout = QHBoxLayout(self)
        self.bonusButtons: dict[str, CatanBonusButton] = {}
        for key in self.engine.getComponents():
            button = CatanBonusButton(
                ICONS[key], self.limits[key], self.pcolour, 48, self
            )
            if key in COUNTERS:
                button.stepped.connect(
                    lambda step, key=key: self.stepCounter(key, step)
                )
            else:
                button.stepped.connect(lambda _, key=key: self.toggleAward(key))
            self.bonusButtons[key] = button
            self.buttonsLayout.addWidget(button)

        self.setColour(self.pcolour)
        self.retranslateUI()

    def retranslateUI(self) -> None:
        for key, button in self.bonusButtons.items():
            button.setToolTip(holdingLabel(key))

    def setColour(self, colour: QColor) -> None:
        self.pcolour = colour
        r, g, b = colour.red(), colour.green(), colour.blue()
        self.setStyleSheet(f"""
            QGroupBox {{ font-size: 24px; font-weight: bold; color: rgb({r},{g},{b}); }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                subcontrol-position: top center;
                padding: 0 10px;
                background-color: transparent;
            }}
        """)
        for button in self.bonusButtons.values():
            button.setColour(colour)

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
        self.edited.emit()

    def canStep(self, key: str, step: int) -> bool:
        """Whether a counter can change by ``step`` within the piece limits."""
        value = self.state[key] + step
        if not 0 <= value <= self.limits[key]:
            return False
        if key == "cities":
            settlements = self.state["settlements"] - step
            return 0 <= settlements <= self.limits["settlements"]
        return True

    def toggleAward(self, key: str) -> None:
        """Grant or drop an award, claiming it from any other holder."""
        self.setAward(key, not self.state[key])
        self.edited.emit()

    def setAward(self, key: str, held: bool) -> None:
        """Grant or drop an award, claiming it from any other holder."""
        if self.state[key] == int(held):
            return
        self.state[key] = int(held)
        if held:
            self.awardClaimed.emit(key, self.player)
        self.updatePanel()
        self.changed.emit()

    def releaseAward(self, key: str) -> None:
        """Drop an award another player has just claimed."""
        self.setAward(key, False)

    def updatePanel(self) -> None:
        """Refresh the holding buttons."""
        for key, button in self.bonusButtons.items():
            button.setValue(self.state[key])

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
        # Rows are labelled by their piece, in a neutral colour.
        components = cast("CatanEngine", self.engine).getComponents()
        self.totals.setVerticalHeader(
            ColourIconHeader([ICONS[key] for key in components], self.totals)
        )
        for row in range(len(components)):
            self.totals.setVerticalHeaderItem(row, QTableWidgetItem(""))
        self.tableContainerLayout.addWidget(self.totals)
        self.totals.setMaximumHeight(self.totals.sizeHint().height())

    def retranslateUI(self) -> None:
        for row, key in enumerate(cast("CatanEngine", self.engine).getComponents()):
            header = self.totals.verticalHeaderItem(row)
            if header:
                header.setToolTip(holdingLabel(key))
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


# Item data role holding a round-table cell's (score, colour, changes) to draw.
CHANGES_ROLE = QtCore.Qt.ItemDataRole.UserRole + 1


def shownChanges(changes: dict[str, int]) -> dict[str, int]:
    """Return the changes worth showing: a city upgrade is shown as the city
    alone, without the settlement it replaced."""
    shown = dict(changes)
    shown["settlements"] = changes["settlements"] + changes["cities"]
    return {key: value for key, value in shown.items() if value}


class CatanChangesDelegate(QStyledItemDelegate):
    """Paints a round-table cell as the point change followed by piece icons.

    A gained piece shows solid, as on a held button; a lost one shows empty
    and crossed out; several of a kind are preceded by their count.
    """

    def paint(self, painter: QPainter, option, index) -> None:
        data = index.data(CHANGES_ROLE)
        if not data:
            super().paint(painter, option, index)
            return
        score, colour, changes = data
        opt = QStyleOptionViewItem(option)
        self.initStyleOption(opt, index)
        opt.text = ""
        style = opt.widget.style() if opt.widget else QApplication.style()
        style.drawControl(
            QStyle.ControlElement.CE_ItemViewItem, opt, painter, opt.widget
        )

        foreground = index.data(QtCore.Qt.ItemDataRole.ForegroundRole)
        textColour = foreground.color() if foreground else opt.palette.text().color()
        rect = QRectF(opt.rect)
        iconSize = min(rect.height() - 6, 22)
        bold = QFont(opt.font)
        bold.setBold(True)
        parts = self._parts(score, changes)
        metrics = QtGui.QFontMetricsF(bold)
        gap = 4
        width = sum(
            metrics.horizontalAdvance(p) if isinstance(p, str) else iconSize
            for p in parts
        ) + gap * (len(parts) - 1)

        painter.save()
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setFont(bold)
        painter.setPen(textColour)
        x = rect.center().x() - width / 2
        for part in parts:
            if isinstance(part, str):
                w = metrics.horizontalAdvance(part)
                painter.drawText(
                    QRectF(x, rect.top(), w, rect.height()),
                    QtCore.Qt.AlignmentFlag.AlignCenter,
                    part,
                )
            else:
                w = iconSize
                key, gained = part
                icon = QRectF(x, rect.center().y() - iconSize / 2, iconSize, iconSize)
                paintColourIcon(painter, icon, ICONS[key], colour, gained)
                if not gained:
                    painter.setPen(QPen(textColour, 2))
                    painter.drawLine(icon.bottomLeft(), icon.topRight())
            x += w + gap
        painter.restore()

    @staticmethod
    def _parts(score: int, changes: dict[str, int]) -> list:
        """Lay out a cell: the score text, then per change an optional count
        (text) and the piece (a ``(key, gained)`` tuple)."""
        parts: list = [f"{score:+d}"]
        for key, value in changes.items():
            if abs(value) > 1:
                parts.append(str(abs(value)))
            parts.append((key, value > 0))
        return parts


class CatanRoundTable(GameRoundTable):
    """Per-round table showing each player's point change and the pieces
    behind it."""

    def __init__(self, engine, bgcolors, parent: QWidget | None = None) -> None:
        self.bgcolors = bgcolors
        super().__init__(engine, parent)
        self.setItemDelegate(CatanChangesDelegate(self))

    def openTableMenu(self, position: QPoint) -> None:
        # Holdings build on each other, so only the last round can be deleted.
        if self.indexAt(position).row() != self.rowCount() - 1:
            return
        super().openTableMenu(position)

    def playerColour(self, player: str) -> QColor:
        """Return ``player``'s colour from the board, if this table is on one."""
        widget = self.parent()
        while widget is not None:
            if isinstance(widget, GameWidget):
                return widget.playerColour(player)
            widget = widget.parent()
        idx = self.engine.getListPlayers().index(player)
        return _CATAN_COLOURS[idx % len(_CATAN_COLOURS)]

    def insertRound(self, r) -> None:
        """Append a row for round ``r`` with each player's changes."""
        rnd = cast("CatanRound", r)
        i = rnd.getNumRound() - 1
        self.insertRow(i)
        for j, player in enumerate(self.engine.getListPlayers()):
            item = QTableWidgetItem()
            item.setFlags(item.flags() ^ QtCore.Qt.ItemFlag.ItemIsEditable)
            changes = shownChanges(rnd.getChanges(player))
            score = rnd.getPlayerScore(player)
            if changes:
                item.setData(CHANGES_ROLE, (score, self.playerColour(player), changes))
                item.setToolTip(
                    "\n".join(
                        f"{holdingLabel(key)}: {value:+d}"
                        for key, value in changes.items()
                    )
                )
            if score:
                background = self.bgcolors[0] if score > 0 else self.bgcolors[1]
                item.setBackground(QtGui.QBrush(QtGui.QColor(background)))
                item.setForeground(QtGui.QBrush(QtGui.QColor(0, 0, 0)))
            self.setItem(i, j, item)
        self.scrollToBottom()


class CatanRoundPlot(GameRoundPlot):
    """Victory points plot with the target points drawn as a limit line."""

    player_colours = _CATAN_COLOURS

    def updatePlot(self) -> None:
        super().updatePlot()
        if not self.isPlotInited():
            return
        initial = self.engine.victoryPoints(self.engine.getInitialState())
        scores = {}
        for player in self.engine.getPlayers():
            scores[player] = [initial]

        for rnd in self.engine.getRounds():
            for player in self.engine.getPlayers():
                accumscore = scores[player][-1] + rnd.getPlayerScore(player)
                scores[player].append(accumscore)

        self.canvas.clearPlotContents()
        self.canvas.addLimit(self.engine.getTop())
        for player in self.engine.getListPlayers():
            self.canvas.addSeries(scores[player], player)
