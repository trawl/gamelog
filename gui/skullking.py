#!/usr/bin/env python
# -*- coding: utf-8 -*-

from typing import cast

from PySide6 import QtCore, QtGui
from PySide6.QtCore import (
    Property,
    QCoreApplication,
    QEasingCurve,
    QPropertyAnimation,
    QRectF,
    Qt,
    QTimer,
)
from PySide6.QtGui import QColor, QFont, QImage, QPainter, QPainterPath
from PySide6.QtWidgets import (
    QComboBox,
    QFrame,
    QGraphicsColorizeEffect,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QSizePolicy,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from controllers.skullkingengine import SkullKingEngine
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

i18n = QCoreApplication.translate


class SkullKingWidget(GameWidget):
    QCoreApplication.translate("SkullKingWidget", "classic_scoring")
    QCoreApplication.translate("SkullKingWidget", "standard_scoring")
    QCoreApplication.translate("SkullKingWidget", "rascal_scoring")
    QCoreApplication.translate("SkullKingWidget", "standard_rounds")
    QCoreApplication.translate("SkullKingWidget", "even")
    QCoreApplication.translate("SkullKingWidget", "brawl")
    QCoreApplication.translate("SkullKingWidget", "skirmish")
    QCoreApplication.translate("SkullKingWidget", "barrage")
    QCoreApplication.translate("SkullKingWidget", "whirlpool")

    def createEngine(self):
        if self.game != "Skull King":
            raise Exception("No engine for game {}".format(self.game))
        self.engine = SkullKingEngine()

    def initUI(self):
        super(SkullKingWidget, self).initUI()

        self.gameInput = SkullKingInputWidget(self.engine, self)
        self.gameInput.enterPressed.connect(self.commitRound)
        self.roundLayout.addWidget(self.gameInput)
        # self.roundTitleLabel.hide()
        self.progressBar = StepProgressBar(self.engine.getRoundSequence(), self)
        self.progressBar.setCurrentStep(self.engine.getNumRound() - 1)
        self.matchGroupLayout.addWidget(self.progressBar)

        self.configLayout = QVBoxLayout()
        self.matchGroupLayout.addLayout(self.configLayout)
        self.dealerPolicyCheckBox.hide()

        # self.scoringModeLabel = QLabel(self.tr("Scoring"), self)
        # self.configLayout.addWidget(self.scoringModeLabel, 0, 0)
        self.scoringModeCombo = QComboBox(self)
        self.scoringModeCombo.addItems(
            [
                self.tr(m)
                for m in cast("SkullKingEngine", self.engine).listScoringModes()
            ]
        )
        self.scoringModeCombo.setCurrentText(
            self.tr(cast("SkullKingEngine", self.engine).getScoringMode())
        )
        self.scoringModeCombo.currentIndexChanged.connect(self.changeScoringMode)
        self.configLayout.addWidget(self.scoringModeCombo)

        # self.roundModeLabel = QLabel(self.tr("Card Counts"), self)
        # self.configLayout.addWidget(self.roundModeLabel, 1, 0)
        self.roundModeCombo = QComboBox(self)
        self.roundModeCombo.addItems(
            [self.tr(m) for m in cast("SkullKingEngine", self.engine).listRoundModes()]
        )
        self.roundModeCombo.setCurrentText(
            self.tr(cast("SkullKingEngine", self.engine).getRoundMode())
        )
        self.roundModeCombo.currentIndexChanged.connect(self.changeRoundMode)
        self.configLayout.addWidget(self.roundModeCombo)

        self.enableConfigCombos(self.engine.getNumRound() == 1)

        self.detailGroup = SkullKingRoundsDetail(self.engine, self)
        self.detailGroup.edited.connect(self.updatePanel)
        # self.widgetLayout.addWidget(self.detailGroup, 1, 0)
        self.leftLayout.addWidget(self.detailGroup)

        # self.playerGroup = QGroupBox(self)

        # self.widgetLayout.addWidget(self.playerGroup, 1, 1)
        # self.matchGroupLayout.addWidget(self.playerGroup)

        # self.playerGroup.setStyleSheet(
        #     "QGroupBox { font-size: 18px; font-weight: bold; }"
        # )
        self.playersLayout = QVBoxLayout()
        self.matchGroupLayout.addLayout(self.playersLayout)
        # self.playersLayout.addStretch()
        self.playerGroupBox = {}
        for i, player in enumerate(self.players):
            pw = GamePlayerWidget(player, PlayerColours[i], self.matchGroup)
            pw.updateDisplay(self.engine.getScoreFromPlayer(player))
            if player == self.engine.getDealer():
                pw.setDealer()
            self.matchGroupLayout.addWidget(pw)
            self.playerGroupBox[player] = pw

        # self.playersLayout.addStretch()

        self.retranslateUI()

    def retranslateUI(self):
        super(SkullKingWidget, self).retranslateUI()
        # self.playerGroup.setTitle(i18n("GameWidget", "Scoreboard"))
        # self.scoringModeLabel.setText(self.tr("Scoring"))
        for i, m in enumerate(cast("SkullKingEngine", self.engine).listScoringModes()):
            self.scoringModeCombo.setItemText(i, self.tr(m))

        # self.roundModeLabel.setText(self.tr("Card Counts"))
        for i, m in enumerate(cast("SkullKingEngine", self.engine).listRoundModes()):
            self.roundModeCombo.setItemText(i, self.tr(m))

        self.detailGroup.retranslateUI()

    def setRoundTitle(self):
        super(SkullKingWidget, self).setRoundTitle()
        hands = self.engine.getHands()
        if hands == 1:
            self.roundTitleLabel.setText(
                "{} - {} {}".format(
                    self.engine.getGame(), str(hands), i18n("PochaWidget", "hand")
                )
            )
        else:
            self.roundTitleLabel.setText(
                "{} - {} {}".format(
                    self.engine.getGame(), str(hands), i18n("PochaWidget", "hands")
                )
            )

    def enableConfigCombos(self, enable=True):
        for combo in (self.scoringModeCombo, self.roundModeCombo):
            combo.view().setEnabled(enable)

    def checkPlayerScore(self, player, score):
        return True

    def unsetDealer(self):
        self.playerGroupBox[self.engine.getDealer()].unsetDealer()

    def setDealer(self):
        self.playerGroupBox[self.engine.getDealer()].setDealer()

    def updatePanel(self):
        self.progressBar.setCurrentStep(self.engine.getNumRound() - 1)
        self.enableConfigCombos(self.engine.getNumRound() == 1)
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
                self,
                self.game,
                i18n("PochaWidget", "There are players with no selected won hands."),
            )
            return
        if hands == won + 1 and self.engine.getScoringMode() != "classic_scoring":
            # Kraken case
            kraken_msg = QCoreApplication.translate(
                "SkullKingWidget", "Has the Kraken appeared?"
            )
            msg = (
                i18n(
                    "PochaWidget",
                    "There are {} won hands selected when there should be {}.",
                ).format(won, hands)
                + " "
                + kraken_msg
            )
            ret = QMessageBox.question(
                self,
                self.game,
                msg,
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No,
            )
            if ret == QMessageBox.StandardButton.No:
                return
        elif hands != won:
            msg = i18n(
                "PochaWidget",
                "There are {} won hands selected when there should be {}.",
            )
            QMessageBox.warning(self, self.game, msg.format(won, hands))
            return
        # Validate bonuses
        if self.engine.getScoringMode() != "classic_scoring":
            fourteens = 0
            loots = 0
            for piw in self.gameInput.playerInputList.values():
                bbtns = piw.getBonusButtons()
                for bn, btn in bbtns.items():
                    if bn == "fourteen":
                        fourteens += int(btn.getValue())
                    if bn == "loot":
                        loots += int(btn.getValue())
            if fourteens > 3:
                msg = QCoreApplication.translate(
                    "SkullKingWidget",
                    "There are more than 3 Fourteen bonuses selected.",
                )
                QMessageBox.warning(self, self.game, msg)
                return
            if loots > 4:
                msg = self.tr("There are more than 4 Loot bonuses selected.")
                QMessageBox.warning(self, self.game, msg)
                return

        super(SkullKingWidget, self).commitRound()

    def setFocus(self, reason=None):
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

    def changeRoundMode(self, _index):
        rmode = list(cast("SkullKingEngine", self.engine).listRoundModes())[
            self.roundModeCombo.currentIndex()
        ]
        try:
            cast("SkullKingEngine", self.engine).setRoundMode(rmode)
        except ValueError as ve:
            QMessageBox.critical(self, self.game, str(ve))
            return
        self.setRoundTitle()
        self.progressBar.setSteps(self.engine.getRoundSequence())
        self.progressBar.setCurrentStep(self.engine.getNumRound() - 1)
        self.detailGroup.updatePlot()
        self.gameInput.changeRoundMode()

    def changeScoringMode(self, _index):
        smode = list(cast("SkullKingEngine", self.engine).listScoringModes())[
            self.scoringModeCombo.currentIndex()
        ]
        try:
            cast("SkullKingEngine", self.engine).setScoringMode(smode)
        except ValueError as ve:
            QMessageBox.critical(self, self.game, str(ve))
            return
        self.gameInput.changeScoringMode()
        # self.updatePlayerOrder()


