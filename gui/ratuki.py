#!/usr/bin/env python
# -*- coding: utf-8 -*-

try:
    from PySide6 import QtCore, QtGui
    from PySide6.QtWidgets import (QApplication, QFrame, QGridLayout, QGroupBox,
                                QHBoxLayout, QLabel, QLineEdit, QSizePolicy,
                                QTableWidgetItem, QVBoxLayout)
except ImportError:
    from PyQt5 import QtCore, QtGui
    from PyQt5.QtWidgets import (QApplication, QFrame, QGridLayout, QGroupBox,
                                QHBoxLayout, QLabel, QLineEdit, QSizePolicy,
                                QTableWidgetItem, QVBoxLayout)

from controllers.ratukiengine import RatukiEngine
from gui.game import (GameWidget, GameInputWidget, ScoreSpinBox,
                      GameRoundsDetail, GameRoundTable, GameRoundPlot,
                      GamePlayerWidget, PlayerColours)

i18n = QApplication.translate


class RatukiWidget(GameWidget):

    def createEngine(self):
        if self.game != 'Ratuki':
            raise Exception("No engine for game {}".format(self.game))
            return
        self.engine = RatukiEngine()

    def initUI(self):
        super(RatukiWidget, self).initUI()

        self.gameInput = RatukiInputWidget(self.engine, self)
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

        self.detailGroup = RatukiRoundsDetail(self.engine, self)
        self.detailGroup.edited.connect(self.updatePanel)
        # self.widgetLayout.addWidget(self.detailGroup, 1, 0)
        self.leftLayout.addWidget(self.detailGroup)

        self.playerGroup = QGroupBox(self)
        # self.widgetLayout.addWidget(self.playerGroup, 1, 1)
        self.rightLayout.addWidget(self.playerGroup)

        self.playerGroup.setStyleSheet(
            "QGroupBox { font-size: 18px; font-weight: bold; }")
        self.playersLayout = QVBoxLayout(self.playerGroup)
        # self.playersLayout.addStretch()
        self.playerGroupBox = {}
        for i, player in enumerate(self.players):
            pw = GamePlayerWidget(player, PlayerColours[i], self.playerGroup)
            pw.updateDisplay(self.engine.getScoreFromPlayer(player))
            if player == self.engine.getDealer():
                pw.setDealer()
            self.playersLayout.addWidget(pw)
            self.playerGroupBox[player] = pw

        # self.playersLayout.addStretch()

        self.retranslateUI()

    def retranslateUI(self):
        super(RatukiWidget, self).retranslateUI()
        self.topPointsLabel.setText(
            i18n("RatukiWidget", "Score Limit"))
#         self.playerGroup.setTitle(i18n("RatukiWidget","Score"))
        self.playerGroup.setTitle(i18n("GameWidget","Scoreboard"))
        self.detailGroup.retranslateUI()

    def checkPlayerScore(self, player, score): return True

    def unsetDealer(
        self): self.playerGroupBox[self.engine.getDealer()].unsetDealer()

    def setDealer(
        self): self.playerGroupBox[self.engine.getDealer()].setDealer()

    def updatePanel(self):
        self.topPointsLineEdit.setReadOnly(True)
        self.dealerPolicyCheckBox.setEnabled(False)
        for player in self.players:
            score = self.engine.getScoreFromPlayer(player)
            self.playerGroupBox[player].updateDisplay(score)

        if self.engine.getWinner():
            self.detailGroup.updateStats()
        self.detailGroup.updateRound()
        super(RatukiWidget, self).updatePanel()

    def changeTop(self, newtop):
        try:
            newtop = int(newtop)
            self.engine.setTop(newtop)
            self.detailGroup.updatePlot()
        except ValueError:
            pass

    def setWinner(self):
        super(RatukiWidget, self).setWinner()
        winner = self.engine.getWinner()
        if winner in self.players:
            self.playerGroupBox[winner].setWinner()

    def updatePlayerOrder(self):
        GameWidget.updatePlayerOrder(self)
        trash = QWidget()
        trash.setLayout(self.playersLayout)
        self.playersLayout = QVBoxLayout(self.playerGroup)
        # self.playersLayout.addStretch()
        for i, player in enumerate(self.engine.getListPlayers()):
            trash.layout().removeWidget(self.playerGroupBox[player])
            self.playersLayout.addWidget(self.playerGroupBox[player])
            self.playerGroupBox[player].setColour(PlayerColours[i])
        # self.playersLayout.addStretch()
        self.detailGroup.updatePlayerOrder()


class RatukiInputWidget(GameInputWidget):

    def __init__(self, engine, parent=None):
        super(RatukiInputWidget, self).__init__(engine, parent)
        self.initUI()

    def initUI(self):
        self.widgetLayout = QHBoxLayout(self)

        for i, player in enumerate(self.engine.getListPlayers()):
            self.playerInputList[player] = RatukiPlayerInputWidget(
                player, PlayerColours[i], self)
            self.widgetLayout.addWidget(self.playerInputList[player])
            self.playerInputList[player].winnerSet.connect(self.changedWinner)

    def getScores(self):
        scores = {}
        for player, piw in self.playerInputList.items():
            scores[player] = piw.getScore()
        return scores

    def updatePlayerOrder(self):
        #         QWidget().setLayout(self.layout())
        trash = QWidget()
        trash.setLayout(self.layout())
        self.widgetLayout = QHBoxLayout(self)
        for i, player in enumerate(self.engine.getListPlayers()):
            trash.layout().removeWidget(self.playerInputList[player])
            self.widgetLayout.addWidget(self.playerInputList[player])
            self.playerInputList[player].setColour(PlayerColours[i])


