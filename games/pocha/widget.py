"""Qt scoreboard widgets for Pocha: hand-bidding input, round table and plot."""

from __future__ import annotations

from typing import cast

from PySide6 import QtCore, QtGui
from PySide6.QtCore import QCoreApplication
from PySide6.QtGui import QColor, QKeyEvent
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

from core.model.base import GenericRound
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
    """Scoreboard tab for Pocha, adding deck-suit selection and hand progress."""

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

    def createEngine(self) -> None:
        if self.game != "Pocha":
            raise GameNotImplementedException(f"No engine for game {self.game}")
        self.engine = PochaEngine()

    def initUI(self) -> None:
        super().initUI()
        self.retranslateUI()

    def createGameInputWidget(self, parent: QWidget | None = None) -> PochaInputWidget:
        return PochaInputWidget(self.engine, parent)

    def createRoundsDetail(self, parent: QWidget | None = None) -> PochaRoundsDetail:
        return PochaRoundsDetail(self.engine, parent)

    def retranslateUI(self) -> None:
        super().retranslateUI()
        self.spanishSuitRadio.setText(self.tr("Spanish Deck"))
        self.frenchSuitRadio.setText(self.tr("French Deck"))
        self.detailGroup.retranslateUI()

    def addExtraConfig(self) -> None:
        """Add the hand-progress bar and the Spanish/French deck selector."""
        super().addExtraConfig()
        self.progressBar = StepProgressBar(
            # Hand counts (ints) are rendered as step labels via str().
            cast("PochaEngine", self.engine).getRoundSequence(),  # pyright: ignore[reportArgumentType]
            self,
        )
        self.progressBar.setCurrentStep(self.engine.getNumRound() - 1)
        # self.matchGroupLayout.addWidget(self.progressBar)
        self.matchGroupLayout.insertWidget(1, self.progressBar)

        self.configLayout = QGridLayout()
        # self.matchGroupLayout.insertLayout(3, self.configLayout)
        self.matchGroupLayout.addLayout(self.configLayout)
        self.suitTypeGroup = QButtonGroup(self)
        self.spanishSuitRadio = QRadioButton(self)
        self.spanishSuitRadio.setChecked(
            cast("PochaEngine", self.engine).getSuitType() == "spanish"
        )
        self.spanishSuitRadio.toggled.connect(self.changeSuit)
        self.suitTypeGroup.addButton(self.spanishSuitRadio)
        self.configLayout.addWidget(self.spanishSuitRadio)
        self.frenchSuitRadio = QRadioButton(self)
        self.suitTypeGroup.addButton(self.frenchSuitRadio)
        self.configLayout.addWidget(self.frenchSuitRadio)
        self.frenchSuitRadio.setChecked(
            cast("PochaEngine", self.engine).getSuitType() == "french"
        )
        self.dealerPolicyCheckBox.hide()

    def changeSuit(self, *_args) -> None:
        """Switch the engine between the Spanish and French card decks."""
        if self.spanishSuitRadio.isChecked():
            cast("PochaEngine", self.engine).setSuitType("spansih")
        elif self.frenchSuitRadio.isChecked():
            cast("PochaEngine", self.engine).setSuitType("french")
        self.retranslateUI()

    def setRoundTitle(self) -> None:
        """Show the game name plus the current hand count and direction."""
        if self.engine.getWinner():
            self.roundTitleLabel.setText(f"{self.engine.getGame()}")
            return
        hands = cast("PochaEngine", self.engine).getHands()
        direction = cast("PochaEngine", self.engine).getDirection()
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

    def checkPlayerScore(
        self, player: str, score: int, extras: dict | None = None
    ) -> bool:
        return True

    def updatePanel(self) -> None:
        super().updatePanel()
        self.progressBar.setCurrentStep(self.engine.getNumRound() - 1)
        # self.spanishSuitRadio.setDisabled(self.engine.getNumRound() > 1)
        # self.frenchSuitRadio.setDisabled(self.engine.getNumRound() > 1)

    def commitRoundSanityCheck(self, interactive: bool = False) -> bool:
        """Verify the selected won hands add up to the number played."""
        hands = cast("PochaEngine", self.engine).getHands()
        wonhands = cast("PochaInputWidget", self.gameInput).getWonHands()
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

    def setFocus(self, _reason=None) -> None:
        self.gameInput.setFocus()