class SkullKingInputWidget(GameInputWidget):
    def __init__(self, engine, parent=None):
        super(SkullKingInputWidget, self).__init__(engine, parent)
        self.lastChoices = []
        self.initUI()

    def initUI(self):
        self.widgetLayout = QGridLayout(self)
        players = self.engine.getListPlayers()
        players_per_column = 4
        if len(players) in (5, 6):
            players_per_column = 3

        for i, player in enumerate(players):
            self.playerInputList[player] = SkullKingPlayerInputWidget(
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
            self.playerInputList[player].handsClicked.connect(self.newChoice)
            self.playerInputList[player].betTricksChanged.connect(
                self.updateCandidateAction
            )
            for bonus_button in self.playerInputList[player].getBonusButtons().values():
                bonus_button.bonusChanged.connect(self.bonusChangedAction)

        print(f"trying to set focus to {self.engine.getListPlayers()[0]}")
        self.playerInputList[self.engine.getListPlayers()[0]].setFocus()
        self.updateCandidateAction()

    def newChoice(self, mode, player):
        self.lastChoices.append((mode, player))

    def updateCandidateAction(self):
        if self.engine.getWinner():
            for piw in self.playerInputList.values():
                piw.lockBets()
                piw.lockTricks()
            return
        players = self.engine.getListPlayers()
        expected_hands = self.getExpectedHands()
        won_hands = self.getWonHands()
        dealer = self.engine.getDealer()
        first_player = (players.index(dealer) + 1) % len(players)
        hand_player_order = players[first_player:] + players[0:first_player]
        found = False
        if any([value < 0 for value in expected_hands.values()]):
            for player in hand_player_order:
                if not found and expected_hands[player] < 0:
                    self.playerInputList[player].setCandidate(True)
                    found = True
                else:
                    self.playerInputList[player].setCandidate(False)
        else:
            for player in hand_player_order:
                if not found and won_hands[player] < 0:
                    self.playerInputList[player].setCandidate(True)
                    found = True
                else:
                    self.playerInputList[player].setCandidate(False)

        expected_set_count = sum(1 for value in expected_hands.values() if value >= 0)
        won_set_count = sum(1 for value in won_hands.values() if value >= 0)
        if expected_set_count == len(players) and won_set_count > 0:
            for piw in self.playerInputList.values():
                piw.lockBets()
                piw.unlockTricks()
        elif expected_set_count == len(players) and won_set_count == 0:
            for piw in self.playerInputList.values():
                piw.unlockBets()
                piw.unlockTricks()
        else:
            for piw in self.playerInputList.values():
                piw.unlockBets()
                piw.lockTricks()

    def reset(self):
        super(SkullKingInputWidget, self).reset()
        self.lastChoices = []
        self.playerInputList[self.engine.getListPlayers()[0]].setFocus()
        self.updateCandidateAction()

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
        for piw in self.playerInputList.values():
            piw.disableWonRow(piw.getExpectedHands() < 0)
            # print(f"CheckExpected {player}: {piw.getExpectedHands()} {piw.getWonHands()}")
            # piw.disableExtraRow(piw.getExpectedHands() != piw.getWonHands() or piw.getExpectedHands() < 1)

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
            QtCore.Qt.Key.Key_9,
        ]

        if event.key() in (QtCore.Qt.Key.Key_Backspace, QtCore.Qt.Key.Key_Delete):
            try:
                mode, player = self.lastChoices.pop()
                if mode == "expected":
                    self.playerInputList[player].setExpectedHands(-1)
                else:
                    pil = self.playerInputList[player]
                    pil.setWonHands(-1)
                    pil.disableExtraRow(
                        pil.getExpectedHands() != pil.getWonHands()
                        or pil.getExpectedHands() < 1
                    )
                event.accept()
                return super(SkullKingInputWidget, self).keyPressEvent(event)
            except IndexError:
                pass

        try:
            number = numberkeys.index(event.key())
        except ValueError:
            return super(SkullKingInputWidget, self).keyPressEvent(event)

        if number in range(0, 10):
            self.feedNumber(number)

        return super(SkullKingInputWidget, self).keyPressEvent(event)

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
                    pil = self.playerInputList[player]
                    pil.disableExtraRow(
                        pil.getExpectedHands() != pil.getWonHands()
                        or pil.getExpectedHands() < 1
                    )
                return

        return

    def updatePlayerOrder(self):
        #         QWidget().setLayout(self.layout())
        trash = QWidget()
        trash_layout = self.layout()
        if trash_layout:
            trash.setLayout(trash_layout)
        self.widgetLayout = QGridLayout(self)
        ppr = 4
        nplayers = len(self.engine.getListPlayers())
        if nplayers in (5, 6):
            ppr = 3
        for i, player in enumerate(self.engine.getListPlayers()):
            if trash_layout:
                trash_layout.removeWidget(self.playerInputList[player])
            self.widgetLayout.addWidget(self.playerInputList[player], i // ppr, i % ppr)
            self.playerInputList[player].setColour(PlayerColours[i])

    def bonusChangedAction(self, sender_type, sender):
        for player in self.engine.getListPlayers():
            for bn, btn in self.playerInputList[player].getBonusButtons().items():
                trifecta = ("skullking", "pirate", "mermaid")
                if sender_type in trifecta:
                    if (
                        bn == sender_type
                        and btn is not sender
                        or bn != sender_type
                        and bn in trifecta
                    ):
                        btn.setChecked(False)
                if sender_type in ("blackfourteen", "roatan"):
                    if bn == sender_type and btn is not sender:
                        btn.setChecked(False)

    def changeRoundMode(self):
        for piw in self.playerInputList.values():
            piw.refreshButtons()

    def changeScoringMode(self):
        for piw in self.playerInputList.values():
            piw.updateBonusButtons()


class SkullKingPlayerInputWidget(QGroupBox):
    winnerSet = QtCore.Signal(str)
    newExpected = QtCore.Signal()
    handsClicked = QtCore.Signal(str, str)
    betTricksChanged = QtCore.Signal()

    def __init__(self, player, engine, colour=QColor(0, 0, 0), parent=None):
        super(SkullKingPlayerInputWidget, self).__init__(parent)
        self.player = player
        self.engine = engine
        self.winner = False
        self.candidate = False
        self.mainLayout = QVBoxLayout(self)
        self.mainLayout.setSpacing(0)

        self.setTitle(self.player)
        self.pcolour = colour

        self.upperLayout = QHBoxLayout()
        self.upperLayout.addStretch(1)
        self.mainLayout.addLayout(self.upperLayout)
        self.btWidget = BetTrickWidget(self.pcolour, 40, self)
        self.btWidget.changed.connect(self.betTricksChanged)
        self.upperLayout.addWidget(self.btWidget)
        self.rightUpperLayout = QHBoxLayout()
        self.rightUpperLayout.setContentsMargins(0, 0, 0, 0)

        self.upperLayout.addLayout(self.rightUpperLayout)
        self.upperLayout.addStretch(1)

        self.lowerLayout = QHBoxLayout()
        self.mainLayout.addLayout(self.lowerLayout)
        self.extraPointsGroup = QFrame(self)
        self.extraPointsGroup.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred
        )
        self.lowerLayout.addWidget(self.extraPointsGroup)
        self.epLayout = QHBoxLayout(self.extraPointsGroup)
        self.epLayout.setSpacing(0)
        self.epLayout.setContentsMargins(2, 2, 2, 2)
        self.extraFeaturesGroup = QFrame(self)
        self.extraFeaturesGroup.setSizePolicy(
            QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Preferred
        )
        self.bonusButtons = {}
        self.setColour(colour)
        self.updateBonusButtons()
        self.reset()

    def isCandidate(self):
        return self.candidate

    def setCandidate(self, value=True):
        self.btWidget.setCandidate(value)
        self.candidate = value

    def updateBonusButtons(self):
        trash = QWidget()
        trash_layout = self.epLayout
        if trash_layout:
            trash.setLayout(trash_layout)

        self.epLayout = QHBoxLayout(self.extraPointsGroup)
        if len(list(self.engine.listBonusTypes())) > 4:
            self.epLayout.setSpacing(5)
        else:
            self.epLayout.setSpacing(20)
        self.epLayout.setContentsMargins(2, 2, 2, 2)
        self.epLayout.addStretch()

        for btn in self.bonusButtons.values():
            trash_layout.removeWidget(btn)
            btn.deleteLater()

        self.bonusButtons = {}

        for btype in self.engine.listBonusTypes():
            parent = self.extraPointsGroup
            layout = self.epLayout
            position = 0
            size = 30
            alignment = Qt.AlignmentFlag.AlignCenter
            reps = min(
                len(self.engine.getPlayers()) - 1, self.engine.getBonusReps(btype)
            )
            if btype == "cannonball":
                parent = self
                layout = self.rightUpperLayout
                position = 0
                size = 40
                # alignment = Qt.AlignmentFlag.AlignLeft
            if btype == "fourteen":
                reps = min(
                    len(self.engine.getPlayers()), self.engine.getBonusReps(btype)
                )
            self.bonusButtons[btype] = SkullKingBonusButton(
                btype,
                reps,
                self.pcolour,
                size,
                parent,
            )
            layout.addWidget(self.bonusButtons[btype], position)
            layout.setAlignment(self.bonusButtons[btype], alignment)

        self.epLayout.addStretch()

    def reset(self):
        self.btWidget.reset()
        self.refreshButtons()
        for button in self.bonusButtons.values():
            button.setChecked(False)
        self.disableExtraRow()

    def refreshButtons(self, _forbidden=-1):
        hands = self.engine.getHands()
        self.btWidget.setMaxBet(hands)

    def disableExtraRow(self, disable=True):
        self.extraPointsGroup.setDisabled(disable)

    def enableWonGroup(self, _button):
        self.newExpected.emit()

    def isWinner(self):
        return False

    def getPlayer(self):
        return self.player

    def getScore(self):
        expected = self.getExpectedHands()
        won = self.getWonHands()
        bonuses = {bt: int(v.getValue()) for bt, v in self.bonusButtons.items()}
        return self.engine.computePlayerScore(expected, won, bonuses)

    def getWonHands(self):
        return self.btWidget.getTricks()

    def getExpectedHands(self):
        return self.btWidget.getBet()

    def setExpectedHands(self, number):
        self.btWidget.setBet(number)
        return True

    def setWonHands(self, number):
        self.btWidget.setTricks(number)
        return True

    def expectedClickedAction(self, _):
        self.handsClicked.emit("expected", self.player)

    def wonClickedAction(self, _):
        self.disableExtraRow(
            self.getExpectedHands() != self.getWonHands() or self.getExpectedHands() < 1
        )
        self.handsClicked.emit("won", self.player)

    def setColour(self, colour):
        self.pcolour = colour
        css = """
            QGroupBox {{ font-size: 24px; font-weight: bold; color:rgb({},{},{});}}
            QGroupBox:focus-within {{ border: 2px solid #0078d7; background-color: #e6f1fb;}}
            QGroupBox::title {{
                    subcontrol-origin: margin;
                    subcontrol-position: top center;
                    padding: 0 10px;
                    background-color: transparent;
            }}
        """
        self.setStyleSheet(
            css.format(self.pcolour.red(), self.pcolour.green(), self.pcolour.blue())
        )
        self.btWidget.setColour(self.pcolour)

    def getBonusButtons(self):
        return self.bonusButtons

    def lockBets(self):
        self.btWidget.lockBets()

    def unlockBets(self):
        self.btWidget.unlockBets()

    def lockTricks(self):
        self.btWidget.lockTricks()

    def unlockTricks(self):
        self.btWidget.unlockTricks()


