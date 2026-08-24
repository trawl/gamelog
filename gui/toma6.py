from PySide6 import QtCore, QtGui
from PySide6.QtWidgets import (
    QHBoxLayout,
    QTableWidgetItem,
)

from controllers.toma6engine import Toma6Engine
from gui.game import GameNotImplementedException, GamePlayerWidget, PlayerColours
from gui.remigio import (
    RemigioInputWidget,
    RemigioPlayerInputWidget,
    RemigioRoundPlot,
    RemigioRoundsDetail,
    RemigioRoundTable,
    RemigioWidget,
)


class Toma6Widget(RemigioWidget):
    def createEngine(self):
        if self.game != "Toma6":
            raise GameNotImplementedException(f"No engine for game {self.game}")
        self.engine = Toma6Engine()

    def createGameInputWidget(self, parent=None):
        return Toma6InputWidget(self.engine, parent)

    def createRoundsDetail(self, parent=None):
        return Toma6RoundsDetail(self.engine, parent)


class Toma6InputWidget(RemigioInputWidget):
    def initUI(self):
        self.widgetLayout = QHBoxLayout(self)

        for i, player in enumerate(self.engine.getListPlayers()):
            self.playerInputList[player] = Toma6PlayerInputWidget(
                player, self.bgcolors, PlayerColours[i], self
            )
            self.widgetLayout.addWidget(self.playerInputList[player])
            self.playerInputList[player].changed.connect(self.changed)
            self.playerInputList[player].changed.connect(self.getWinner)

    def getWinner(self):
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
    def increaseCloseType(self):
        pass

    def updatePanel(self):
        text = f"{self.player}"
        css = ""
        self.scoreSpinBox.setValue(-1)
        self.scoreSpinBox.setEnabled(True)

        self.label.setText(text)
        self.setStyleSheet(f"QFrame {{ {css} }}")

    def mousePressEvent(self, event):
        self.scoreSpinBox.setFocus()

    def mouseDoubleClickEvent(self, event):
        super(RemigioPlayerInputWidget, self).mouseDoubleClickEvent(event)

    def isWinner(self):
        return False


class Toma6PlayerWidget(GamePlayerWidget):
    pass


class Toma6RoundsDetail(RemigioRoundsDetail):
    def __init__(self, engine, parent=None):
        self.bgcolors = [0xCCFF99, 0xFFCC99]
        super().__init__(engine, self.bgcolors, parent)
        self.container.setCurrentWidget(self.plot)

    def createRoundTable(self, engine, parent=None):
        return Toma6RoundTable(self.engine, self.bgcolors, parent)

    def createRoundPlot(self, engine, parent=None):
        return Toma6RoundPlot(self.engine, self)


class Toma6RoundTable(RemigioRoundTable):
    def __init__(self, engine, bgcolors, parent=None):
        self.bgcolors = bgcolors
        super().__init__(engine, self.bgcolors, parent)

    def insertRound(self, r):
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
    pass
