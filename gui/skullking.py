#!/usr/bin/env python
# -*- coding: utf-8 -*-

try:
    from PySide6 import QtCore, QtGui
    from PySide6.QtWidgets import (QApplication, QButtonGroup, QFrame, QGridLayout,
                                QGroupBox, QHBoxLayout, QLabel, QMessageBox,
                                QPushButton, QCheckBox, QSizePolicy,
                                QTableWidgetItem, QVBoxLayout, QWidget)
except ImportError:
    from PyQt5 import QtCore, QtGui
    from PyQt5.QtWidgets import (QApplication, QButtonGroup, QFrame, QGridLayout,
                                QGroupBox, QHBoxLayout, QLabel, QMessageBox,
                                QPushButton, QCheckBox, QSizePolicy,
                                QTableWidgetItem, QVBoxLayout, QWidget)

from controllers.skullkingengine import SkullKingEngine
from gui.game import (GameWidget, GameInputWidget, GameRoundsDetail,
                      GameRoundTable, GameRoundPlot, GamePlayerWidget,
                      PlayerColours, ScoreSpinBox)
from gui.gamestats import QuickStatsTW, GeneralQuickStats, ParticularQuickStats

i18n = QApplication.translate


class SkullKingWidget(GameWidget):

    def createEngine(self):
        if self.game != 'Skull King':
            raise Exception("No engine for game {}".format(self.game))
            return
        self.engine = SkullKingEngine()

    def initUI(self):
        super(SkullKingWidget, self).initUI()

        self.gameInput = SkullKingInputWidget(self.engine, self)
        self.gameInput.enterPressed.connect(self.commitRound)
        self.roundLayout.addWidget(self.gameInput)

        self.configLayout = QGridLayout()
        self.matchGroupLayout.addLayout(self.configLayout)
        self.dealerPolicyCheckBox.hide()

        self.detailGroup = SkullKingRoundsDetail(self.engine, self)
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
        super(SkullKingWidget, self).retranslateUI()
        self.playerGroup.setTitle(i18n("GameWidget","Scoreboard"))
        self.detailGroup.retranslateUI()

    def setRoundTitle(self):
        super(SkullKingWidget, self).setRoundTitle()
        hands = self.engine.getHands()
        if hands == 1:
            self.roundGroup.setTitle("{} - {} {}".format(
                self.roundGroup.title(), str(hands),
                i18n("PochaWidget", "hand")))
        else:
            self.roundGroup.setTitle("{} - {} {}".format(
                self.roundGroup.title(), str(hands),
                i18n("PochaWidget", "hands")))

    def checkPlayerScore(self, player, score): return True

    def unsetDealer(
        self): self.playerGroupBox[self.engine.getDealer()].unsetDealer()

    def setDealer(
        self): self.playerGroupBox[self.engine.getDealer()].setDealer()

    def updatePanel(self):
        for player in self.players:
            score = self.engine.getScoreFromPlayer(player)
            self.playerGroupBox[player].updateDisplay(score)

        if self.engine.getWinner():
            self.detailGroup.updateStats()
        self.detailGroup.updateRound()
        super(SkullKingWidget, self).updatePanel()
        self.gameInput.setFocus()

    def setWinner(self):
        super(SkullKingWidget, self).setWinner()
        winner = self.engine.getWinner()
        if winner in self.players:
            self.playerGroupBox[winner].setWinner()

    def commitRound(self):
        hands = self.engine.getHands()
        wonhands = self.gameInput.getWonHands()
        won = sum(wonhands.values())
        if min(wonhands.values()) < 0:
            QMessageBox.warning(
                self, self.game,
                i18n("PochaWidget",
                     "There are players with no selected won hands."))
            return

        if hands != won:
            msg = i18n(
                "PochaWidget",
                "There are {} won hands selected when there should be {}.")
            QMessageBox.warning(
                self, self.game, msg.format(won, hands))
            return

        super(SkullKingWidget, self).commitRound()

    def setFocus(self):
        self.gameInput.setFocus()

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