class PochaInputWidget(GameInputWidget):
    """Per-player expected/won hand selectors making up a Pocha round."""

    def __init__(self, engine, parent: QWidget | None = None) -> None:
        super().__init__(engine, parent)
        self.lastChoices: list[tuple[str, str]] = []

    def initUI(self) -> None:
        """Lay out one hand-selector box per player in a grid."""
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

    def newChoice(self, mode: str, player: str) -> None:
        self.lastChoices.append((mode, player))

    def reset(self) -> None:
        super().reset()
        self.lastChoices = []

    def getWonHands(self) -> dict[str, int]:
        """Return each player's currently selected number of won hands."""
        won = {}
        for player, piw in self.playerInputList.items():
            won[player] = piw.getWonHands()
        return won

    def getExpectedHands(self) -> dict[str, int]:
        """Return each player's currently selected number of expected hands."""
        expected = {}
        for player, piw in self.playerInputList.items():
            expected[player] = piw.getExpectedHands()
        return expected

    def checkExpected(self) -> None:
        """Enable/disable selectors so the forbidden bid stays unavailable."""
        notselected = []
        totalexpected = 0
        hands = cast("PochaEngine", self.engine).getHands()
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

    def keyPressEvent(self, event: QKeyEvent) -> None:
        """Feed number keys into the selectors; Backspace undoes the last choice."""
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
            number = numberkeys.index(cast("QtCore.Qt.Key", event.key()))
        except ValueError:
            return super().keyPressEvent(event)

        if number in range(9):
            self.feedNumber(number)

        return super().keyPressEvent(event)

    def feedNumber(self, number: int) -> None:
        """Apply ``number`` to the next unset expected (then won) selector in order."""
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
                return

        return

    def updatePlayerOrder(self) -> None:
        """Re-lay the player selectors and recolour them in the new order."""
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
    """A single player's expected/won hand button rows for one round."""

    winnerSet = QtCore.Signal(str)
    newExpected = QtCore.Signal()
    handsClicked = QtCore.Signal(str, str)
    changed = QtCore.Signal()

    def __init__(
        self,
        player: str,
        engine,
        colour: QColor | None = None,
        parent: QWidget | None = None,
    ) -> None:
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
        self.expectedButtons: list[PochaHandsButton] = []

        self.wonGroupBox = QFrame(self)
        self.mainLayout.addWidget(self.wonGroupBox)
        self.wbLayout = QHBoxLayout(self.wonGroupBox)
        self.wbLayout.setSpacing(2)
        self.wbLayout.setContentsMargins(2, 2, 2, 2)
        self.wonGroup = QButtonGroup(self)
        self.wonGroup.buttonReleased.connect(self.wonClickedAction)
        self.wonButtons: list[PochaHandsButton] = []
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

    def reset(self) -> None:
        """Reset both rows to zero and re-enable them for a fresh round."""
        self.expectedButtons[0].setChecked(True)
        self.wonButtons[0].setChecked(True)
        self.refreshButtons()
        self.disableWonRow()

    def refreshButtons(self, forbidden: int = -1) -> None:
        """Show/enable only the hand buttons valid for the current hand count."""
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

    def disableWonRow(self, disable: bool = True) -> None:
        """Disable the won-hands row until an expected bid has been made."""
        if self.getExpectedHands() < 0:
            self.wonGroupBox.setDisabled(True)
        else:
            self.wonGroupBox.setDisabled(disable)

    def enableWonGroup(self, _button) -> None:
        self.newExpected.emit()

    def isWinner(self) -> bool:
        return False

    def getPlayer(self) -> str:
        return self.player

    def getScore(self) -> int:
        """Compute this player's round score from their expected/won bids."""
        expected = self.expectedGroup.checkedId()
        won = self.wonGroup.checkedId()
        if expected < 0 or won < 0:
            return 0
        if expected == won:
            return 10 + 3 * won
        return -3 * abs(expected - won)

    def getWonHands(self) -> int:
        return self.wonGroup.checkedId()

    def getExpectedHands(self) -> int:
        return self.expectedGroup.checkedId()

    def setExpectedHands(self, number: int) -> bool:
        """Select ``number`` expected hands; return whether it was applied."""
        if number < 0:
            self.expectedButtons[0].toggle()
            return True
        button = self.expectedGroup.button(number)
        if button.isEnabled():
            button.toggle()
            return True
        return False

    def setWonHands(self, number: int) -> bool:
        """Select ``number`` won hands; return whether it was applied."""
        if number < 0:
            self.wonButtons[0].toggle()
            return True
        button = self.wonGroup.button(number)
        if button.isEnabled():
            button.toggle()
            return True
        return False

    def expectedClickedAction(self, _) -> None:
        self.handsClicked.emit("expected", self.player)

    def wonClickedAction(self, _) -> None:
        self.handsClicked.emit("won", self.player)

    def setColour(self, colour: QColor) -> None:
        """Restyle the box and its buttons in ``colour``."""
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
    """A small checkable button standing for one possible hand count."""

    def __init__(self, text: str = "", parent: QWidget | None = None) -> None:
        super().__init__(text, parent)
        self.setCheckable(True)
        self.setMinimumSize(25, 25)
        self.setSizePolicy(
            QSizePolicy.Policy.MinimumExpanding, QSizePolicy.Policy.Maximum
        )
        self.toggled.connect(self.setColour)
        self.setColour(False)

    def setColour(self, _toggle) -> None:
        return
        # if _toggle:
        #     self.setStyleSheet("background-color: red; font: bold")
        # else:
        #     self.setStyleSheet("background-color: lightgreen; font: normal")

    def setDisabled(self, disabled: bool = True) -> None:
        return super().setDisabled(disabled)
        if disabled:
            self.setStyleSheet("background-color: none; font: normal")
        else:
            self.setColour(self.isChecked())
        return super().setDisabled(disabled)