class ClickableLabel(QLabel):
    clicked = QtCore.Signal(Qt.MouseButton)

    def __init__(self, text="", pcolour=QColor(255, 255, 255), size=40, parent=None):
        super().__init__(text, parent)
        self.pcolour = pcolour
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.diameter = size
        self.locked = False
        self.candidate = False
        self.setFixedSize(self.diameter, self.diameter)
        # Color animation effect (disabled unless candidate=True)
        self.effect = QGraphicsColorizeEffect(self)
        # self.effect.setColor(QColor("#4c8bf5"))  # glow color
        self.effect.setColor(self.pcolour)  # glow color
        self.effect.setStrength(0.0)
        self.setGraphicsEffect(self.effect)

        # Animation: pulse between strength=0 -> 0.6 -> 0
        self.anim = QPropertyAnimation(self.effect, b"strength")
        self.anim.setDuration(1800)
        self.anim.setStartValue(0.0)
        self.anim.setKeyValueAt(0.5, 0.2)
        self.anim.setEndValue(0.0)
        self.anim.setLoopCount(-1)  # infinite
        self.setStyleSheet(self.normalStyle())

    def isCandidate(self):
        return self.candidate

    def setCandidate(self, value):
        if self.candidate == value:
            return
        self.candidate = value
        if value:
            self.startCandidateAnimation()
        else:
            self.stopCandidateAnimation()

    candidateProperty = Property(bool, isCandidate, setCandidate)

    def startCandidateAnimation(self):
        self.anim.start()

    def stopCandidateAnimation(self):
        self.anim.stop()
        self.effect.setStrength(0.0)

    def normalStyle(self):
        if self.locked:
            return self.lockStyle()
        hovercolour = "#555555"
        return f"""
            QLabel {{
                background-color: #444444;
                border: 1px solid #666666;
                border-radius: {self.diameter // 2}px;
                font-size: 24px;
                font-weight: bold;
                color: rgb({self.pcolour.red()},{self.pcolour.green()},{self.pcolour.blue()});
            }}
            QLabel:hover {{
                background-color: {hovercolour};
            }}
        """

    def lockStyle(self):
        return f"""
            QLabel {{
                background-color: #444444;
                border: 1px solid;
                border-color: rgb({self.pcolour.red()},{self.pcolour.green()},{self.pcolour.blue()});
                border-radius: {self.diameter // 2}px;
                font-size: 24px;
                font-weight: bold;
                color: rgb({self.pcolour.red()},{self.pcolour.green()},{self.pcolour.blue()});
            }}
            QLabel:hover {{
                background-color: #444444;
            }}
        """

    def pressedStyle(self):
        return f"""
            QLabel {{
                background-color: #333333;
                border: 1px solid #777777;
                border-radius: {self.diameter // 2}px;
                font-size: 24px;
                font-weight: bold;
                color: rgb({self.pcolour.red()},{self.pcolour.green()},{self.pcolour.blue()});
            }}
        """

    def mousePressEvent(self, event):
        self.highlightChange()
        self.clicked.emit(event.button())

    def resetStyle(self):
        self.setStyleSheet(self.normalStyle())

    def highlightChange(self):
        self.setStyleSheet(self.pressedStyle())
        QTimer.singleShot(180, self.resetStyle)

    def lock(self):
        self.locked = True
        self.setStyleSheet(self.lockStyle())

    def unlock(self):
        self.locked = False
        self.setStyleSheet(self.normalStyle())

    def isLocked(self):
        return self.locked

    def setColour(self, colour):
        self.pcolour = colour
        self.effect.setColor(self.pcolour)  # glow color
        self.resetStyle()


