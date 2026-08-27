from typing import cast

from PySide6 import QtCore, QtGui
from PySide6.QtCore import QCoreApplication
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QButtonGroup,
    QFrame,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QMessageBox,
    QPushButton,
    QRadioButton,
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
)
from core.ui.gamestats import GeneralQuickStats, ParticularQuickStats, QuickStatsTW
from core.ui.progress import StepProgressBar
from games.pocha.engine import PochaEngine


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
            raise GameNotImplementedException(f"No engine for game {self.game}")
        self.engine = PochaEngine()

    def initUI(self):
        super().initUI()
        self.retranslateUI()

    def createGameInputWidget(self, parent=None):
        return PochaInputWidget(self.engine, parent)

    def createRoundsDetail(self, parent=None):
        return PochaRoundsDetail(self.engine, parent)

    def retranslateUI(self):
        super().retranslateUI()
        self.spanishSuitRadio.setText(self.tr("Spanish Deck"))
        self.frenchSuitRadio.setText(self.tr("French Deck"))
        self.detailGroup.retranslateUI()

    def addExtraConfig(self):
        super().addExtraConfig()
        self.progressBar = StepProgressBar(self.engine.getRoundSequence(), self)
        self.progressBar.setCurrentStep(self.engine.getNumRound() - 1)
        # self.matchGroupLayout.addWidget(self.progressBar)
        self.matchGroupLayout.insertWidget(1, self.progressBar)

        self.configLayout = QGridLayout()
        # self.matchGroupLayout.insertLayout(3, self.configLayout)
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

    def changeSuit(self, *_args):
        if self.spanishSuitRadio.isChecked():
            self.engine.setSuitType("spansih")
        elif self.frenchSuitRadio.isChecked():
            self.engine.setSuitType("french")
        self.retranslateUI()

    def setRoundTitle(self):
        if self.engine.getWinner():
            self.roundTitleLabel.setText(f"{self.engine.getGame()}")
            return
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

    def checkPlayerScore(self, player, score, extras=None):
        return True

    def updatePanel(self):
        super().updatePanel()
        self.progressBar.setCurrentStep(self.engine.getNumRound() - 1)
        # self.spanishSuitRadio.setDisabled(self.engine.getNumRound() > 1)
        # self.frenchSuitRadio.setDisabled(self.engine.getNumRound() > 1)

    def commitRoundSanityCheck(self, interactive=False):
        hands = self.engine.getHands()
        wonhands = cast(PochaInputWidget, self.gameInput).getWonHands()
        won = sum(wonhands.values())
        if min(wonhands.values()) < 0:
            msg = self.tr("There are players with no selected won hands.")
            if interactive:
                QMessageBox.warning(
                    self,
                    self.game,
                    msg,
                )
            return False

        if hands != won:
            msg = self.tr("There are {} won hands selected when there should be {}.")
            if interactive:
                QMessageBox.warning(self, self.game, msg.format(won, hands))
            return False
        return True

    def setFocus(self, _reason=None):
        self.gameInput.setFocus()


class PochaInputWidget(GameInputWidget):
    def __init__(self, engine, parent=None):
        super().__init__(engine, parent)
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
            self.playerInputList[player].changed.connect(self.changed)

    def newChoice(self, mode, player):
        self.lastChoices.append((mode, player))

    def reset(self):
        super().reset()
        self.lastChoices = []

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
                return super().keyPressEvent(event)
            except IndexError:
                pass

        try:
            number = numberkeys.index(event.key())
        except ValueError:
            return super().keyPressEvent(event)

        if number in range(9):
            self.feedNumber(number)

        return super().keyPressEvent(event)

    def feedNumber(self, number):
        players = self.engine.getListPlayers()
        expected_hands = self.getExpectedHands()
        won_hands = self.getWonHands()
        dealer = self.engine.getDealer()
        first_player = (players.index(dealer) + 1) % len(players)
        hand_player_order = players[first_player:] + players[0:first_player]
        if any(value < 0 for value in expected_hands.values()):
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