class PochaRoundsDetail(GameRoundsDetail):
    """Rounds-detail panel for Pocha, opening on the score plot."""

    def __init__(self, engine, parent: QWidget | None = None) -> None:
        self.bgcolors = [0xCCFF99, 0xFFCC99]
        super().__init__(engine, parent)
        self.setCurrentWidget(self.plot)

    def createRoundTable(self, engine, parent: QWidget | None = None):
        return PochaRoundTable(self.engine, self.bgcolors, parent)

    def createRoundPlot(self, engine, parent: QWidget | None = None):
        return PochaRoundPlot(self.engine, self)

    def createQSBox(self, parent: QWidget | None = None):
        return PochaQSTW(
            self.engine.getGame(),  # pyright: ignore[reportArgumentType]
            self.engine.getListPlayers(),
            self,
        )


class PochaRoundTable(GameRoundTable):
    """Per-round score table for Pocha, colouring gains and losses."""

    def __init__(self, engine, bgcolors: list[int], parent: QWidget | None = None):
        self.bgcolors = bgcolors
        super().__init__(engine, parent)

    def insertRound(self, r: GenericRound) -> None:
        """Append a row for round ``r`` with per-player scores and the winner."""
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
    """Cumulative score-over-rounds plot for Pocha."""

    def retranslatePlot(self) -> None:
        self.updatePlot()

    def updatePlot(self) -> None:
        """Redraw the running-total series, one line per player."""
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
    """Quick-stats tab set for Pocha."""

    def initStatsWidgets(self) -> None:
        self.gs = PochaQSBox(self.game, self)
        self.ps = PochaPQSBox(self.game, self)


class PochaQSBox(GeneralQuickStats):
    """General quick-stats page adding Pocha hit and best-round columns."""

    QCoreApplication.translate("GeneralQuickStats", "Max Hits")
    QCoreApplication.translate("GeneralQuickStats", "Min Hits")
    QCoreApplication.translate("GeneralQuickStats", "Best Round")

    def __init__(self, gname: str, parent) -> None:
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
    """Player-filtered variant of the Pocha quick-stats page."""