class RatukiPlayerInputWidget(QFrame):

    winnerSet = QtCore.Signal(str)

    def __init__(self, player, colour=None, parent=None):
        super(RatukiPlayerInputWidget, self).__init__(parent)
        self.player = player
        self.winner = False
        self.pcolour = colour
        self.mainLayout = QVBoxLayout(self)

        self.label = QLabel(self)
        self.label.setText(self.player)
        self.mainLayout.addWidget(self.label)
        self.label.setAutoFillBackground(False)
        self.setFrameShape(QFrame.Panel)
        self.setFrameShadow(QFrame.Raised)
        self.label.setScaledContents(True)
        self.label.setAlignment(QtCore.Qt.AlignCenter)
        self.label.setWordWrap(False)

        self.scoreSpinBox = ScoreSpinBox(self)
        self.scoreSpinBox.setAlignment(QtCore.Qt.AlignCenter)
#         self.scoreSpinBox.setMaximumWidth(60)
        self.scoreSpinBox.setRange(-100, 100)
#         self.mainLayout.addWidget(self.scoreSpinBox)
#         self.mainLayout.setAlignment(self.scoreSpinBox,QtCore.Qt.AlignCenter)

        self.setColour(self.pcolour)

        self.lowerLayout = QHBoxLayout()
        self.mainLayout.addLayout(self.lowerLayout)
        self.lowerLayout.addWidget(self.scoreSpinBox)

        self.reset()

    def reset(self):
        self.winner = False
        self.scoreSpinBox.setValue(0)
        self.updatePanel()

    def updatePanel(self):
        css = ""
        if self.winner:
            css = "font-weight: bold; background-color: #{0:X}".format(
                0xFFFF99)
            self.setFrameShadow(QFrame.Sunken)
        else:
            self.setFrameShadow(QFrame.Raised)
        self.setStyleSheet("QFrame {{ {} }}".format(css))

    def mousePressEvent(self, event):
        self.scoreSpinBox.setFocus()

    def mouseDoubleClickEvent(self, event):
        if not self.isWinner():
            self.winner = True
            self.updatePanel()
            self.winnerSet.emit(self.player)
        else:
            super(RatukiPlayerInputWidget, self).mouseDoubleClickEvent(event)

    def isWinner(self): return self.winner

    def getPlayer(self): return self.player

    def getScore(self): return self.scoreSpinBox.value()

    def setColour(self, colour=None):
        if colour is not None:
            self.pcolour = colour
        sh = "font-size: 24px; font-weight: bold; color:rgb({},{},{});".format(
            self.pcolour.red(), self.pcolour.green(), self.pcolour.blue())
        self.label.setStyleSheet(sh)
        sh = "QSpinBox {{ {} }}".format(sh)
        # sh = """
        # QSpinBox {{ {} }}
        # QSpinBox::up-button  {{subcontrol-origin: border;
        #     subcontrol-position: left; width: 60px; height: 60px; }}
        # QSpinBox::down-button  {{subcontrol-origin: border;
        #     subcontrol-position: right; width: 60px; height: 60px; }}
        # """.format(sh)
        self.scoreSpinBox.setStyleSheet(sh)
        print("Setting stylesheet to the scoreSpinBox")


class RatukiRoundsDetail(GameRoundsDetail):

    def __init__(self, engine, parent=None):
        self.bgcolors = [0xCCFF99, 0xFFCC99]
        super(RatukiRoundsDetail, self).__init__(engine, parent)

    def createRoundTable(self, engine, parent=None):
        return RatukiRoundTable(self.engine, self.bgcolors, parent)

    def createRoundPlot(self, engine, parent=None):
        return RatukiRoundPlot(self.engine, self)


class RatukiRoundTable(GameRoundTable):

    def __init__(self, engine, bgcolors, parent=None):
        self.bgcolors = bgcolors
        super(RatukiRoundTable, self).__init__(engine, parent)

    def insertRound(self, r):
        winner = r.getWinner()
        i = r.getNumRound() - 1
        self.insertRow(i)
        for j, player in enumerate(self.engine.getListPlayers()):
            item = QTableWidgetItem()
            item.setFlags(item.flags() ^ QtCore.Qt.ItemIsEditable)
            item.setTextAlignment(QtCore.Qt.AlignVCenter |
                                  QtCore.Qt.AlignCenter)
            score = r.getPlayerScore(player)
            if score > 0:
                background = self.bgcolors[0]
            else:
                background = self.bgcolors[1]
            item.setBackground(QtGui.QBrush(QtGui.QColor(background)))
            item.setForeground(QtGui.QBrush(QtGui.QColor(0,0,0)))
            text = str(score)
            if player == winner:
                text += i18n(
                    "RatukiRoundTable", " (Winner)")
            item.setText(text)
            self.setItem(i, j, item)
        self.scrollToBottom()


class RatukiRoundPlot(GameRoundPlot):

    def initPlot(self):
        super(RatukiRoundPlot, self).initPlot()
        self.updatePlot()

    def updatePlot(self):
        super(RatukiRoundPlot, self).updatePlot()
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