class BetTrickWidget(QWidget):
    changed = QtCore.Signal()

    def __init__(self, pcolour=QColor(255, 255, 255), size=40, parent=None):
        super().__init__(parent)
        self.bet = -1
        self.tricks = -1
        self.maxBet = 1
        self.pcolour = pcolour

        self.mainLayout = QHBoxLayout()
        self.setLayout(self.mainLayout)
        self.mainLayout.setSpacing(20)

        self.betLabel = ClickableLabel("-", self.pcolour, size, self)
        self.tricksLabel = ClickableLabel("-", self.pcolour, size, self)

        self.betLabel.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.tricksLabel.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)

        self.mainLayout.addWidget(self.betLabel)
        self.mainLayout.addWidget(self.tricksLabel)

        self.betLabel.mousePressEvent = self.cycleBet
        self.tricksLabel.mousePressEvent = self.cycleTricks

    def isCandidate(self):
        return self.betLabel.isCandidate() or self.tricksLabel.isCandidate()

    def setCandidate(self, value):
        if not value:
            self.betLabel.setCandidate(False)
            self.tricksLabel.setCandidate(False)
        elif self.bet < 0:
            self.tricksLabel.setCandidate(False)
            self.betLabel.setCandidate(True)
        elif self.tricks < 0:
            self.betLabel.setCandidate(False)
            self.tricksLabel.setCandidate(True)

    def setMaxBet(self, bet):
        self.maxBet = bet

    def setBet(self, bet):
        if self.betLabel.isLocked():
            return
        if bet > self.maxBet:
            bet = self.maxBet
        self.bet = bet
        if self.bet < 0:
            self.betLabel.setText("-")
            # self.tricksLabel.lock()
        else:
            self.betLabel.setText(str(self.bet))
            # self.tricksLabel.unlock()
        self.betLabel.highlightChange()
        self.changed.emit()

    def resetBet(self):
        self.betLabel.unlock()
        self.setBet(-1)

    def resetTricks(self):
        self.tricksLabel.unlock()
        self.setTricks(-1)
        self.tricksLabel.lock()

    def reset(self):
        self.resetTricks()
        self.resetBet()

    def getBet(self):
        return self.bet

    def getTricks(self):
        return self.tricks

    def setTricks(self, tricks):
        if self.tricksLabel.isLocked():
            return
        if tricks > self.maxBet:
            tricks = self.maxBet
        self.tricks = tricks
        if self.tricks < 0:
            self.tricksLabel.setText("-")
        else:
            self.tricksLabel.setText(str(self.tricks))
        self.tricksLabel.highlightChange()
        self.changed.emit()

    def cycleBet(self, event):
        newbet = self.bet
        if event.button() == Qt.MouseButton.LeftButton:
            newbet = (self.bet + 2) % (self.maxBet + 2) - 1
        elif event.button() == Qt.MouseButton.RightButton:
            newbet = self.bet % (self.maxBet + 2) - 1
        self.setBet(newbet)

    def cycleTricks(self, event):
        newtricks = self.tricks
        if event.button() == Qt.MouseButton.LeftButton:
            newtricks = (self.tricks + 2) % (self.maxBet + 2) - 1
        if event.button() == Qt.MouseButton.RightButton:
            newtricks = self.tricks % (self.maxBet + 2) - 1
        self.setTricks(newtricks)

    def lockBets(self):
        self.betLabel.lock()

    def unlockBets(self):
        self.betLabel.unlock()

    def lockTricks(self):
        self.tricksLabel.lock()

    def unlockTricks(self):
        self.tricksLabel.unlock()

    def setColour(self, colour):
        self.pcolour = colour
        self.betLabel.setColour(colour)
        self.tricksLabel.setColour(colour)


