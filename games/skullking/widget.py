"""Skull King board widgets: score entry, bonus buttons, tables and plots."""

from __future__ import annotations

import logging
from typing import cast

from PySide6 import QtCore, QtGui
from PySide6.QtCore import (
    Property,
    QCoreApplication,
    QPropertyAnimation,
    Qt,
    QTimer,
)
from PySide6.QtGui import QColor, QKeyEvent, QMouseEvent
from PySide6.QtWidgets import (
    QComboBox,
    QFrame,
    QGraphicsColorizeEffect,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QSizePolicy,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from core.model.base import GenericRound
from core.ui.game import (
    BonusButton,
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
from games.skullking.engine import SkullKingEngine

logger = logging.getLogger(__name__)

i18n = QCoreApplication.translate


class SkullKingWidget(GameWidget):
    """Top-level Skull King game widget with scoring and round mode combos."""

    QCoreApplication.translate("SkullKingWidget", "classic_scoring")
    QCoreApplication.translate("SkullKingWidget", "standard_scoring")
    QCoreApplication.translate("SkullKingWidget", "rascal_scoring")
    QCoreApplication.translate("SkullKingWidget", "standard_rounds")
    QCoreApplication.translate("SkullKingWidget", "even")
    QCoreApplication.translate("SkullKingWidget", "brawl")
    QCoreApplication.translate("SkullKingWidget", "skirmish")
    QCoreApplication.translate("SkullKingWidget", "barrage")
    QCoreApplication.translate("SkullKingWidget", "whirlpool")

    def createEngine(self) -> None:
        if self.game != "Skull King":
            raise GameNotImplementedException(f"No engine for game {self.game}")
        self.engine = SkullKingEngine()

    def initUI(self) -> None:
        super().initUI()
        self.retranslateUI()

    def retranslateUI(self) -> None:
        """Re-translate the scoring and round mode combo item labels."""
        super().retranslateUI()
        # self.playerGroup.setTitle(i18n("GameWidget", "Scoreboard"))
        # self.scoringModeLabel.setText(self.tr("Scoring"))
        for i, m in enumerate(cast("SkullKingEngine", self.engine).listScoringModes()):
            self.scoringModeCombo.setItemText(i, self.tr(m))

        # self.roundModeLabel.setText(self.tr("Card Counts"))
        for i, m in enumerate(cast("SkullKingEngine", self.engine).listRoundModes()):
            self.roundModeCombo.setItemText(i, self.tr(m))

    def createGameInputWidget(self, parent: QWidget | None = None):  # pyright: ignore[reportIncompatibleMethodOverride]
        return SkullKingInputWidget(self.engine, parent)

    def createRoundsDetail(self, parent: QWidget | None = None):
        return SkullKingRoundsDetail(self.engine, parent)

    def addExtraConfig(self) -> None:
        """Add the progress bar and the scoring and round mode selectors."""
        super().addExtraConfig()
        self.progressBar = StepProgressBar(
            # StepProgressBar accepts int steps (it stringifies them internally).
            cast("SkullKingEngine", self.engine).getRoundSequence(),  # pyright: ignore[reportArgumentType]
            self,
        )
        self.matchGroupLayout.addWidget(self.progressBar)

        self.configLayout = QVBoxLayout()
        self.matchGroupLayout.addLayout(self.configLayout)
        self.dealerPolicyCheckBox.hide()

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

    def setRoundTitle(self) -> None:
        """Set the round title showing the current hand count."""
        super().setRoundTitle()
        hands = cast("SkullKingEngine", self.engine).getHands()
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

    def enableConfigCombos(self, enable: bool = True) -> None:
        for combo in (self.scoringModeCombo, self.roundModeCombo):
            combo.view().setEnabled(enable)

    def checkPlayerScore(
        self, player: str, score: int, extras: dict | None = None
    ) -> bool:
        return True

    def updatePanel(self) -> None:
        super().updatePanel()
        self.progressBar.setCurrentStep(self.engine.getNumRound() - 1)
        self.enableConfigCombos(self.engine.getNumRound() == 1)

    def commitRoundSanityCheck(self, interactive: bool = False) -> bool:
        """Validate the won hand counts and bonuses before committing a round."""
        hands = cast("SkullKingEngine", self.engine).getHands()
        wonhands = cast(SkullKingInputWidget, self.gameInput).getWonHands()
        won = sum(wonhands.values())
        if min(wonhands.values()) < 0:
            msg = i18n("PochaWidget", "There are players with no selected won hands.")
            if interactive:
                QMessageBox.warning(self, self.game, msg)
            else:
                logger.debug(msg)
            return False
        if (
            hands == won + 2
            and cast("SkullKingEngine", self.engine).getScoringMode()
            != "classic_scoring"
        ):
            if interactive:
                # Kraken + White whale corner case
                kraken_msg = QCoreApplication.translate(
                    "SkullKingWidget",
                    "Has the Kraken and White Whale appeared and discarded two tricks?",
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
                    return False
        elif (
            hands == won + 1
            and cast("SkullKingEngine", self.engine).getScoringMode()
            != "classic_scoring"
        ):
            if interactive:
                # Kraken case
                kraken_msg = QCoreApplication.translate(
                    "SkullKingWidget", "Has the Kraken appeared and discarded a trick?"
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
                    return False
        elif hands != won:
            msg = i18n(
                "PochaWidget",
                "There are {} won hands selected when there should be {}.",
            ).format(won, hands)
            if interactive:
                QMessageBox.warning(self, self.game, msg)
            else:
                logger.debug(msg)
            return False
        # Validate bonuses
        if cast("SkullKingEngine", self.engine).getScoringMode() != "classic_scoring":
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
                if interactive:
                    QMessageBox.warning(self, self.game, msg)
                else:
                    logger.debug(msg)
                return False
            if loots > 4:
                msg = self.tr("There are more than 4 Loot bonuses selected.")
                if interactive:
                    QMessageBox.warning(self, self.game, msg)
                else:
                    logger.debug(msg)
                return False
        return True

    def changeRoundMode(self, _index) -> None:
        """Apply the selected round mode and refresh dependent widgets."""
        rmode = list(cast("SkullKingEngine", self.engine).listRoundModes())[
            self.roundModeCombo.currentIndex()
        ]
        try:
            cast("SkullKingEngine", self.engine).setRoundMode(rmode)
        except ValueError as ve:
            QMessageBox.critical(self, self.game, str(ve))
            return
        self.setRoundTitle()
        self.progressBar.setSteps(
            # StepProgressBar accepts int steps (it stringifies them internally).
            cast("SkullKingEngine", self.engine).getRoundSequence()  # pyright: ignore[reportArgumentType]
        )
        self.progressBar.setCurrentStep(self.engine.getNumRound() - 1)
        self.detailGroup.updatePlot()
        cast(SkullKingInputWidget, self.gameInput).changeRoundMode()

    def changeScoringMode(self, _index) -> None:
        """Apply the selected scoring mode and refresh the input widget."""
        smode = list(cast("SkullKingEngine", self.engine).listScoringModes())[
            self.scoringModeCombo.currentIndex()
        ]
        try:
            cast("SkullKingEngine", self.engine).setScoringMode(smode)
        except ValueError as ve:
            QMessageBox.critical(self, self.game, str(ve))
            return
        cast(SkullKingInputWidget, self.gameInput).changeScoringMode()
        # self.updatePlayerOrder()


class SkullKingInputWidget(GameInputWidget):
    """Grid of per-player Skull King input widgets with keyboard entry."""

    def __init__(self, engine, parent=None) -> None:
        self.lastChoices: list[tuple[str, str]] = []
        super().__init__(engine, parent)

    def initUI(self) -> None:
        """Lay out one input widget per player and wire their signals."""
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
            self.playerInputList[player].betTricksChanged.connect(
                self.updateCandidateAction
            )
            self.playerInputList[player].betTricksChanged.connect(self.changed)
            for bonus_button in self.playerInputList[player].getBonusButtons().values():
                bonus_button.bonusChanged.connect(self.bonusChangedAction)
                bonus_button.bonusChanged.connect(self.changed)

        logger.debug("Trying to set focus to %s", self.engine.getListPlayers()[0])
        self.playerInputList[self.engine.getListPlayers()[0]].setFocus()
        self.updateCandidateAction()

    def newChoice(self, mode: str, player: str) -> None:
        self.lastChoices.append((mode, player))

    def updateCandidateAction(self) -> None:
        """Highlight the next player to enter and lock/unlock bet and trick rows."""
        if self.engine.getWinner():
            for piw in self.playerInputList.values():
                piw.lockBets()
                piw.lockTricks()
            return
        players = self.engine.getListPlayers()
        expected_hands = self.getExpectedHands()
        won_hands = self.getWonHands()
        dealer = self.engine.getDealer()
        first_player = (players.index(cast("str", dealer)) + 1) % len(players)
        hand_player_order = players[first_player:] + players[0:first_player]
        found = False
        if any(value < 0 for value in expected_hands.values()):
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

    def reset(self) -> None:
        super().reset()
        self.lastChoices = []
        self.playerInputList[self.engine.getListPlayers()[0]].setFocus()
        self.updateCandidateAction()

    def getScores(self) -> dict[str, int]:
        scores = {}
        for player, piw in self.playerInputList.items():
            scores[player] = piw.getScore()
        return scores

    def getWonHands(self) -> dict[str, int]:
        won = {}
        for player, piw in self.playerInputList.items():
            won[player] = piw.getWonHands()
        return won

    def getExpectedHands(self) -> dict[str, int]:
        expected = {}
        for player, piw in self.playerInputList.items():
            expected[player] = piw.getExpectedHands()
        return expected

    def checkExpected(self) -> None:
        """Disable the won row of any player without an expected bet set."""
        for piw in self.playerInputList.values():
            piw.disableWonRow(piw.getExpectedHands() < 0)
            # print(f"CheckExpected {player}: {piw.getExpectedHands()} {piw.getWonHands()}")
            # piw.disableExtraRow(piw.getExpectedHands() != piw.getWonHands() or piw.getExpectedHands() < 1)

    def keyPressEvent(self, event: QKeyEvent) -> None:
        """Handle number keys for entry and backspace/delete to undo choices."""
        numberkeys: list[int] = [
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
                return super().keyPressEvent(event)
            except IndexError:
                pass

        try:
            number = numberkeys.index(event.key())
        except ValueError:
            return super().keyPressEvent(event)

        if number in range(10):
            self.feedNumber(number)

        return super().keyPressEvent(event)

    def feedNumber(self, number: int) -> None:
        """Assign ``number`` to the next player awaiting an expected or won value."""
        players = self.engine.getListPlayers()
        expected_hands = self.getExpectedHands()
        won_hands = self.getWonHands()
        dealer = self.engine.getDealer()
        first_player = (players.index(cast("str", dealer)) + 1) % len(players)
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
                    pil = self.playerInputList[player]
                    pil.disableExtraRow(
                        pil.getExpectedHands() != pil.getWonHands()
                        or pil.getExpectedHands() < 1
                    )
                return

        return

    def updatePlayerOrder(self) -> None:
        """Rebuild the player grid in the engine's current player order."""
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
        self.updateCandidateAction()

    def bonusChangedAction(self, sender_type, sender) -> None:
        """Enforce mutual exclusion between related bonus buttons across players."""
        for player in self.engine.getListPlayers():
            for bn, btn in self.playerInputList[player].getBonusButtons().items():
                trifecta = ("skullking", "pirate", "mermaid")
                if sender_type in trifecta and (
                    bn == sender_type
                    and btn is not sender
                    or bn != sender_type
                    and bn in trifecta
                ):
                    btn.setChecked(False)
                if (
                    sender_type in ("blackfourteen", "roatan")
                    and bn == sender_type
                    and btn is not sender
                ):
                    btn.setChecked(False)

    def changeRoundMode(self) -> None:
        for piw in self.playerInputList.values():
            piw.refreshButtons()

    def changeScoringMode(self) -> None:
        for piw in self.playerInputList.values():
            piw.updateBonusButtons()


class SkullKingPlayerInputWidget(QGroupBox):
    """Per-player bet, trick and bonus input for a single Skull King player."""

    winnerSet = QtCore.Signal(str)
    newExpected = QtCore.Signal()
    handsClicked = QtCore.Signal(str, str)
    betTricksChanged = QtCore.Signal()

    def __init__(
        self, player, engine, colour: QColor | None = None, parent=None
    ) -> None:
        super().__init__(parent)
        self.player = player
        self.engine = engine
        self.winner = False
        self.candidate = False
        self.mainLayout = QVBoxLayout(self)
        self.mainLayout.setSpacing(0)

        self.setTitle(self.player)
        self.pcolour = colour if colour else QColor(0, 0, 0)

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
        self.bonusButtons: dict[str, SkullKingBonusButton] = {}
        self.setColour(colour)
        self.updateBonusButtons()
        self.reset()

    def isCandidate(self) -> bool:
        return self.candidate

    def setCandidate(self, value: bool = True) -> None:
        self.btWidget.setCandidate(value)
        self.candidate = value

    def updateBonusButtons(self) -> None:
        """Rebuild the bonus buttons for the engine's active scoring mode."""
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

        self.disableExtraRow(
            self.getExpectedHands() != self.getWonHands() or self.getExpectedHands() < 1
        )
        self.epLayout.addStretch()

    def reset(self) -> None:
        self.btWidget.reset()
        self.refreshButtons()
        for button in self.bonusButtons.values():
            button.setChecked(False)
        self.disableExtraRow()

    def refreshButtons(self, _forbidden: int = -1) -> None:
        hands = self.engine.getHands()
        self.btWidget.setMaxBet(hands)

    def disableExtraRow(self, disable: bool = True) -> None:
        """Enable or disable each bonus button per current bet/trick state."""
        for btype, b in self.bonusButtons.items():
            if btype == "loot":
                b.setEnabled(
                    self.getExpectedHands() == self.getWonHands()
                    and self.getExpectedHands() >= 0
                )
            elif btype == "roatan":
                b.setEnabled(self.getExpectedHands() >= 0 and self.getWonHands() != 0)
            else:
                b.setDisabled(disable)

    def enableWonGroup(self, _button) -> None:
        self.newExpected.emit()

    def isWinner(self) -> bool:
        return False

    def getPlayer(self) -> str:
        return self.player

    def getScore(self) -> int:
        """Compute this player's round score from bets, tricks and bonuses."""
        expected = self.getExpectedHands()
        won = self.getWonHands()
        bonuses = {bt: int(v.getValue()) for bt, v in self.bonusButtons.items()}
        return self.engine.computePlayerScore(expected, won, bonuses)

    def getWonHands(self) -> int:
        return self.btWidget.getTricks()

    def getExpectedHands(self) -> int:
        return self.btWidget.getBet()

    def setExpectedHands(self, number: int) -> bool:
        self.btWidget.setBet(number)
        return True

    def setWonHands(self, number: int) -> bool:
        self.btWidget.setTricks(number)
        return True

    def expectedClickedAction(self, _) -> None:
        self.handsClicked.emit("expected", self.player)

    def wonClickedAction(self, _) -> None:
        self.disableExtraRow(
            self.getExpectedHands() != self.getWonHands() or self.getExpectedHands() < 1
        )
        self.handsClicked.emit("won", self.player)

    def setColour(self, colour) -> None:
        """Apply the player colour to the group box style and the bet widget."""
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

    def getBonusButtons(self) -> dict[str, SkullKingBonusButton]:
        return self.bonusButtons

    def lockBets(self) -> None:
        self.btWidget.lockBets()

    def unlockBets(self) -> None:
        self.btWidget.unlockBets()

    def lockTricks(self) -> None:
        self.btWidget.lockTricks()

    def unlockTricks(self) -> None:
        self.btWidget.unlockTricks()


class ClickableLabel(QLabel):
    """Circular label that emits clicks and animates a candidate highlight."""

    clicked = QtCore.Signal(Qt.MouseButton)

    def __init__(
        self,
        text: str = "",
        pcolour: QColor | None = None,
        size: int = 40,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(text, parent)

        self.pcolour = pcolour if pcolour is not None else QColor(255, 255, 255)

        self.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.diameter = size
        self.locked = False
        self.candidate = False

        self.setFixedSize(
            self.diameter,
            self.diameter,
        )

        # ---------------------------------------------
        # Custom colour animation
        # ---------------------------------------------

        self.effect = QGraphicsColorizeEffect(self)
        self.effect.setColor(self.pcolour)
        self.effect.setStrength(0.0)
        self.setGraphicsEffect(self.effect)

        self.anim = QPropertyAnimation(
            self.effect,
            b"strength",
        )
        self.anim.setDuration(1800)
        self.anim.setStartValue(0.0)
        self.anim.setKeyValueAt(0.7, 0.7)
        self.anim.setEndValue(0.0)
        self.anim.setLoopCount(-1)

        # ---------------------------------------------
        # QSS state properties
        # ---------------------------------------------

        self.setProperty("locked", False)
        self.setProperty("pressed", False)

        # Apply the instance-specific colour.
        self._update_colour_style()

    # ---------------------------------------------
    # COLOUR
    # ---------------------------------------------

    def setColour(self, colour) -> None:
        self.pcolour = colour

        self.effect.setColor(self.pcolour)

        self._update_colour_style()

    def _update_colour_style(self) -> None:
        """
        Apply only the instance-specific colour.

        The rest of the styling comes from the application's
        global light/dark QSS.
        """

        colour = self.pcolour

        css_colour = f"rgb({colour.red()}, {colour.green()}, {colour.blue()})"

        self.setStyleSheet(
            f"""
            ClickableLabel {{
                font-size: 24px;
                font-weight: bold;
                color: {css_colour};
            }}

            ClickableLabel[locked="true"] {{
                font-size: 24px;
                font-weight: bold;
                border-color: {css_colour};
            }}
            """
        )

    # ---------------------------------------------
    # CANDIDATE
    # ---------------------------------------------

    def isCandidate(self) -> bool:
        return self.candidate

    def setCandidate(self, value) -> None:
        """Toggle the candidate state, starting or stopping its animation."""
        value = bool(value)

        if self.candidate == value:
            return

        self.candidate = value

        if value:
            self.startCandidateAnimation()
        else:
            self.stopCandidateAnimation()

    candidateProperty = Property(
        bool,
        isCandidate,
        setCandidate,
    )

    def startCandidateAnimation(self) -> None:
        self.anim.start()

    def stopCandidateAnimation(self) -> None:
        self.anim.stop()
        self.effect.setStrength(0.0)

    # ---------------------------------------------
    # LOCK
    # ---------------------------------------------

    def isLocked(self) -> bool:
        return self.locked

    def lock(self) -> None:
        if self.locked:
            return

        self.locked = True
        self._set_state_property(
            "locked",
            True,
        )

    def unlock(self) -> None:
        if not self.locked:
            return

        self.locked = False
        self._set_state_property(
            "locked",
            False,
        )

    # ---------------------------------------------
    # PRESS
    # ---------------------------------------------

    def mousePressEvent(self, event: QMouseEvent) -> None:
        """Flash the pressed state briefly and emit the button clicked."""
        self._set_state_property(
            "pressed",
            True,
        )

        self.clicked.emit(event.button())

        QTimer.singleShot(
            180,
            lambda: self._set_state_property(
                "pressed",
                False,
            ),
        )

        super().mousePressEvent(event)

    # ---------------------------------------------
    # QSS STATE
    # ---------------------------------------------

    def _set_state_property(self, name, value) -> None:
        """Set a QSS state property and repolish the widget style."""
        self.setProperty(name, value)

        self.style().unpolish(self)
        self.style().polish(self)

        self.update()


class BetTrickWidget(QWidget):
    """Paired clickable bet and trick counters that cycle through values."""

    changed = QtCore.Signal()

    def __init__(
        self, pcolour: QColor | None = None, size: int = 40, parent=None
    ) -> None:
        super().__init__(parent)
        self.bet = -1
        self.tricks = -1
        self.maxBet = 1
        self.pcolour = pcolour if pcolour else QColor(255, 255, 255)

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

    def isCandidate(self) -> bool:
        return self.betLabel.isCandidate() or self.tricksLabel.isCandidate()

    def setCandidate(self, value) -> None:
        """Highlight the first unset of the bet or trick labels, or clear both."""
        if not value:
            self.betLabel.setCandidate(False)
            self.tricksLabel.setCandidate(False)
        elif self.bet < 0:
            self.tricksLabel.setCandidate(False)
            self.betLabel.setCandidate(True)
        elif self.tricks < 0:
            self.betLabel.setCandidate(False)
            self.tricksLabel.setCandidate(True)

    def setMaxBet(self, bet: int) -> None:
        self.maxBet = bet

    def setBet(self, bet: int) -> None:
        """Set the bet, clamped to the maximum, unless the label is locked."""
        if self.betLabel.isLocked():
            return
        bet = min(bet, self.maxBet)
        self.bet = bet
        if self.bet < 0:
            self.betLabel.setText("-")
            # self.tricksLabel.lock()
        else:
            self.betLabel.setText(str(self.bet))
            # self.tricksLabel.unlock()
        # self.betLabel.highlightChange()
        self.changed.emit()

    def resetBet(self) -> None:
        self.betLabel.unlock()
        self.setBet(-1)

    def resetTricks(self) -> None:
        self.tricksLabel.unlock()
        self.setTricks(-1)
        self.tricksLabel.lock()

    def reset(self) -> None:
        self.resetTricks()
        self.resetBet()

    def getBet(self) -> int:
        return self.bet

    def getTricks(self) -> int:
        return self.tricks

    def setTricks(self, tricks: int) -> None:
        """Set the tricks, clamped to the maximum, unless the label is locked."""
        if self.tricksLabel.isLocked():
            return
        tricks = min(tricks, self.maxBet)
        self.tricks = tricks
        if self.tricks < 0:
            self.tricksLabel.setText("-")
        else:
            self.tricksLabel.setText(str(self.tricks))
        # self.tricksLabel.highlightChange()
        self.changed.emit()

    def cycleBet(self, event: QMouseEvent) -> None:
        """Cycle the bet forward on left-click or backward on right-click."""
        newbet = self.bet
        if event.button() == Qt.MouseButton.LeftButton:
            newbet = (self.bet + 2) % (self.maxBet + 2) - 1
        elif event.button() == Qt.MouseButton.RightButton:
            newbet = self.bet % (self.maxBet + 2) - 1
        self.setBet(newbet)

    def cycleTricks(self, event: QMouseEvent) -> None:
        """Cycle the tricks forward on left-click or backward on right-click."""
        newtricks = self.tricks
        if event.button() == Qt.MouseButton.LeftButton:
            newtricks = (self.tricks + 2) % (self.maxBet + 2) - 1
        if event.button() == Qt.MouseButton.RightButton:
            newtricks = self.tricks % (self.maxBet + 2) - 1
        self.setTricks(newtricks)

    def lockBets(self) -> None:
        self.betLabel.lock()

    def unlockBets(self) -> None:
        self.betLabel.unlock()

    def lockTricks(self) -> None:
        self.tricksLabel.lock()

    def unlockTricks(self) -> None:
        self.tricksLabel.unlock()

    def setColour(self, colour) -> None:
        self.pcolour = colour
        self.betLabel.setColour(colour)
        self.tricksLabel.setColour(colour)


class SkullKingBonusButton(BonusButton):
    """Bonus button specialised for Skull King (behaves as the base button)."""

    pass


class SkullKingRoundsDetail(GameRoundsDetail):
    """Rounds detail view (table, plot and quick stats) for Skull King."""

    def __init__(self, engine, parent=None) -> None:
        self.bgcolors = [0xCCFF99, 0xFFCC99]
        super().__init__(engine, parent)
        self.setCurrentWidget(self.plot)

    def createRoundTable(self, engine, parent=None):
        return SkullKingRoundTable(self.engine, self.bgcolors, parent)

    def createRoundPlot(self, engine, parent=None):
        return SkullKingRoundPlot(self.engine, self)

    def createQSBox(self, parent=None):
        logger.debug("Creating SkullKingQSTW")
        return SkullKingQSTW(
            self.engine.getGame(),  # pyright: ignore[reportArgumentType]
            self.engine.getListPlayers(),
            self,
        )


class SkullKingRoundTable(GameRoundTable):
    """Per-round score table colouring cells by positive or negative score."""

    def __init__(self, engine, bgcolors: list[int], parent=None) -> None:
        self.bgcolors = bgcolors
        super().__init__(engine, parent)

    def insertRound(self, rnd: GenericRound) -> None:
        """Append a table row with each player's score for ``rnd``."""
        winner = rnd.getWinner()
        i = rnd.getNumRound() - 1
        self.insertRow(i)
        hands = self.engine.getHands(rnd.getNumRound())
        hitem = QTableWidgetItem(f"{hands}")
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
    """Cumulative score-over-rounds plot for Skull King."""

    def updatePlot(self) -> None:
        """Recompute and redraw each player's cumulative score series."""
        super().updatePlot()
        if not self.isPlotInited():
            return
        scores = {}
        roundNames = [""]
        for player in self.engine.getPlayers():
            scores[player] = [0]
        for i, roundName in enumerate(
            cast(SkullKingEngine, self.engine).getRoundSequence()
        ):
            roundNames.append(f"{roundName}")
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
    """Quick-stats tab set pairing general and player-filtered Skull King stats."""

    def initStatsWidgets(self) -> None:
        self.gs = SkullKingQSBox(self.game, self)
        self.ps = SkullKingPQSBox(self.game, self)


class SkullKingQSBox(GeneralQuickStats):
    """General quick-stats page adding hit-rate and best-round columns."""

    def __init__(self, gname: str, parent) -> None:
        super().__init__(gname, parent)
        self.playerStatsKeys.append("max_hits")
        self.playerStatsHeaders.append(self.tr("Max Hit %"))
        self.playerStatsKeys.append("avg_hits")
        self.playerStatsHeaders.append(self.tr("Avg Hit %"))
        self.playerStatsKeys.append("max_round_score")
        self.playerStatsHeaders.append(self.tr("Best Round"))
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
    """Player-filtered variant of the Skull King quick-stats page."""

    pass
