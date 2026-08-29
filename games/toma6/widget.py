"""6 Nimmt! (Toma6) scoreboard widgets, specialising the Remigio widgets."""

from __future__ import annotations

from PySide6 import QtCore, QtGui
from PySide6.QtGui import QMouseEvent
from PySide6.QtWidgets import (
    QHBoxLayout,
    QTableWidgetItem,
)

from core.ui.game import GameNotImplementedException, GamePlayerWidget, PlayerColours
from games.remigio.widget import (
    RemigioInputWidget,
    RemigioPlayerInputWidget,
    RemigioRoundPlot,
    RemigioRoundsDetail,
    RemigioRoundTable,
    RemigioWidget,
)
from games.toma6.engine import Toma6Engine


class Toma6Widget(RemigioWidget):
    """Scoreboard tab for Toma6, reusing Remigio's layout and controls."""

    def createEngine(self) -> None:
        if self.game != "Toma6":
            raise GameNotImplementedException(f"No engine for game {self.game}")
        self.engine = Toma6Engine()

    def createGameInputWidget(self, parent=None) -> Toma6InputWidget:
        return Toma6InputWidget(self.engine, parent)

    def createRoundsDetail(self, parent=None) -> Toma6RoundsDetail:
        return Toma6RoundsDetail(self.engine, parent)


class Toma6InputWidget(RemigioInputWidget):
    """Score-entry widget where the lowest score wins, with no close types."""

    def initUI(self) -> None:
        self.widgetLayout = QHBoxLayout(self)

        for i, player in enumerate(self.engine.getListPlayers()):
            self.playerInputList[player] = Toma6PlayerInputWidget(
                player, self.bgcolors, PlayerColours[i], self
            )
            self.widgetLayout.addWidget(self.playerInputList[player])
            self.playerInputList[player].changed.connect(self.changed)
            self.playerInputList[player].changed.connect(self.getWinner)

    # Toma6 scores the lowest player as winner, so this widens the Remigio
    # base return to allow None while no valid winner is selected yet.
    def getWinner(self) -> str | None:  # pyright: ignore[reportIncompatibleMethodOverride]
        scores = self.getScores()
        if any(score < 0 for score in scores.values()):
            return None
        min_score = 100000
        self.winnerSelected = None
        for player, score in scores.items():
            if score < min_score:
                min_score = score
                self.winnerSelected = player
        return self.winnerSelected


class Toma6PlayerInputWidget(RemigioPlayerInputWidget):
    """Per-player input box for Toma6: a plain score field, never a winner."""

    def increaseCloseType(self) -> None:
        pass

    def updatePanel(self) -> None:
        text = f"{self.player}"
        css = ""
        self.scoreSpinBox.setValue(-1)
        self.scoreSpinBox.setEnabled(True)

        self.label.setText(text)
        self.setStyleSheet(f"QFrame {{ {css} }}")

    def mousePressEvent(self, event: QMouseEvent) -> None:
        self.scoreSpinBox.setFocus()

    def mouseDoubleClickEvent(self, event: QMouseEvent) -> None:
        super(RemigioPlayerInputWidget, self).mouseDoubleClickEvent(event)

    def isWinner(self) -> bool:
        return False


class Toma6PlayerWidget(GamePlayerWidget):
    """Scoreboard player box for Toma6 (identical to the generic box)."""


class Toma6RoundsDetail(RemigioRoundsDetail):
    """Rounds detail panel for Toma6, defaulting to the plot tab."""

    def __init__(self, engine, parent=None) -> None:
        self.bgcolors = [0xCCFF99, 0xFFCC99]
        super().__init__(engine, self.bgcolors, parent)
        self.setCurrentWidget(self.plot)

    def createRoundTable(self, engine, parent=None) -> Toma6RoundTable:
        return Toma6RoundTable(self.engine, self.bgcolors, parent)

    def createRoundPlot(self, engine, parent=None) -> Toma6RoundPlot:
        return Toma6RoundPlot(self.engine, self)


class Toma6RoundTable(RemigioRoundTable):
    """Per-round score table for Toma6, highlighting the round winner."""

    def __init__(self, engine, bgcolors, parent=None) -> None:
        self.bgcolors = bgcolors
        super().__init__(engine, self.bgcolors, parent)

    def insertRound(self, r) -> None:
        """Append a table row for round ``r`` with each player's score."""
        i = r.getNumRound() - 1
        winner = r.getWinner()
        self.insertRow(i)
        for j, player in enumerate(self.engine.getListPlayers()):
            item = QTableWidgetItem()
            item.setFlags(item.flags() ^ QtCore.Qt.ItemFlag.ItemIsEditable)
            item.setTextAlignment(
                QtCore.Qt.AlignmentFlag.AlignVCenter
                | QtCore.Qt.AlignmentFlag.AlignCenter
            )
            if player == winner:
                background = self.bgcolors[1]
                font = item.font()
                font.setBold(True)
                item.setFont(font)
            else:
                background = self.bgcolors[0]
            item.setBackground(QtGui.QBrush(QtGui.QColor(background)))
            item.setForeground(QtGui.QBrush(QtGui.QColor(0, 0, 0)))
            item.setText(str(r.getPlayerScore(player)))
            self.setItem(i, j, item)
        self.scrollToBottom()


class Toma6RoundPlot(RemigioRoundPlot):
    """Cumulative-score plot for Toma6."""
