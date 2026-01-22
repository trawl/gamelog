#!/usr/bin/env python
# -*- coding: utf-8 -*-
from typing import cast

from PySide6 import QtCore, QtGui
from PySide6.QtCore import QCoreApplication
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QButtonGroup,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QRadioButton,
    QSizePolicy,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from controllers.pochaengine import PochaEngine
from gui.game import (
    GameInputWidget,
    GamePlayerWidget,
    GameRoundPlot,
    GameRoundsDetail,
    GameRoundTable,
    GameWidget,
    PlayerColours,
)
from gui.gamestats import GeneralQuickStats, ParticularQuickStats, QuickStatsTW
from gui.progress import StepProgressBar


class PochaWidget(GameWidget):
    QCoreApplication.translate("PochaWidget", "going up")
    QCoreApplication.translate("PochaWidget", "going down")
    QCoreApplication.translate("PochaWidget", "hand")
    QCoreApplication.translate("PochaWidget", "hands")
    QCoreApplication.translate("PochaWidget", "coins")
    QCoreApplication.translate("PochaWidget", "cups")
    QCoreApplication.translate("PochaWidget", "swords")
    QCoreApplication.translate("PochaWidget", "clubs")
    QCoreApplication.translate("PochaWidget", "diamonds")
    QCoreApplication.translate("PochaWidget", "hearts")
    QCoreApplication.translate("PochaWidget", "spades")
    QCoreApplication.translate("PochaWidget", "clovers")

    def createEngine(self):
        if self.game != "Pocha":
            raise Exception("No engine for game {}".format(self.game))
        self.engine = PochaEngine()

    def initUI(self):
        super(PochaWidget, self).initUI()

        self.gameInput = PochaInputWidget(self.engine, self)
        self.gameInput.enterPressed.connect(self.commitRound)
        self.roundLayout.addWidget(self.gameInput)

        self.progressBar = StepProgressBar(self.engine.getRoundSequence(), self)
        self.progressBar.setCurrentStep(self.engine.getNumRound() - 1)
        self.matchGroupLayout.addWidget(self.progressBar)

        self.configLayout = QGridLayout()
        self.matchGroupLayout.addLayout(self.configLayout)
        self.suitTypeGroup = QButtonGroup(self)
        self.spanishSuitRadio = QRadioButton(self)
        self.spanishSuitRadio.setChecked(self.engine.getSuitType() == "spanish")
        self.spanishSuitRadio.toggled.connect(self.changeSuit)
        self.suitTypeGroup.addButton(self.spanishSuitRadio)
        self.configLayout.addWidget(self.spanishSuitRadio)
        self.frenchSuitRadio = QRadioButton(self)
        self.suitTypeGroup.addButton(self.frenchSuitRadio)
        self.configLayout.addWidget(self.frenchSuitRadio)
        self.frenchSuitRadio.setChecked(self.engine.getSuitType() == "french")

        self.dealerPolicyCheckBox.hide()

        self.detailGroup = PochaRoundsDetail(self.engine, self)
        self.detailGroup.edited.connect(self.updatePanel)
        # self.widgetLayout.addWidget(self.detailGroup, 1, 0)
        self.leftLayout.addWidget(self.detailGroup)

        # self.playerGroup = QGroupBox(self)
        # # self.widgetLayout.addWidget(self.playerGroup, 1, 1)
        # self.rightLayout.addWidget(self.playerGroup)

        # self.playerGroup.setStyleSheet(
        #     "QGroupBox { font-size: 18px; font-weight: bold; }"
        # )
        # self.playersLayout = QVBoxLayout(self.playerGroup)
        # self.playersLayout.addStretch()
        self.playersLayout = QVBoxLayout()
        self.matchGroupLayout.addLayout(self.playersLayout)
        self.playerGroupBox = {}
        for i, player in enumerate(self.players):
            pw = GamePlayerWidget(player, PlayerColours[i], self.matchGroup)
            pw.updateDisplay(self.engine.getScoreFromPlayer(player))
            if player == self.engine.getDealer():
                pw.setDealer()
            self.playersLayout.addWidget(pw)
            self.playerGroupBox[player] = pw

        # self.playersLayout.addStretch()

        self.retranslateUI()

    def retranslateUI(self):
        super(PochaWidget, self).retranslateUI()
        #         self.playerGroup.setTitle(i18n("PochaWidget","Score"))
        self.spanishSuitRadio.setText(self.tr("Spanish Deck"))
        self.frenchSuitRadio.setText(self.tr("French Deck"))
        # self.playerGroup.setTitle(self.tr("Scoreboard"))
        self.detailGroup.retranslateUI()

    def changeSuit(self, *_args):
        if self.spanishSuitRadio.isChecked():
            self.engine.setSuitType("spansih")
        elif self.frenchSuitRadio.isChecked():
            self.engine.setSuitType("french")
        self.retranslateUI()

    def setRoundTitle(self):
        super(PochaWidget, self).setRoundTitle()
        hands = self.engine.getHands()
        direction = self.engine.getDirection()
        if hands == 1:
            self.roundTitleLabel.setText(
                "{} - {} {} {}".format(
                    self.engine.getGame(),
                    str(hands),
                    self.tr("hand"),
                    self.tr(direction),
                )
            )
        else:
            self.roundTitleLabel.setText(
                "{} - {} {} {}".format(
                    self.engine.getGame(),
                    str(hands),
                    self.tr("hands"),
                    self.tr(direction),
                )
            )

    def checkPlayerScore(self, player, score):
        return True

    def unsetDealer(self):
        self.playerGroupBox[self.engine.getDealer()].unsetDealer()

    def setDealer(self):
        self.playerGroupBox[self.engine.getDealer()].setDealer()

    def updatePanel(self):
        self.progressBar.setCurrentStep(self.engine.getNumRound() - 1)
        for player in self.players:
            score = self.engine.getScoreFromPlayer(player)
            self.playerGroupBox[player].updateDisplay(score)

        if self.engine.getWinner():
            self.detailGroup.updateStats()
        self.detailGroup.updateRound()
        super(PochaWidget, self).updatePanel()
        self.gameInput.setFocus()

    def setWinner(self):
        super(PochaWidget, self).setWinner()
        winner = self.engine.getWinner()
        if winner in self.players:
            self.playerGroupBox[winner].setWinner()

    def commitRound(self):
        hands = self.engine.getHands()
        wonhands = self.gameInput.getWonHands()
        won = sum(wonhands.values())
        if min(wonhands.values()) < 0:
            QMessageBox.warning(
                self,
                self.game,
                self.tr("There are players with no selected won hands."),
            )
            return

        if hands != won:
            msg = self.tr("There are {} won hands selected when there should be {}.")
            QMessageBox.warning(self, self.game, msg.format(won, hands))
            return

        super(PochaWidget, self).commitRound()

    def setFocus(self, _reason=None):
        self.gameInput.setFocus()

    def updatePlayerOrder(self):
        GameWidget.updatePlayerOrder(self)
        # self.playersLayout.addStretch()
        for player in self.engine.getListPlayers():
            self.playersLayout.removeWidget(self.playerGroupBox[player])

        for i, player in enumerate(self.engine.getListPlayers()):
            self.playersLayout.addWidget(self.playerGroupBox[player])
            self.playerGroupBox[player].setColour(PlayerColours[i])
        # self.playersLayout.addStretch()
        self.detailGroup.updatePlayerOrder()


