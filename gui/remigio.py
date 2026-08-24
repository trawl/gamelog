from typing import cast

from PySide6 import QtCore, QtGui
from PySide6.QtWidgets import (
    QGraphicsOpacityEffect,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QSizePolicy,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from controllers.remigioengine import RemigioEngine
from gui.game import (
    GameInputWidget,
    GameNotImplementedException,
    GamePlayerWidget,
    GameRoundPlot,
    GameRoundsDetail,
    GameRoundTable,
    GameWidget,
    PlayerColours,
    ScoreSpinBox,
)


class RemigioWidget(GameWidget):
    bgcolors = (0, 0xCCFF99, 0xFFFF99, 0xFFCC99, 0xFFCCFF)

    def createEngine(self):
        if self.game != "Remigio":
            raise GameNotImplementedException(f"No engine for game {self.game}")
        self.engine = RemigioEngine()

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

    def addPlayerWidgets(self):
        np = len(self.players)
        if np <= 6:
            self.playersLayout = QVBoxLayout()
        else:
            self.playersLayout = QGridLayout()
            self.matchGroup.setMinimumWidth(int(self.matchGroup.minimumWidth() * 1.5))
        self.matchGroupLayout.addLayout(self.playersLayout)
        self.playerGroupBox = {}
        for i, player in enumerate(self.players):
            pw = RemigioPlayerWidget(
                player, PlayerColours[i % len(PlayerColours)], self.matchGroup
            )
            pw.updateDisplay(self.engine.getScoreFromPlayer(player))
            if player == self.engine.getDealer():
                pw.setDealer()
            if self.engine.isPlayerOff(player):
                pw.koPlayer()
            if np < 8:
                self.playersLayout.addWidget(pw)
            else:
                self.playersLayout.addWidget(pw, i // 2, i % 2)  # pyright: ignore[reportArgumentType]
            self.playerGroupBox[player] = pw

    def createGameInputWidget(self, parent=None):
        return RemigioInputWidget(self.engine, self.bgcolors, parent)

    def createRoundsDetail(self, parent=None):
        return RemigioRoundsDetail(self.engine, self.bgcolors, parent)

    def updateGameStatusLabel(self):
        super().updateGameStatusLabel()
        if self.gameStatusLabel.text() == "":
            self.gameStatusLabel.setStyleSheet("QLabel {font-weight:bold;}")
            msg = self.tr(
                "Warning: real points are computed automatically depending on the close type"
            )
            self.gameStatusLabel.setText(msg)
            self.gameStatusLabel.show()

    def getPlayerExtraInfo(self, player):
        c_type = cast(RemigioInputWidget, self.gameInput).getCloseType()
        if c_type:
            return {"closeType": c_type}
        else:
            return {}

    def updatePanel(self):
        super().updatePanel()
        self.topPointsScoreBox.setReadOnly(self.engine.getNumRound() > 1)

    def updateScores(self):
        super().updateScores()
        for player in self.players:
            if self.engine.isPlayerOff(player):
                self.playerGroupBox[player].koPlayer()
                cast(RemigioInputWidget, self.gameInput).koPlayer(player)
            else:
                self.playerGroupBox[player].unKoPlayer()
                cast(RemigioInputWidget, self.gameInput).unKoPlayer(player)

    def changeTop(self, newtop=None):
        if newtop is None:
            newtop = self.topPointsScoreBox.value()
        try:
            if newtop is None:
                return
            newtop = int(newtop)
            self.engine.setTop(newtop)
            self.detailGroup.updatePlot()
        except (ValueError, TypeError):
            pass


class RemigioInputWidget(GameInputWidget):
    def __init__(self, engine, bgcolors, parent=None):
        self.bgcolors = bgcolors
        super().__init__(engine, parent)

    def initUI(self):
        for i, player in enumerate(self.engine.getListPlayers()):
            self.playerInputList[player] = RemigioPlayerInputWidget(
                player, self.bgcolors, PlayerColours[i], self
            )
            if self.engine.isPlayerOff(player):
                self.koPlayer(player)
            self.playerInputList[player].winnerSet.connect(self.changedWinner)
            self.playerInputList[player].changed.connect(self.changed)

        nplayers = len(self.engine.getListPlayers())
        if nplayers < 8:
            self.widgetLayout = QHBoxLayout(self)
            for piw in self.playerInputList.values():
                self.widgetLayout.addWidget(piw)
        else:
            self.widgetLayout = QGridLayout(self)
            for i, piw in enumerate(self.playerInputList.values()):
                self.widgetLayout.addWidget(
                    piw, i // ((nplayers + 1) // 2), i % ((nplayers + 1) // 2)
                )

    def getCloseType(self):
        try:
            return self.playerInputList[self.winnerSelected].getCloseType()
        except KeyError:
            return 0

    def getWinner(self):
        return self.winnerSelected

    def getScores(self):
        scores = {}
        for player, piw in self.playerInputList.items():
            if not piw.isKo():
                scores[player] = piw.getScore()
        return scores

    def koPlayer(self, player):
        self.playerInputList[player].setKo()

    def unKoPlayer(self, player):
        self.playerInputList[player].unsetKo()

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


class RemigioPlayerInputWidget(QGroupBox):
    winnerSet = QtCore.Signal(str)
    changed = QtCore.Signal()

    def __init__(self, player, bgcolors, colour=None, parent=None):
        super().__init__(parent)
        self.player = player
        self.pcolour = colour
        self.ko = False
        self.bgcolors = bgcolors

        self.mainLayout = QVBoxLayout(self)

        self.label = QLabel(self)
        self.mainLayout.addWidget(self.label)
        self.label.setAutoFillBackground(False)
        self.label.setScaledContents(True)
        self.label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.label.setWordWrap(False)

        self.scoreSpinBox = ScoreSpinBox(self)
        # self.scoreSpinBox.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        #         self.scoreSpinBox.setMaximumWidth(150)
        self.scoreSpinBox.setRange(-1, 100)
        self.setColour(colour)
        self.scoreSpinBox.spacePressed.connect(self.setWinner)
        self.scoreSpinBox.valueChanged.connect(self.changed)

        self.lowerLayout = QHBoxLayout()
        self.mainLayout.addLayout(self.lowerLayout)
        self.lowerLayout.addWidget(self.scoreSpinBox)

        self.reset()

    def reset(self):
        self.closeType = 0
        self.updatePanel()
        self.changed.emit()

    def setColour(self, colour):
        self.pcolour = colour
        sh = f"font-size: 24px; font-weight: bold; color:rgba({self.pcolour.red()},{self.pcolour.green()},{self.pcolour.blue()},{self.pcolour.alpha()});"
        self.label.setStyleSheet(sh)
        self.scoreSpinBox.setColour(self.pcolour)

    def increaseCloseType(self):
        self.closeType = (self.closeType) % 4 + 1
        self.changed.emit()
        self.updatePanel()

    def updatePanel(self):
        text = f"{self.player}"
        css = ""
        if self.closeType > 0:
            text = text + f" ({self.closeType}x)"
            css = f"font-weight: bold; border-radius: 4px; background-color: #{self.bgcolors[self.closeType]:X}"
            self.scoreSpinBox.setValue(0)
            self.scoreSpinBox.setReadOnly(True)
            # self.scoreSpinBox.setDisabled(True)

        else:
            self.scoreSpinBox.setValue(-1)
            self.scoreSpinBox.setReadOnly(False)
            # self.scoreSpinBox.setEnabled(True)

        self.label.setText(text)
        self.setStyleSheet(f"QGroupBox {{ {css} }}")

    def mousePressEvent(self, event):
        if self.isWinner():
            self.increaseCloseType()
        else:
            self.scoreSpinBox.setFocus()

    def mouseDoubleClickEvent(self, event):
        if not self.isWinner():
            self.winnerSet.emit(self.player)
            self.increaseCloseType()
        else:
            super().mouseDoubleClickEvent(event)

    def keyPressEvent(self, event):
        if event.key() == QtCore.Qt.Key.Key_Space:
            event.accept()
            self.setWinner()
        return super().keyPressEvent(event)

    def setWinner(self):
        if not self.isWinner():
            self.winnerSet.emit(self.player)
        self.increaseCloseType()

    def getScore(self):
        if self.isWinner():
            return 0
        else:
            return self.scoreSpinBox.value()

    def isWinner(self):
        return self.closeType > 0

    def getCloseType(self):
        return self.closeType

    def getPlayer(self):
        return self.player

    def isKo(self):
        return self.ko

    def setKo(self):
        self.ko = True
        self.setDisabled(True)
        self.hide()

    def unsetKo(self):
        self.ko = False
        self.setDisabled(False)
        self.show()


class RemigioPlayerWidget(GamePlayerWidget):
    def __init__(self, nick, colour, parent):
        super().__init__(nick, colour, parent)
        self.lcdOpacity = QGraphicsOpacityEffect(self.scoreLCD)
        self.lcdOpacity.setOpacity(1.0)
        self.scoreLCD.setGraphicsEffect(self.lcdOpacity)

    def koPlayer(self):
        self.background = QtGui.QPixmap(":/icons/skull.png")
        self.setProperty("ko", True)
        self.style().polish(self)
        self.lcdOpacity.setOpacity(0.3)
        self.update()

    def unKoPlayer(self):
        self.background = None
        self.setProperty("ko", False)
        self.lcdOpacity.setOpacity(1.0)
        self.style().polish(self)
        self.update()


class RemigioRoundsDetail(GameRoundsDetail):
    def __init__(self, engine, bgcolors, parent=None):
        self.bgcolors = bgcolors
        super().__init__(engine, parent)
        self.setCurrentWidget(self.plot)

    def createRoundTable(self, engine, parent=None):
        return RemigioRoundTable(self.engine, self.bgcolors, parent)

    def createRoundPlot(self, engine, parent=None):
        return RemigioRoundPlot(self.engine, self)


class RemigioRoundTable(GameRoundTable):
    def __init__(self, engine, bgcolors, parent=None):
        self.bgcolors = bgcolors
        super().__init__(engine, parent)

    def insertRound(self, r):
        closeType = r.getCloseType()
        winner = r.getWinner()
        background = self.bgcolors[closeType]
        i = r.getNumRound() - 1
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
            if player == winner:
                text = self.tr("Winner ({}x)").format(closeType)
                font = item.font()
                font.setBold(True)
                item.setFont(font)
            elif (
                self.engine.wasPlayerOff(player, r.getNumRound())
                or r.getPlayerScore(player) < 0
            ):
                if r.getPlayerScore(player) < 0:
                    text = ""
                else:
                    text = str(r.getPlayerScore(player))
                item.setBackground(QtGui.QBrush(QtCore.Qt.GlobalColor.gray))
                item.setForeground(QtGui.QBrush(QtGui.QColor(0, 0, 0)))
            else:
                text = str(r.getPlayerScore(player))
            item.setText(text)
            self.setItem(i, j, item)
        self.scrollToBottom()


class RemigioRoundPlot(GameRoundPlot):
    def updatePlot(self):
        super().updatePlot()
        if not self.isPlotInited():
            return
        scores = {}
        for player in self.engine.getPlayers():
            scores[player] = [0]

        for rnd in self.engine.getRounds():
            for player in self.engine.getPlayers():
                if player not in scores:
                    scores[player] = [0]
                rndscore = rnd.getPlayerScore(player)
                if rndscore >= 0:
                    accumscore = scores[player][-1] + rndscore
                    scores[player].append(accumscore)

        self.canvas.clearPlotContents()
        self.canvas.addLimit(self.engine.getTop())
        for player in self.engine.getListPlayers():
            self.canvas.addSeries(scores[player], player)