class PochaPlayerInputWidget(QGroupBox):
    winnerSet = QtCore.Signal(str)
    newExpected = QtCore.Signal()
    handsClicked = QtCore.Signal(str, str)
    changed = QtCore.Signal()

    def __init__(self, player, engine, colour=None, parent=None):
        super().__init__(parent)
        self.player = player
        self.engine = engine
        self.winner = False
        self.pcolour = colour if colour else QColor(0, 0, 0)
        self.mainLayout = QVBoxLayout(self)
        self.mainLayout.setSpacing(0)

        self.setTitle(self.player)

        self.expectedGroupBox = QFrame(self)
        self.mainLayout.addWidget(self.expectedGroupBox)
        self.ebLayout = QHBoxLayout(self.expectedGroupBox)
        self.ebLayout.setSpacing(2)
        self.ebLayout.setContentsMargins(2, 2, 2, 2)
        self.expectedGroup = QButtonGroup(self)
        self.expectedGroup.buttonReleased.connect(self.expectedClickedAction)
        self.expectedButtons = []

        self.wonGroupBox = QFrame(self)
        self.mainLayout.addWidget(self.wonGroupBox)
        self.wbLayout = QHBoxLayout(self.wonGroupBox)
        self.wbLayout.setSpacing(2)
        self.wbLayout.setContentsMargins(2, 2, 2, 2)
        self.wonGroup = QButtonGroup(self)
        self.wonGroup.buttonReleased.connect(self.wonClickedAction)
        self.wonButtons = []
        for i in range(-1, 9):
            button = PochaHandsButton(str(i), self)
            self.expectedGroup.addButton(button, i)
            self.expectedButtons.append(button)
            button.toggled.connect(self.enableWonGroup)
            button.toggled.connect(self.changed)
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
            button.toggled.connect(self.changed)

        self.setColour(self.pcolour)
        self.reset()

    def reset(self):
        self.expectedButtons[0].setChecked(True)
        self.wonButtons[0].setChecked(True)
        self.refreshButtons()
        self.disableWonRow()

    def refreshButtons(self, forbidden=-1):
        hands = self.engine.getHands()
        for eb, wb in zip(self.expectedButtons, self.wonButtons, strict=False):
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
        css = f"""
            QGroupBox {{ font-size: 24px; font-weight: bold; color: {self.pcolour.name()}; }}
            QGroupBox:focus-within {{ border: 2px solid #0078d7; background-color: #e6f1fb;}}
            QGroupBox::title {{
                    subcontrol-origin: margin;
                    subcontrol-position: top center;
                    padding: 0 10px;
                    background-color: transparent;
            }}

            QPushButton {{
                padding: 2px 2px;
            }}

            QPushButton:checked {{
                background: {self.pcolour.name()};
                border: 1px solid {self.pcolour.name()};
            }}

            QPushButton:checked:hover {{
                background: {self.pcolour.name()};
            }}
        """
        self.setStyleSheet(css)


class PochaHandsButton(QPushButton):
    def __init__(self, text="", parent=None):
        super().__init__(text, parent)
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
        return super().setDisabled(disabled)
        if disabled:
            self.setStyleSheet("background-color: none; font: normal")
        else:
            self.setColour(self.isChecked())
        return super().setDisabled(disabled)


class PochaRoundsDetail(GameRoundsDetail):
    def __init__(self, engine, parent=None):
        self.bgcolors = [0xCCFF99, 0xFFCC99]
        super().__init__(engine, parent)
        self.setCurrentWidget(self.plot)

    def createRoundTable(self, engine, parent=None):
        return PochaRoundTable(self.engine, self.bgcolors, parent)

    def createRoundPlot(self, engine, parent=None):
        return PochaRoundPlot(self.engine, self)

    def createQSBox(self, parent=None):
        return PochaQSTW(self.engine.getGame(), self.engine.getListPlayers(), self)


class PochaRoundTable(GameRoundTable):
    def __init__(self, engine, bgcolors, parent=None):
        self.bgcolors = bgcolors
        super().__init__(engine, parent)

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
        super().updatePlot()
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
        super().__init__(gname, parent)
        self.playerStatsKeys.append("max_hits")
        self.playerStatsHeaders.append("Max Hits")
        self.playerStatsKeys.append("min_hits")
        self.playerStatsHeaders.append("Min Hits")
        self.playerStatsKeys.append("max_round_score")
        self.playerStatsHeaders.append("Best Round")
        for i in ("minscore", "sumscore"):
            try:
                self.playerStatsKeys.remove(i)
            except KeyError:
                pass
        for i in ("Lowest", "Total"):
            try:
                self.playerStatsHeaders.remove(i)
            except KeyError:
                pass


class PochaPQSBox(PochaQSBox, ParticularQuickStats):
    pass