class SkullKingBonusButton(QPushButton):
    bonusChanged = QtCore.Signal(str, object)

    def __init__(
        self, bonus_name: str, maximum: int = 1, colour=None, size=32, parent=None
    ):
        super().__init__(parent)

        self.bonus_name = bonus_name
        self.maximum = maximum
        self.count = 0
        self.button_size = size
        self.highlight_colour = colour if colour else QColor(200, 0, 0)

        original_image = QImage(f"icons/{bonus_name}.png")
        self.image = original_image.scaled(
            self.button_size,
            self.button_size,
            QtCore.Qt.AspectRatioMode.KeepAspectRatio,
            QtCore.Qt.TransformationMode.SmoothTransformation,
        )

        self.grey_image = self.image.convertToFormat(QImage.Format.Format_Grayscale8)

        self.setCheckable(True)
        self.setFlat(True)
        self.setStyleSheet("border: none;")

        self.setFixedSize(self.button_size, self.button_size)

        self._fade_alpha = 0.0

        self.fade_anim = QPropertyAnimation(self, b"fade_alpha")
        self.fade_anim.setDuration(400)
        self.fade_anim.setEasingCurve(QEasingCurve.Type.OutCubic)

        self.clicked.connect(self._on_pressed)

    def _on_pressed(self):
        old_value = self.count
        self.count = (self.count + 1) % (self.maximum + 1)
        self.setChecked(
            self.count > 0
        )  # trigger pulse animation only when transitioning 0 -> >0

        if old_value == 0 and self.count > 0:
            self.fade_anim.stop()
            self.fade_anim.setStartValue(0.0)
            self.fade_anim.setEndValue(1.0)
            self.fade_anim.start()
            self.bonusChanged.emit(self.bonus_name, self)

        elif old_value > 0 and self.count == 0:
            self.fade_anim.stop()
            self.fade_anim.setStartValue(1.0)
            self.fade_anim.setEndValue(0.0)
            self.fade_anim.start()
        self.update()

    def get_fade_alpha(self):
        return self._fade_alpha

    def set_fade_alpha(self, value):
        self._fade_alpha = float(value)
        self.update()

    fade_alpha = QtCore.Property(float, get_fade_alpha, set_fade_alpha)

    def getValue(self):
        return self.count

    def setChecked(self, checked):
        if not checked:
            self.count = 0
        super().setChecked(checked)

    def sizeHint(self):
        return QtCore.QSize(self.button_size, self.button_size)

    def setMaximum(self, maximum):
        self.maximum = maximum
        if self.count > self.maximum:
            self.count = self.maximum
            if self.count == 0:
                self.setChecked(False)
            self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # --- circular clipping ---
        path = QPainterPath()
        radius = min(self.width(), self.height()) / 2
        center = self.rect().center()
        path.addEllipse(center, radius, radius)
        painter.setClipPath(path)

        # --- choose image (normal or greyscale if disabled) ---
        if self.isEnabled():
            img_to_draw = self.image
        else:
            img_to_draw = self.grey_image
            self.setChecked(False)

        # --- draw icon ---
        painter.drawImage(self.rect(), img_to_draw)

        # --- active outline (red circular ring) ---
        if self.count > 0:
            alpha = int(255 * self._fade_alpha)
            ring_radius = radius - 2
            pen = painter.pen()
            colour = QColor(self.highlight_colour)
            colour.setAlpha(alpha)
            pen.setColor(colour)  # red
            pen.setWidth(4)
            painter.setPen(pen)
            painter.setBrush(QtCore.Qt.BrushStyle.NoBrush)
            painter.drawEllipse(center, ring_radius, ring_radius)

        # --- text overlay when count > 1 ---
        if self.count >= 1 and self.maximum > 1:
            # Semi-transparent dark circle behind the number
            overlay_color = QColor(0, 0, 0, 120)
            painter.setBrush(overlay_color)
            painter.setPen(QtCore.Qt.PenStyle.NoPen)

            circle_diameter = min(self.width(), self.height()) * 0.45
            circle_rect = QRectF(
                (self.width() - circle_diameter) / 2,
                (self.height() - circle_diameter) / 2,
                circle_diameter,
                circle_diameter,
            )
            painter.drawEllipse(circle_rect)

            # Draw the number
            painter.setPen(QColor(255, 255, 255, 220))
            painter.setPen(self.highlight_colour)
            font = QFont("Arial", int(circle_diameter * 0.9), QFont.Weight.Bold)
            painter.setFont(font)

            painter.drawText(
                self.rect(), QtCore.Qt.AlignmentFlag.AlignCenter, str(self.count)
            )

        painter.end()


