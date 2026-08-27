from PySide6 import QtCore, QtGui
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QSizePolicy,
    QTableWidgetItem,
    QVBoxLayout,
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
    ScoreSpinBox,
)
from games.ratuki.engine import RatukiEngine


class RatukiWidget(GameWidget):
    def createEngine(self):
        if self.game != "Ratuki":
            raise GameNotImplementedException(f"No engine for game {self.game}")
        self.engine = RatukiEngine()

    def initUI(self):
        super().initUI()
        self.retranslateUI()

    def addExtraConfig(self):
        super().addExtraConfig()
        self.topPointsScoreBox = ScoreSpinBox(self.matchGroup)
        self.topPointsScoreBox.setMaximum(1000)
        self.topPointsScoreBox.setValue(self.engine.getTop())
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

    def createGameInputWidget(self, parent=None):
        return RatukiInputWidget(self.engine, parent)

    def createRoundsDetail(self, parent=None):
        return RatukiRoundsDetail(self.engine, parent)

    def checkPlayerScore(self, player, score, extras=None):
        if score is None:
            return False
        return -100 <= score <= 100

    def updatePanel(self):
        super().updatePanel()
        self.topPointsScoreBox.setReadOnly(self.engine.getNumRound() > 1)

    def changeTop(self, newtop):
        try:
            newtop = int(newtop)
            self.engine.setTop(newtop)
            self.detailGroup.updatePlot()
        except ValueError:
            pass


class RatukiInputWidget(GameInputWidget):
    def initUI(self):
        self.widgetLayout = QHBoxLayout(self)
        for i, player in enumerate(self.engine.getListPlayers()):
            self.playerInputList[player] = RatukiPlayerInputWidget(
                player, PlayerColours[i], self
            )
            self.widgetLayout.addWidget(self.playerInputList[player])
            self.playerInputList[player].winnerSet.connect(self.changedWinner)
            self.playerInputList[player].changed.connect(self.changed)

    def getWinner(self):
        for player, piw in self.playerInputList.items():
            if piw.isWinner():
                return player
        return None

    def changedWinner(self, winner):
        winner = str(winner)
        if self.winnerSelected != "":
            self.playerInputList[self.winnerSelected].unsetWinner()
        self.winnerSelected = winner

    def updatePlayerOrder(self):
        #         QWidget().setLayout(self.layout())
        trash = QWidget()
        trash_layout = self.layout()
        if trash_layout:
            trash.setLayout(trash_layout)
        self.widgetLayout = QHBoxLayout(self)
        for i, player in enumerate(self.engine.getListPlayers()):
            if trash_layout:
                trash_layout.removeWidget(self.playerInputList[player])
            self.widgetLayout.addWidget(self.playerInputList[player])
            self.playerInputList[player].setColour(PlayerColours[i])


