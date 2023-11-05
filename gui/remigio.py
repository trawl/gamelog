#!/usr/bin/env python
# -*- coding: utf-8 -*-

from PyQt5 import QtCore, QtGui
from PyQt5.QtWidgets import (QApplication, QFrame, QGridLayout, QGroupBox,
                             QHBoxLayout, QLabel, QLineEdit, QSizePolicy,
                             QTableWidgetItem, QVBoxLayout, QWidget)

from controllers.remigioengine import RemigioEngine
from gui.game import (GameWidget, GameInputWidget, ScoreSpinBox,
                      GameRoundsDetail, GameRoundTable, GameRoundPlot,
                      GamePlayerWidget, PlayerColours)

i18n = QApplication.translate


class RemigioWidget(GameWidget):

    bgcolors = [0, 0xCCFF99, 0xFFFF99, 0xFFCC99, 0xFFCCFF]

    def createEngine(self):
        if self.game != 'Remigio':
            raise Exception("No engine for game {}".format(self.game))
            return
        self.engine = RemigioEngine()

    def initUI(self):
        super(RemigioWidget, self).initUI()

        self.gameInput = RemigioInputWidget(
            self.engine, RemigioWidget.bgcolors, self)
        self.gameInput.enterPressed.connect(self.commitRound)
        self.roundLayout.addWidget(self.gameInput)

        self.configLayout = QGridLayout()
        self.matchGroupLayout.addLayout(self.configLayout)
        self.topPointsLineEdit = QLineEdit(self.matchGroup)
        self.topPointsLineEdit.setText(str(self.engine.getTop()))
        self.topPointsLineEdit.setValidator(
            QtGui.QIntValidator(1, 10000, self.topPointsLineEdit))
        self.topPointsLineEdit.setFixedWidth(50)
        sp = QSizePolicy(
            QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.topPointsLineEdit.setSizePolicy(sp)
        self.topPointsLineEdit.textChanged.connect(self.changeTop)
        self.topPointsLineEdit.setDisabled(self.engine.getNumRound() > 1)
        self.configLayout.addWidget(self.topPointsLineEdit, 0, 0)

        self.topPointsLabel = QLabel(self.matchGroup)
        self.topPointsLabel.setStyleSheet("QLabel {font-weight: bold; }")
        self.configLayout.addWidget(self.topPointsLabel, 0, 1)

        self.detailGroup = RemigioRoundsDetail(
            self.engine, RemigioWidget.bgcolors, self)
        self.detailGroup.edited.connect(self.updatePanel)
#         self.detailGroup = GameRoundsDetail(self.engine, self)
        self.widgetLayout.addWidget(self.detailGroup, 1, 0)

        self.playerGroup = QGroupBox(self)
        self.widgetLayout.addWidget(self.playerGroup, 1, 1)

        self.playerGroup.setStyleSheet(
            "QGroupBox { font-size: 18px; font-weight: bold; }")
        self.playersLayout = QVBoxLayout(self.playerGroup)
        self.playersLayout.addStretch()
        self.playerGroupBox = {}
        for i, player in enumerate(self.players):
            pw = RemigioPlayerWidget(
                player, PlayerColours[i % len(PlayerColours)],
                self.playerGroup)
            pw.updateDisplay(self.engine.getScoreFromPlayer(player))
            if player == self.engine.getDealer():
                pw.setDealer()
            if self.engine.isPlayerOff(player):
                print("Should set {} to ko...".format(player))
                pw.koPlayer()
            self.playersLayout.addWidget(pw)
            self.playerGroupBox[player] = pw

        self.playersLayout.addStretch()

        self.retranslateUI()

    def retranslateUI(self):
        super(RemigioWidget, self).retranslateUI()
        self.topPointsLabel.setText(
            i18n("RemigioWidget", "Score Limit"))
#         self.playerGroup.setTitle(i18n("RemigioWidget","Score"))
        self.detailGroup.retranslateUI()

    def updateGameStatusLabel(self):
        super(RemigioWidget, self).updateGameStatusLabel()
        if self.gameStatusLabel.text() == "":
            self.gameStatusLabel.setStyleSheet("QLabel {font-weight:bold;}")
            msg = i18n("RemigioWidget", "Warning: real points are computed \
                        automatically depending on the close type")
            self.gameStatusLabel.setText(msg)

    def getPlayerExtraInfo(self, player):
        c_type = self.gameInput.getCloseType()
        if c_type:
            return {'closeType': c_type}
        else:
            return {}

    def unsetDealer(
        self): self.playerGroupBox[self.engine.getDealer()].unsetDealer()

    def setDealer(
        self): self.playerGroupBox[self.engine.getDealer()].setDealer()

    def updatePanel(self):
        self.topPointsLineEdit.setReadOnly(True)
        self.dealerPolicyCheckBox.setEnabled(False)
        self.updateScores()
        if self.engine.getWinner():
            self.detailGroup.updateStats()
        self.detailGroup.updateRound()
        super(RemigioWidget, self).updatePanel()

    def updateScores(self):
        for player in self.players:
            score = self.engine.getScoreFromPlayer(player)
            self.playerGroupBox[player].updateDisplay(score)
            if self.engine.isPlayerOff(player):
                self.playerGroupBox[player].koPlayer()
                self.gameInput.koPlayer(player)
            else:
                self.playerGroupBox[player].unKoPlayer()
                self.gameInput.unKoPlayer(player)

    def changeTop(self, newtop):
        try:
            newtop = int(newtop)
            self.engine.setTop(newtop)
            self.detailGroup.updatePlot()
        except ValueError:
            pass

    def setWinner(self):
        super(RemigioWidget, self).setWinner()
        winner = self.engine.getWinner()
        if winner in self.players:
            self.playerGroupBox[winner].setWinner()

    def updatePlayerOrder(self):
        GameWidget.updatePlayerOrder(self)
        trash = QWidget()
        trash.setLayout(self.playersLayout)
        self.playersLayout = QVBoxLayout(self.playerGroup)
        self.playersLayout.addStretch()
        for i, player in enumerate(self.engine.getListPlayers()):
            trash.layout().removeWidget(self.playerGroupBox[player])
            self.playersLayout.addWidget(self.playerGroupBox[player])
            self.playerGroupBox[player].setColour(PlayerColours[i])
        self.playersLayout.addStretch()
        self.detailGroup.updatePlayerOrder()


class RemigioInputWidget(GameInputWidget):

    def __init__(self, engine, bgcolors, parent=None):
        super(RemigioInputWidget, self).__init__(engine, parent)
        self.bgcolors = bgcolors
        self.initUI()

    def initUI(self):
        self.widgetLayout = QHBoxLayout(self)

        for i, player in enumerate(self.engine.getListPlayers()):
            self.playerInputList[player] = RemigioPlayerInputWidget(
                player, self.bgcolors, PlayerColours[i], self)
            if self.engine.isPlayerOff(player):
                self.koPlayer(player)
            self.widgetLayout.addWidget(self.playerInputList[player])
            self.playerInputList[player].winnerSet.connect(self.changedWinner)

    def getCloseType(self):
        try:
            return self.playerInputList[self.winnerSelected].getCloseType()
        except KeyError:
            return 0

    def getWinner(self): return self.winnerSelected

    def getScores(self):
        scores = {}
        for player, piw in self.playerInputList.items():
            if not piw.isKo():
                scores[player] = piw.getScore()
        return scores

    def koPlayer(self, player): self.playerInputList[player].setKo()

    def unKoPlayer(self, player): self.playerInputList[player].unsetKo()

    def updatePlayerOrder(self):
        #         QWidget().setLayout(self.layout())
        trash = QWidget()
        trash.setLayout(self.layout())
        self.widgetLayout = QHBoxLayout(self)
        for i, player in enumerate(self.engine.getListPlayers()):
            trash.layout().removeWidget(self.playerInputList[player])
            self.widgetLayout.addWidget(self.playerInputList[player])
            self.playerInputList[player].setColour(PlayerColours[i])


class RemigioPlayerInputWidget(QFrame):

    winnerSet = QtCore.pyqtSignal(str)

    def __init__(self, player, bgcolors, colour=None, parent=None):
        super(RemigioPlayerInputWidget, self).__init__(parent)
        self.player = player
        self.pcolour = colour
        self.ko = False
        self.bgcolors = bgcolors

        self.mainLayout = QVBoxLayout(self)

        self.label = QLabel(self)
        self.mainLayout.addWidget(self.label)
        self.label.setAutoFillBackground(False)
        self.setFrameShape(QFrame.Panel)
        self.setFrameShadow(QFrame.Raised)
        self.label.setScaledContents(True)
        self.label.setAlignment(QtCore.Qt.AlignCenter)
        self.label.setWordWrap(False)

        self.scoreSpinBox = ScoreSpinBox(self)
        self.scoreSpinBox.setAlignment(QtCore.Qt.AlignCenter)
#         self.scoreSpinBox.setMaximumWidth(150)
        self.scoreSpinBox.setRange(-1, 100)
        self.setColour(colour)

        self.lowerLayout = QHBoxLayout()
        self.mainLayout.addLayout(self.lowerLayout)
        self.lowerLayout.addWidget(self.scoreSpinBox)

        self.reset()

    def reset(self):
        self.closeType = 0
        self.updatePanel()

    def setColour(self, colour):
        self.pcolour = colour
        sh = "font-size: 24px; font-weight: bold; color:rgb({},{},{});".format(
            self.pcolour.red(), self.pcolour.green(), self.pcolour.blue())
        self.label.setStyleSheet(sh)
        sh = """
        QSpinBox {{ {} }}
        QSpinBox::up-button  {{subcontrol-origin: border;
            subcontrol-position: left; width: 60px; height: 60px; }}
        QSpinBox::down-button  {{subcontrol-origin: border;
            subcontrol-position: right; width: 60px; height: 60px; }}
        """.format(sh)
        self.scoreSpinBox.setStyleSheet(sh)

    def increaseCloseType(self):
        self.closeType = (self.closeType) % 4 + 1
        self.updatePanel()

    def updatePanel(self):
        text = "{}".format(self.player)
        css = ""
        if self.closeType > 0:
            text = text + " ({}x)".format(self.closeType)
            css = "font-weight: bold; background-color: #{0:X}".format(
                self.bgcolors[self.closeType])
            self.setFrameShadow(QFrame.Sunken)
            self.scoreSpinBox.setValue(0)
            self.scoreSpinBox.setDisabled(True)

        else:
            self.setFrameShadow(QFrame.Raised)
            self.scoreSpinBox.setValue(-1)
            self.scoreSpinBox.setEnabled(True)

        self.label.setText(text)
        self.setStyleSheet("QFrame {{ {} }}".format(css))

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
            super(RemigioPlayerInputWidget, self).mouseDoubleClickEvent(event)

    def getScore(self):
        if self.isWinner():
            return 0
        else:
            return self.scoreSpinBox.value()

    def isWinner(self): return self.closeType > 0

    def getCloseType(self): return self.closeType

    def getPlayer(self): return self.player

    def isKo(self): return self.ko

    def setKo(self):
        self.ko = True
        self.setDisabled(True)

    def unsetKo(self):
        self.ko = False
        self.setDisabled(False)


class RemigioPlayerWidget(GamePlayerWidget):

    def koPlayer(self):
        self.iconlabel.setPixmap(QtGui.QPixmap('icons/skull.png'))

    def unKoPlayer(self):
        self.iconlabel.setPixmap(self.nonDealerPixmap)


class RemigioRoundsDetail(GameRoundsDetail):

    def __init__(self, engine, bgcolors, parent=None):
        self.bgcolors = bgcolors
        super(RemigioRoundsDetail, self).__init__(engine, parent)

    def createRoundTable(self, engine, parent=None):
        return RemigioRoundTable(self.engine, self.bgcolors, parent)

    def createRoundPlot(self, engine, parent=None):
        return RemigioRoundPlot(self.engine, self)


class RemigioRoundTable(GameRoundTable):

    def __init__(self, engine, bgcolors, parent=None):
        self.bgcolors = bgcolors
        super(RemigioRoundTable, self).__init__(engine, parent)

    def insertRound(self, r):
        closeType = r.getCloseType()
        winner = r.getWinner()
        background = self.bgcolors[closeType]
        i = r.getNumRound() - 1
        self.insertRow(i)
        for j, player in enumerate(self.engine.getListPlayers()):
            item = QTableWidgetItem()
            item.setFlags(item.flags() ^ QtCore.Qt.ItemIsEditable)
            item.setTextAlignment(QtCore.Qt.AlignVCenter |
                                  QtCore.Qt.AlignCenter)
            item.setBackground(QtGui.QBrush(QtGui.QColor(background)))
            if player == winner:
                text = i18n(
                    "RemigioRoundTable", "Winner ({}x)").format(closeType)
                font = item.font()
                font.setBold(True)
                item.setFont(font)
            elif self.engine.wasPlayerOff(
                    player, r.getNumRound()) or r.getPlayerScore(player) < 0:
                if r.getPlayerScore(player) < 0:
                    text = ""
                else:
                    text = str(r.getPlayerScore(player))
                item.setBackground(QtGui.QBrush(QtCore.Qt.gray))
            else:
                text = str(r.getPlayerScore(player))
            item.setText(text)
            self.setItem(i, j, item)
        self.scrollToBottom()


class RemigioRoundPlot(GameRoundPlot):

    def initPlot(self):
        super(RemigioRoundPlot, self).initPlot()
        self.updatePlot()

    def updatePlot(self):
        super(RemigioRoundPlot, self).updatePlot()
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