class SkullKingRoundsDetail(GameRoundsDetail):
    def __init__(self, engine, parent=None):
        self.bgcolors = [0xCCFF99, 0xFFCC99]
        super(SkullKingRoundsDetail, self).__init__(engine, parent)
        self.container.setCurrentWidget(self.plot)

    def createRoundTable(self, engine, parent=None):
        return SkullKingRoundTable(self.engine, self.bgcolors, parent)

    def createRoundPlot(self, engine, parent=None):
        return SkullKingRoundPlot(self.engine, self)

    def createQSBox(self, parent=None):
        print("Creating SkullKingQSTW")
        return SkullKingQSTW(self.engine.getGame(), self.engine.getListPlayers(), self)


class SkullKingRoundTable(GameRoundTable):
    def __init__(self, engine, bgcolors, parent=None):
        self.bgcolors = bgcolors
        super(SkullKingRoundTable, self).__init__(engine, parent)

    def insertRound(self, rnd):
        winner = rnd.getWinner()
        i = rnd.getNumRound() - 1
        self.insertRow(i)
        hands = self.engine.getHands(rnd.getNumRound())
        hitem = QTableWidgetItem("{}".format(hands))
        self.setVerticalHeaderItem(i, hitem)

        for j, player in enumerate(self.engine.getListPlayers()):
            item = QTableWidgetItem()
            item.setFlags(item.flags() ^ QtCore.Qt.ItemFlag.ItemIsEditable)
            item.setTextAlignment(
                QtCore.Qt.AlignmentFlag.AlignVCenter
                | QtCore.Qt.AlignmentFlag.AlignCenter
            )
            score = rnd.getPlayerScore(player)
            if score > 0:
                background = self.bgcolors[0]
            else:
                background = self.bgcolors[1]
            item.setBackground(QtGui.QBrush(QtGui.QColor(background)))
            item.setForeground(QtGui.QBrush(QtGui.QColor(0, 0, 0)))
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
        roundNames = [""]
        for player in self.engine.getPlayers():
            scores[player] = [0]
        for i, roundName in enumerate(
            cast(SkullKingEngine, self.engine).getRoundSequence()
        ):
            roundNames.append("{}".format(roundName))
            for player in self.engine.getPlayers():
                try:
                    rnd = self.engine.getRounds()[i]
                    rndscore = rnd.getPlayerScore(player)
                    accumscore = scores[player][-1] + rndscore
                    scores[player].append(accumscore)
                except IndexError:
                    pass

        self.canvas.addHHeaders(roundNames)
        self.canvas.clearPlotContents()
        for player in self.engine.getListPlayers():
            self.canvas.addSeries(scores[player], player)

        self.canvas._scene.update()


class SkullKingQSTW(QuickStatsTW):
    def initStatsWidgets(self):
        self.gs = SkullKingQSBox(self.game, self)
        self.ps = SkullKingPQSBox(self.game, self)


class SkullKingQSBox(GeneralQuickStats):
    QCoreApplication.translate("GeneralQuickStats", "Max Hits")
    QCoreApplication.translate("GeneralQuickStats", "Avg Hits")
    QCoreApplication.translate("GeneralQuickStats", "Best Round")

    def __init__(self, gname, parent):
        super(SkullKingQSBox, self).__init__(gname, parent)
        self.playerStatsKeys.append("max_hits")
        self.playerStatsHeaders.append("Max Hits")
        self.playerStatsKeys.append("avg_hits")
        self.playerStatsHeaders.append("Avg Hits")
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


class SkullKingPQSBox(SkullKingQSBox, ParticularQuickStats):
    pass