class RatukiPlayerInputWidget(QGroupBox):
    winnerSet = QtCore.Signal(str)
    changed = QtCore.Signal()

    def __init__(self, player, colour=None, parent=None):
        super().__init__(parent)
        self.player = player
        self.pcolour = colour if colour else QColor(0, 0, 0)
        self.winner = False
        self.initUI()
        self.reset()

    def initUI(self):
        self.mainLayout = QVBoxLayout(self)

        self.label = QLabel(self)
        self.mainLayout.addWidget(self.label)
        self.label.setAutoFillBackground(False)
        self.label.setScaledContents(True)
        self.label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.label.setWordWrap(False)

        self.scoreSpinBox = ScoreSpinBox(self)
        self.scoreSpinBox.setRange(-100, 100)
        self.setColour(self.pcolour)
        self.scoreSpinBox.spacePressed.connect(self.setWinner)
        self.scoreSpinBox.valueChanged.connect(self.changed)

        self.lowerLayout = QHBoxLayout()
        self.mainLayout.addLayout(self.lowerLayout)
        self.lowerLayout.addWidget(self.scoreSpinBox)

    def reset(self):
        self.winner = False
        self.scoreSpinBox.setValue(None)
        self.updatePanel()

    def setColour(self, colour):
        self.pcolour = colour
        sh = f"font-size: 24px; font-weight: bold; color:rgba({self.pcolour.red()},{self.pcolour.green()},{self.pcolour.blue()},{self.pcolour.alpha()});"
        self.label.setStyleSheet(sh)
        self.scoreSpinBox.setColour(self.pcolour)

    def updatePanel(self):
        text = f"{self.player}"
        css = ""
        if self.winner:
            css = f"font-weight: bold; border-radius: 4px; background-color: #{0xFFFF99:X}"

        self.label.setText(text)
        self.setStyleSheet(f"QGroupBox {{ {css} }}")

    def mousePressEvent(self, event):
        self.scoreSpinBox.setFocus()

    def mouseDoubleClickEvent(self, event):
        if not self.isWinner():
            self.setWinner()
            # event.accept()
        return super().mouseDoubleClickEvent(event)

    def keyPressEvent(self, event):
        if event.key() == QtCore.Qt.Key.Key_Space:
            event.accept()
            self.setWinner()
        return super().keyPressEvent(event)

    def setWinner(self):
        if not self.isWinner():
            self.winner = True
            self.winnerSet.emit(self.player)
            self.changed.emit()
            self.updatePanel()

    def unsetWinner(self):
        if self.isWinner():
            self.winner = False
            self.changed.emit()
            self.updatePanel()

    def getScore(self):
        return self.scoreSpinBox.value()

    def isWinner(self):
        return self.winner

    def getPlayer(self):
        return self.player


class RatukiRoundsDetail(GameRoundsDetail):
    def __init__(self, engine, parent=None):
        self.bgcolors = [0xCCFF99, 0xFFCC99]
        super().__init__(engine, parent)
        self.setCurrentWidget(self.plot)

    def createRoundTable(self, engine, parent=None):
        return RatukiRoundTable(self.engine, self.bgcolors, parent)

    def createRoundPlot(self, engine, parent=None):
        return RatukiRoundPlot(self.engine, self)


class RatukiRoundTable(GameRoundTable):
    def __init__(self, engine, bgcolors, parent=None):
        self.bgcolors = bgcolors
        super().__init__(engine, parent)

    def insertRound(self, r):
        winner = r.getWinner()
        i = r.getNumRound() - 1
        self.insertRow(i)
        for j, player in enumerate(self.engine.getListPlayers()):
            item = QTableWidgetItem()
            item.setFlags(item.flags() ^ QtCore.Qt.ItemFlag.ItemIsEditable)
            item.setTextAlignment(
                QtCore.Qt.AlignmentFlag.AlignVCenter
                | QtCore.Qt.AlignmentFlag.AlignCenter
            )
            score = r.getPlayerScore(player)
            if score > 0:
                background = self.bgcolors[0]
            else:
                background = self.bgcolors[1]
            item.setBackground(QtGui.QBrush(QtGui.QColor(background)))
            item.setForeground(QtGui.QBrush(QtGui.QColor(0, 0, 0)))
            text = str(score)
            if player == winner:
                text += self.tr(" (Winner)")
            item.setText(text)
            self.setItem(i, j, item)
        self.scrollToBottom()


class RatukiRoundPlot(GameRoundPlot):
    def updatePlot(self):
        super().updatePlot()
        if not self.isPlotInited():
            return
        scores = {}
        for player in self.engine.getPlayers():
            scores[player] = [0]

        for rnd in self.engine.getRounds():
            for player in self.engine.getPlayers():
                rndscore = rnd.getPlayerScore(player)
                accumscore = scores[player][-1] + rndscore
                scores[player].append(accumscore)

        self.canvas.clearPlotContents()
        self.canvas.addLimit(self.engine.getTop())
        for player in self.engine.getListPlayers():
            self.canvas.addSeries(scores[player], player)