class PochaInputWidget(GameInputWidget):
    def __init__(self, engine, parent=None):
        super(PochaInputWidget, self).__init__(engine, parent)
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
            self.playerInputList[player] = PochaPlayerInputWidget(
                player, self.engine, PlayerColours[i], self
            )
            self.widgetLayout.addWidget(
                self.playerInputList[player],
                i // players_per_column,
                i % players_per_column,
            )
            self.playerInputList[player].winnerSet.connect(self.changedWinner)
            self.playerInputList[player].newExpected.connect(self.checkExpected)
            self.playerInputList[player].handsClicked.connect(self.newChoice)

    def newChoice(self, mode, player):
        self.lastChoices.append((mode, player))

    def reset(self):
        super(PochaInputWidget, self).reset()
        self.lastChoices = []

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
        notselected = []
        totalexpected = 0
        hands = self.engine.getHands()
        for player, piw in self.playerInputList.items():
            expected = piw.getExpectedHands()
            if expected < 0:
                notselected.append(player)
            else:
                totalexpected += expected

        forbidden = hands - totalexpected

        for player, piw in self.playerInputList.items():
            if len(notselected) == 1 and player in notselected and forbidden >= 0:
                piw.refreshButtons(forbidden)
            else:
                piw.refreshButtons()
            piw.disableWonRow(len(notselected) == 0 and forbidden == 0)

    def keyPressEvent(self, event):
        numberkeys = [
            QtCore.Qt.Key.Key_0,
            QtCore.Qt.Key.Key_1,
            QtCore.Qt.Key.Key_2,
            QtCore.Qt.Key.Key_3,
            QtCore.Qt.Key.Key_4,
            QtCore.Qt.Key.Key_5,
            QtCore.Qt.Key.Key_6,
            QtCore.Qt.Key.Key_7,
            QtCore.Qt.Key.Key_8,
        ]

        if event.key() in (QtCore.Qt.Key.Key_Backspace, QtCore.Qt.Key.Key_Delete):
            try:
                mode, player = self.lastChoices.pop()
                if mode == "expected":
                    self.playerInputList[player].setExpectedHands(-1)
                else:
                    self.playerInputList[player].setWonHands(-1)
                event.accept()
                return super(PochaInputWidget, self).keyPressEvent(event)
            except IndexError:
                pass

        try:
            number = numberkeys.index(event.key())
        except ValueError:
            return super(PochaInputWidget, self).keyPressEvent(event)

        if number in range(0, 9):
            self.feedNumber(number)

        return super(PochaInputWidget, self).keyPressEvent(event)

    def feedNumber(self, number):
        players = self.engine.getListPlayers()
        expected_hands = self.getExpectedHands()
        won_hands = self.getWonHands()
        dealer = self.engine.getDealer()
        first_player = (players.index(dealer) + 1) % len(players)
        hand_player_order = players[first_player:] + players[0:first_player]
        if any([value < 0 for value in expected_hands.values()]):
            for player in hand_player_order:
                if expected_hands[player] < 0:
                    if self.playerInputList[player].setExpectedHands(number):
                        self.lastChoices.append(("expected", player))
                    return

        for player in hand_player_order:
            if won_hands[player] < 0:
                if self.playerInputList[player].setWonHands(number):
                    self.lastChoices.append(("won", player))
                return

        return

    def updatePlayerOrder(self):
        #         QWidget().setLayout(self.layout())
        trash = QWidget()
        trash_layout = self.layout()
        if trash_layout:
            trash.setLayout(trash_layout)
        self.widgetLayout = QGridLayout(self)
        for i, player in enumerate(self.engine.getListPlayers()):
            if trash_layout:
                trash_layout.removeWidget(self.playerInputList[player])
            self.widgetLayout.addWidget(self.playerInputList[player], i // 4, i % 4)
            self.playerInputList[player].setColour(PlayerColours[i])


class PochaPlayerInputWidget(QFrame):
    winnerSet = QtCore.Signal(str)
    newExpected = QtCore.Signal()
    handsClicked = QtCore.Signal(str, str)

    def __init__(self, player, engine, colour=QColor(0, 0, 0), parent=None):
        super(PochaPlayerInputWidget, self).__init__(parent)
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
        self.setFrameShape(QFrame.Shape.Panel)
        self.setFrameShadow(QFrame.Shadow.Raised)
        self.label.setScaledContents(True)
        self.label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.label.setWordWrap(False)
        css = "QLabel {{ font-size: 24px; font-weight: bold; color:rgb({},{},{});}}"
        self.label.setStyleSheet(
            css.format(self.pcolour.red(), self.pcolour.green(), self.pcolour.blue())
        )

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
        for i in range(-1, 9):
            button = PochaHandsButton(str(i), self)
            self.expectedGroup.addButton(button, i)
            self.expectedButtons.append(button)
            button.toggled.connect(self.enableWonGroup)
            if i < 0:
                button.hide()
            else:
                self.ebLayout.addWidget(button)

            button = PochaHandsButton(str(i), self)
            self.wonGroup.addButton(button, i)
            self.wonButtons.append(button)
            if i < 0:
                button.hide()
            else:
                self.wbLayout.addWidget(button)

        self.reset()

    def reset(self):
        self.expectedButtons[0].setChecked(True)
        self.wonButtons[0].setChecked(True)
        self.refreshButtons()
        self.disableWonRow()

    def refreshButtons(self, forbidden=-1):
        hands = self.engine.getHands()
        for eb, wb in zip(self.expectedButtons, self.wonButtons):
            if int(eb.text()) > hands or int(eb.text()) < 0:
                eb.hide()
            else:
                eb.show()
            if int(wb.text()) > hands or int(eb.text()) < 0:
                wb.hide()
            else:
                wb.show()
            eb.setDisabled(int(eb.text()) > hands)
            if int(eb.text()) == forbidden:
                eb.setDisabled(True)
            wb.setDisabled(int(wb.text()) > hands)

    def disableWonRow(self, disable=True):
        if self.getExpectedHands() < 0:
            self.wonGroupBox.setDisabled(True)
        else:
            self.wonGroupBox.setDisabled(disable)

    def enableWonGroup(self, _button):
        self.newExpected.emit()

    def isWinner(self):
        return False

    def getPlayer(self):
        return self.player

    def getScore(self):
        expected = self.expectedGroup.checkedId()
        won = self.wonGroup.checkedId()
        if expected < 0 or won < 0:
            return 0
        if expected == won:
            return 10 + 3 * won
        return -3 * abs(expected - won)

    def getWonHands(self):
        return self.wonGroup.checkedId()

    def getExpectedHands(self):
        return self.expectedGroup.checkedId()

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
        self.handsClicked.emit("expected", self.player)

    def wonClickedAction(self, _):
        self.handsClicked.emit("won", self.player)

    def setColour(self, colour):
        self.pcolour = colour
        css = "QLabel {{ font-size: 24px; font-weight: bold; color:rgb({},{},{});}}"
        self.label.setStyleSheet(
            css.format(self.pcolour.red(), self.pcolour.green(), self.pcolour.blue())
        )


class PochaHandsButton(QPushButton):
    def __init__(self, text="", parent=None):
        super(PochaHandsButton, self).__init__(text, parent)
        self.setCheckable(True)
        self.setMinimumSize(25, 25)
        self.setSizePolicy(
            QSizePolicy.Policy.MinimumExpanding, QSizePolicy.Policy.Maximum
        )
        self.toggled.connect(self.setColour)
        self.setColour(False)

    def setColour(self, _toggle):
        return
        # if _toggle:
        #     self.setStyleSheet("background-color: red; font: bold")
        # else:
        #     self.setStyleSheet("background-color: lightgreen; font: normal")

    def setDisabled(self, disabled=True):
        if disabled:
            self.setStyleSheet("background-color: none; font: normal")
        else:
            self.setColour(self.isChecked())
        return super(PochaHandsButton, self).setDisabled(disabled)


class PochaRoundsDetail(GameRoundsDetail):
    def __init__(self, engine, parent=None):
        self.bgcolors = [0xCCFF99, 0xFFCC99]
        super(PochaRoundsDetail, self).__init__(engine, parent)
        self.container.setCurrentWidget(self.plot)

    def createRoundTable(self, engine, parent=None):
        return PochaRoundTable(self.engine, self.bgcolors, parent)

    def createRoundPlot(self, engine, parent=None):
        return PochaRoundPlot(self.engine, self)

    def createQSBox(self, parent=None):
        return PochaQSTW(self.engine.getGame(), self.engine.getListPlayers(), self)


class PochaRoundTable(GameRoundTable):
    def __init__(self, engine, bgcolors, parent=None):
        self.bgcolors = bgcolors
        super(PochaRoundTable, self).__init__(engine, parent)

    def insertRound(self, r):
        winner = r.getWinner()
        i = r.getNumRound() - 1
        self.insertRow(i)
        hands = self.engine.getHands(r.getNumRound())
        direction = self.engine.getDirection(r.getNumRound())
        hitem = QTableWidgetItem(
            "{} {}".format(hands, QCoreApplication.translate("PochaWidget", direction))
        )
        self.setVerticalHeaderItem(i, hitem)

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


class PochaRoundPlot(GameRoundPlot):
    def retranslatePlot(self):
        self.updatePlot()

    def updatePlot(self):
        super(PochaRoundPlot, self).updatePlot()
        if not self.isPlotInited():
            return
        scores = {}
        roundNames = [""]
        for player in self.engine.getPlayers():
            scores[player] = [0]

        for i, hands in enumerate(cast(PochaEngine, self.engine).getRoundSequence()):
            direction = self.engine.getDirection(i + 1)
            roundNames.append(
                "{} {}".format(
                    hands, QCoreApplication.translate("PochaWidget", direction)
                )
            )

        for rnd in self.engine.getRounds():
            for player in self.engine.getPlayers():
                rndscore = rnd.getPlayerScore(player)
                accumscore = scores[player][-1] + rndscore
                scores[player].append(accumscore)

        self.canvas.addHHeaders(roundNames)
        self.canvas.clearPlotContents()
        for player in self.engine.getListPlayers():
            self.canvas.addSeries(scores[player], player)

        self.canvas._scene.update()


class PochaQSTW(QuickStatsTW):
    def initStatsWidgets(self):
        self.gs = PochaQSBox(self.game, self)
        self.ps = PochaPQSBox(self.game, self)


class PochaQSBox(GeneralQuickStats):
    QCoreApplication.translate("GeneralQuickStats", "Max Hits")
    QCoreApplication.translate("GeneralQuickStats", "Min Hits")
    QCoreApplication.translate("GeneralQuickStats", "Best Round")

    def __init__(self, gname, parent):
        super(PochaQSBox, self).__init__(gname, parent)
        self.playerStatsKeys.append("max_hits")
        self.playerStatsHeaders.append("Max Hits")
        self.playerStatsKeys.append("min_hits")
        self.playerStatsHeaders.append("Min Hits")
        self.playerStatsKeys.append("max_round_score")
        self.playerStatsHeaders.append("Best Round")


class PochaPQSBox(PochaQSBox, ParticularQuickStats):
    pass