class SkullKingInputWidget(GameInputWidget):

    def __init__(self, engine, parent=None):
        super(SkullKingInputWidget, self).__init__(engine, parent)
        self.initUI()
        self.lastChoices = []

    def initUI(self):
        self.widgetLayout = QGridLayout(self)
        players = self.engine.getListPlayers()
        if len(players) == 4:
            players_per_column = 2
        else:
            players_per_column = 3

        for i, player in enumerate(players):
            self.playerInputList[player] = SkullKingPlayerInputWidget(
                player, self.engine, PlayerColours[i], self)
            self.widgetLayout.addWidget(
                self.playerInputList[player], i // players_per_column, i % players_per_column)
            self.playerInputList[player].winnerSet.connect(self.changedWinner)
            self.playerInputList[player].newExpected.connect(
                self.checkExpected)
            self.playerInputList[player].handsClicked.connect(self.newChoice)

        print(f"trying to set focus to {self.engine.getListPlayers()[0]}")
        self.playerInputList[self.engine.getListPlayers()[0]].setFocus()

    def newChoice(self, mode, player):
        self.lastChoices.append((mode, player))

    def reset(self):
        super(SkullKingInputWidget, self).reset()
        self.lastChoices = []
        self.playerInputList[self.engine.getListPlayers()[0]].setFocus()

    def getScores(self):
        scores = {}
        for player, piw in self.playerInputList.items():
            scores[player] = piw.getScore()
        return scores

    def getWonHands(self):
        won = {}
        for player, piw in self.playerInputList.items():
            won[player] = piw.getWonHands()
        return won

    def getExpectedHands(self):
        expected = {}
        for player, piw in self.playerInputList.items():
            expected[player] = piw.getExpectedHands()
        return expected

    def checkExpected(self):
        for player, piw in self.playerInputList.items():
            piw.disableWonRow(piw.getExpectedHands() < 0)
            # print(f"CheckExpected {player}: {piw.getExpectedHands()} {piw.getWonHands()}")
            # piw.disableExtraRow(piw.getExpectedHands() != piw.getWonHands() or piw.getExpectedHands() < 1)

    def keyPressEvent(self, event):
        numberkeys = [QtCore.Qt.Key_0, QtCore.Qt.Key_1, QtCore.Qt.Key_2,
                      QtCore.Qt.Key_3, QtCore.Qt.Key_4, QtCore.Qt.Key_5,
                      QtCore.Qt.Key_6, QtCore.Qt.Key_7, QtCore.Qt.Key_8,
                      QtCore.Qt.Key_9]

        if (event.key() in (QtCore.Qt.Key_Backspace, QtCore.Qt.Key_Delete)):
            try:
                mode, player = self.lastChoices.pop()
                if mode == 'expected':
                    self.playerInputList[player].setExpectedHands(-1)
                else:
                    pil = self.playerInputList[player]
                    pil.setWonHands(-1)
                    pil.disableExtraRow(pil.getExpectedHands() != pil.getWonHands() or pil.getExpectedHands() < 1)
                event.accept()
                return super(SkullKingInputWidget, self).keyPressEvent(event)
            except IndexError:
                pass

        try:
            number = numberkeys.index(event.key())
        except ValueError:
            return super(SkullKingInputWidget, self).keyPressEvent(event)

        if number in range(0, 9):
            self.feedNumber(number)

        return super(SkullKingInputWidget, self).keyPressEvent(event)

    def feedNumber(self, number):
        players = self.engine.getListPlayers()
        expected_hands = self.getExpectedHands()
        won_hands = self.getWonHands()
        dealer = self.engine.getDealer()
        first_player = (players.index(dealer)+1) % len(players)
        hand_player_order = players[first_player:]+players[0:first_player]
        if any([value < 0 for value in expected_hands.values()]):
            for player in players:
                if expected_hands[player] < 0:
                    if self.playerInputList[player].setExpectedHands(number):
                        self.lastChoices.append(('expected', player))
                    return

        for player in players:
            if won_hands[player] < 0:
                if self.playerInputList[player].setWonHands(number):
                    self.lastChoices.append(('won', player))
                    pil = self.playerInputList[player]
                    pil.disableExtraRow(pil.getExpectedHands() != pil.getWonHands() or pil.getExpectedHands() < 1)
                return

        return

    def updatePlayerOrder(self):
        #         QWidget().setLayout(self.layout())
        trash = QWidget()
        trash.setLayout(self.layout())
        self.widgetLayout = QGridLayout(self)
        for i, player in enumerate(self.engine.getListPlayers()):
            trash.layout().removeWidget(self.playerInputList[player])
            self.widgetLayout.addWidget(
                self.playerInputList[player], i//4, i % 4)
            self.playerInputList[player].setColour(PlayerColours[i])


class SkullKingPlayerInputWidget(QFrame):

    winnerSet = QtCore.Signal(str)
    newExpected = QtCore.Signal()
    handsClicked = QtCore.Signal(str, str)

    def __init__(self, player, engine, colour=None, parent=None):
        super(SkullKingPlayerInputWidget, self).__init__(parent)
        self.player = player
        self.engine = engine
        self.winner = False
        self.pcolour = colour
        self.mainLayout = QVBoxLayout(self)
        self.mainLayout.setSpacing(0)

        self.label = QLabel(self)
        self.label.setText(self.player)
        self.mainLayout.addWidget(self.label)
        self.label.setAutoFillBackground(False)
        self.setFrameShape(QFrame.Panel)
        self.setFrameShadow(QFrame.Raised)
        self.label.setScaledContents(True)
        self.label.setAlignment(QtCore.Qt.AlignCenter)
        self.label.setWordWrap(False)
        css = ("QLabel {{ font-size: 24px; font-weight: bold; "
               "color:rgb({},{},{});}}")
        self.label.setStyleSheet(css.format(self.pcolour.red(),
                                            self.pcolour.green(),
                                            self.pcolour.blue()))

        self.expectedGroupBox = QFrame(self)
        self.mainLayout.addWidget(self.expectedGroupBox)
        self.ebLayout = QHBoxLayout(self.expectedGroupBox)
        self.ebLayout.setSpacing(0)
        self.ebLayout.setContentsMargins(2, 2, 2, 2)
        self.expectedGroup = QButtonGroup(self)
        self.expectedGroup.buttonReleased.connect(self.expectedClickedAction)
        self.expectedButtons = []

        self.wonGroupBox = QFrame(self)
        self.mainLayout.addWidget(self.wonGroupBox)
        self.wbLayout = QHBoxLayout(self.wonGroupBox)
        self.wbLayout.setSpacing(0)
        self.wbLayout.setContentsMargins(2, 2, 2, 2)
        self.wonGroup = QButtonGroup(self)
        self.wonGroup.buttonReleased.connect(self.wonClickedAction)
        self.wonButtons = []
        for i in range(-1, 11):
            button = SkullKingHandsButton(str(i), self)
            self.expectedGroup.addButton(button, i)
            self.expectedButtons.append(button)
            button.toggled.connect(self.enableWonGroup)
            if i < 0:
                button.hide()
            else:
                self.ebLayout.addWidget(button)

            button = SkullKingHandsButton(str(i), self)
            self.wonGroup.addButton(button, i)
            self.wonButtons.append(button)
            if i < 0:
                button.hide()
            else:
                self.wbLayout.addWidget(button)
        self.extraPointsGroup = QFrame(self)
        self.mainLayout.addWidget(self.extraPointsGroup)
        self.epLayout = QHBoxLayout(self.extraPointsGroup)
        self.epLayout.setSpacing(0)
        self.epLayout.setContentsMargins(2, 2, 2, 2)
        self.skullKingCaptured = QCheckBox("SKC", self.extraPointsGroup)
        self.epLayout.addWidget(self.skullKingCaptured)
        self.piratesCaptured = ScoreSpinBox(self.extraPointsGroup)
        self.epLayout.addWidget(self.piratesCaptured)
        self.piratesCapturedLabel = QLabel("PC", self.extraPointsGroup)
        self.epLayout.addWidget(self.piratesCapturedLabel)
        self.reset()

    def reset(self):
        self.expectedButtons[0].setChecked(True)
        self.wonButtons[0].setChecked(True)
        self.skullKingCaptured.setChecked(False)
        self.piratesCaptured.setValue(0)
        self.piratesCaptured.clear()
        self.refreshButtons()
        self.disableWonRow()
        self.disableExtraRow()

    def refreshButtons(self, forbidden=-1):
        hands = self.engine.getHands()
        for eb, wb in zip(self.expectedButtons, self.wonButtons):
            eb.setDisabled(int(eb.text()) > hands)
            if int(eb.text()) == forbidden:
                eb.setDisabled(True)
            wb.setDisabled(int(wb.text()) > hands)

    def disableWonRow(self, disable=True):
        if self.getExpectedHands() < 0:
            self.wonGroupBox.setDisabled(True)
        else:
            self.wonGroupBox.setDisabled(disable)

    def disableExtraRow(self, disable=True):
        self.extraPointsGroup.setDisabled(disable)

    def enableWonGroup(self, button):
        self.newExpected.emit()

    def isWinner(self): return False

    def getPlayer(self): return self.player

    def getScore(self):
        expected = self.expectedGroup.checkedId()
        won = self.wonGroup.checkedId()
        if expected == 0 and won == 0:
            return self.engine.getNumRound() * 10
        if expected == 0 and won != 0:
            return self.engine.getNumRound() * -10
        if expected == won:
            return won * 20 + 30 * int(self.piratesCaptured.value()) + 50 * int(self.skullKingCaptured.isChecked())
        return -10 * abs(expected - won) 

    def getWonHands(self): return self.wonGroup.checkedId()

    def getExpectedHands(self): return self.expectedGroup.checkedId()

    def setExpectedHands(self, number):
        if number < 0:
            self.expectedButtons[0].toggle()
            return True
        button = self.expectedGroup.button(number)
        if button.isEnabled():
            button.toggle()
            return True
        return False

    def setWonHands(self, number):
        if number < 0:
            self.wonButtons[0].toggle()
            return True
        button = self.wonGroup.button(number)
        if button.isEnabled():
            button.toggle()
            return True
        return False

    def expectedClickedAction(self, _):
        self.handsClicked.emit('expected', self.player)

    def wonClickedAction(self, _):
        self.disableExtraRow(self.getExpectedHands() != self.getWonHands() or self.getExpectedHands() < 1)
        self.handsClicked.emit('won', self.player)

    def setColour(self, colour):
        self.pcolour = colour
        css = ("QLabel {{ font-size: 24px; font-weight: bold; "
               "color:rgb({},{},{});}}")
        self.label.setStyleSheet(css.format(self.pcolour.red(),
                                            self.pcolour.green(),
                                            self.pcolour.blue()))


class SkullKingHandsButton(QPushButton):

    def __init__(self, text="", parent=None):
        super(SkullKingHandsButton, self).__init__(text, parent)
        self.setCheckable(True)
        self.setMinimumSize(25, 25)
        self.setSizePolicy(QSizePolicy.MinimumExpanding,
                           QSizePolicy.Maximum)
        self.toggled.connect(self.setColour)
        self.setColour(False)

    def setColour(self, toggle):
        return
        if toggle:
            self.setStyleSheet("background-color: red; font: bold")
        else:
            self.setStyleSheet("background-color: green; font: normal")

    def setDisabled(self, disabled=True):
        if disabled:
            self.setStyleSheet("background-color: none; font: normal")
        else:
            self.setColour(self.isChecked())
        return super(SkullKingHandsButton, self).setDisabled(disabled)


class SkullKingRoundsDetail(GameRoundsDetail):

    def __init__(self, engine, parent=None):
        self.bgcolors = [0xCCFF99, 0xFFCC99]
        super(SkullKingRoundsDetail, self).__init__(engine, parent)

    def createRoundTable(self, engine, parent=None):
        return SkullKingRoundTable(self.engine, self.bgcolors, parent)

    def createRoundPlot(self, engine, parent=None):
        return SkullKingRoundPlot(self.engine, self)

    def createQSBox(self, parent=None):
        return SkullKingQSTW(self.engine.getGame(),
                         self.engine.getListPlayers(), self)


class SkullKingRoundTable(GameRoundTable):

    def __init__(self, engine, bgcolors, parent=None):
        self.bgcolors = bgcolors
        super(SkullKingRoundTable, self).__init__(engine, parent)

    def insertRound(self, r):
        winner = r.getWinner()
        i = r.getNumRound() - 1
        self.insertRow(i)
        hands = self.engine.getHands(r.getNumRound())
        hitem = QTableWidgetItem("{}".format(hands))
        self.setVerticalHeaderItem(i, hitem)

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
                text += i18n("PochaWidget", " (Winner)")
            item.setText(text)
            self.setItem(i, j, item)
        self.scrollToBottom()


class SkullKingRoundPlot(GameRoundPlot):

    def updatePlot(self):
        super(SkullKingRoundPlot, self).updatePlot()
        if not self.isPlotInited():
            return
        scores = {}
        roundNames = ['']
        for player in self.engine.getPlayers():
            scores[player] = [0]

        for rnd in self.engine.getRounds():
            hands = self.engine.getHands(rnd.getNumRound())
            roundNames.append("{}".format(hands))
            for player in self.engine.getPlayers():
                rndscore = rnd.getPlayerScore(player)
                accumscore = scores[player][-1] + rndscore
                scores[player].append(accumscore)

        self.canvas.addHHeaders(roundNames)
        self.canvas.clearPlotContents()
        for player in self.engine.getListPlayers():
            self.canvas.addSeries(scores[player], player)


class SkullKingQSTW(QuickStatsTW):
    def initStatsWidgets(self):
        self.gs = SkullKingQSBox(self.game, self)
        self.ps = SkullKingPQSBox(self.game, self)


class SkullKingQSBox(GeneralQuickStats):
    pass

class SkullKingPQSBox(SkullKingQSBox, ParticularQuickStats):
    pass
