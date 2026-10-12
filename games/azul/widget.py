"""Azul and Azul: Summer Pavilion scoreboard widgets: per-player score and
bonus input, round table and plot."""

from __future__ import annotations

from typing import cast

from PySide6 import QtCore, QtGui
from PySide6.QtCore import QCoreApplication
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from core.ui.game import (
    ColourBonusButton,
    ColourIconHeader,
    GameInputWidget,
    GameNotImplementedException,
    GameRoundPlot,
    GameRoundsDetail,
    GameRoundTable,
    GameWidget,
    ScoreSpinBox,
    StatsTable,
)
from core.ui.game.stats import GeneralQuickStats, ParticularQuickStats, QuickStatsTW
from games.azul.engine import AzulEngine, AzulSummerPavilionEngine
from games.azul.model import AzulRound, AzulSummerPavilionMatch

# Icon of the button for each bonus kind.
ICONS = {
    "rows": "azul_rows",
    "columns": "azul_columns",
    "colours": "azul_colours",
    "star_multi": "azul_sp_star_multi",
    "star_red": "azul_sp_star",
    "star_blue": "azul_sp_star",
    "star_yellow": "azul_sp_star",
    "star_orange": "azul_sp_star",
    "star_green": "azul_sp_star",
    "star_purple": "azul_sp_star",
    "ones": "azul_sp_ones",
    "twos": "azul_sp_twos",
    "threes": "azul_sp_threes",
    "fours": "azul_sp_fours",
}

# Bonuses drawn in their own colour rather than the player's.
BONUS_COLOURS = {
    "star_multi": QColor(128, 128, 128),
    "star_red": QColor(215, 54, 43),
    "star_blue": QColor(47, 111, 214),
    "star_yellow": QColor(214, 166, 20),
    "star_orange": QColor(238, 125, 34),
    "star_green": QColor(60, 154, 63),
    "star_purple": QColor(138, 79, 198),
}

# Bonus names, translated in the "AzulInputWidget" context.
LABELS = {
    "rows": "Complete rows (+2 each)",
    "columns": "Complete columns (+7 each)",
    "colours": "Complete colours (+10 each)",
    "star_multi": "Multicoloured star (+12)",
    "star_red": "Red star (+14)",
    "star_blue": "Blue star (+15)",
    "star_yellow": "Yellow star (+16)",
    "star_orange": "Orange star (+17)",
    "star_green": "Green star (+18)",
    "star_purple": "Purple star (+20)",
    "ones": "All 1s (+4)",
    "twos": "All 2s (+8)",
    "threes": "All 3s (+12)",
    "fours": "All 4s (+16)",
}
QCoreApplication.translate("AzulInputWidget", "Complete rows (+2 each)")
QCoreApplication.translate("AzulInputWidget", "Complete columns (+7 each)")
QCoreApplication.translate("AzulInputWidget", "Complete colours (+10 each)")
QCoreApplication.translate("AzulInputWidget", "Multicoloured star (+12)")
QCoreApplication.translate("AzulInputWidget", "Red star (+14)")
QCoreApplication.translate("AzulInputWidget", "Blue star (+15)")
QCoreApplication.translate("AzulInputWidget", "Yellow star (+16)")
QCoreApplication.translate("AzulInputWidget", "Orange star (+17)")
QCoreApplication.translate("AzulInputWidget", "Green star (+18)")
QCoreApplication.translate("AzulInputWidget", "Purple star (+20)")
QCoreApplication.translate("AzulInputWidget", "All 1s (+4)")
QCoreApplication.translate("AzulInputWidget", "All 2s (+8)")
QCoreApplication.translate("AzulInputWidget", "All 3s (+12)")
QCoreApplication.translate("AzulInputWidget", "All 4s (+16)")


def bonusLabel(key: str) -> str:
    return QCoreApplication.translate("AzulInputWidget", LABELS[key])


class AzulWidget(GameWidget):
    """Scoreboard tab for Azul and Azul: Summer Pavilion."""

    def createEngine(self) -> None:
        if self.game == "Azul":
            self.engine = AzulEngine()
        elif self.game == AzulSummerPavilionMatch.gameName:
            self.engine = AzulSummerPavilionEngine()
        else:
            raise GameNotImplementedException(f"No engine for game {self.game}")

    def initUI(self) -> None:
        super().initUI()
        self.retranslateUI()

    def createGameInputWidget(self, parent: QWidget | None = None) -> AzulInputWidget:
        return AzulInputWidget(self.engine, parent)

    def createRoundsDetail(self, parent: QWidget | None = None) -> AzulRoundsDetail:
        return AzulRoundsDetail(self.engine, parent)

    def getPlayerExtraInfo(self, player: str) -> dict:
        """Return the bonus counts selected for ``player``."""
        return cast("AzulInputWidget", self.gameInput).getBonuses()[player]

    def checkPlayerScore(
        self, player: str, score: int, extras: dict | None = None
    ) -> bool:
        # Floor-line penalties can make a round score negative.
        return score is not None

    def commitRoundSanityCheck(self, interactive: bool = False) -> bool:
        """Check every player has a score, and, in Azul, that column or colour
        bonuses only come with the row that ends the game."""
        gameInput = cast("AzulInputWidget", self.gameInput)
        for player, score in gameInput.getScores().items():
            if not self.checkPlayerScore(player, score):
                if interactive:
                    msg = self.tr("{} score is not valid").format(player)
                    QMessageBox.warning(self, self.game, msg)
                return False
        ending = cast("AzulEngine", self.engine).getEndingBonus()
        if ending is None:
            return True
        bonuses = gameInput.getBonuses().values()
        anyEnding = any(b[ending] for b in bonuses)
        anyOther = any(v for b in bonuses for k, v in b.items() if k != ending)
        if anyOther and not anyEnding:
            if interactive:
                msg = self.tr(
                    "Column and colour bonuses are only scored at the end of "
                    "the game, once someone completes a row"
                )
                QMessageBox.warning(self, self.game, msg)
            return False
        return True


class AzulInputWidget(GameInputWidget):
    """Score-entry widget: one box per player with points and bonuses."""

    def initUI(self) -> None:
        self.widgetLayout = QHBoxLayout(self)
        for player in self.engine.getListPlayers():
            piw = AzulPlayerInputWidget(
                player, cast("AzulEngine", self.engine), self.playerColour(player), self
            )
            self.playerInputList[player] = piw
            self.widgetLayout.addWidget(piw)
            piw.changed.connect(self.changed)

    def retranslateUI(self) -> None:
        for piw in self.playerInputList.values():
            piw.retranslateUI()

    def getBonuses(self) -> dict[str, dict[str, int]]:
        return {p: piw.getBonuses() for p, piw in self.playerInputList.items()}

    # Scores may still be missing, so this widens the base return to None.
    def getWinner(self) -> str | None:  # pyright: ignore[reportIncompatibleMethodOverride]
        """Return the player with the best round, once every score is in."""
        scores = self.getScores()
        if any(score is None for score in scores.values()):
            return None
        return max(scores, key=lambda p: scores[p])

    def updatePlayerOrder(self) -> None:
        for piw in self.playerInputList.values():
            self.widgetLayout.removeWidget(piw)
        for player in self.engine.getListPlayers():
            piw = self.playerInputList[player]
            self.widgetLayout.addWidget(piw)
            piw.setColour(self.playerColour(player))


class AzulPlayerInputWidget(QGroupBox):
    """One player's round: wall points plus end-of-game bonus buttons."""

    changed = QtCore.Signal()

    def __init__(
        self,
        player: str,
        engine: AzulEngine,
        colour: QColor | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.player = player
        self.engine = engine
        self.pcolour = colour if colour else QColor(0, 0, 0)
        self.initUI()
        self.reset()

    def initUI(self) -> None:
        self.setTitle(self.player)
        self.mainLayout = QVBoxLayout(self)

        self.scoreSpinBox = ScoreSpinBox(self)
        self.scoreSpinBox.setHideMinimum(False)
        self.scoreSpinBox.setRange(*self.engine.getRoundScoreRange(), 0)
        self.scoreSpinBox.valueChanged.connect(self.changed)
        self.mainLayout.addWidget(self.scoreSpinBox)

        # One centred row of buttons per bonus group; the last row ends with
        # the bonus points label, balanced by an equally wide blank on the
        # left so its buttons stay centred too.
        groups = self.engine.getBonusGroups()
        size = 48 if max(len(group) for group in groups) <= 3 else 32
        labelWidth = 48
        self.bonusButtons: dict[str, ColourBonusButton] = {}
        self.bonusLabel = QLabel(self)
        self.bonusLabel.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.bonusLabel.setFixedWidth(labelWidth)
        for i, group in enumerate(groups):
            last = i == len(groups) - 1
            row = QHBoxLayout()
            row.setSpacing(4)
            self.mainLayout.addLayout(row)
            row.addStretch()
            if last:
                row.addSpacing(labelWidth)
            for key in group:
                button = ColourBonusButton(
                    ICONS[key],
                    self.engine.getMaxBonuses(),
                    BONUS_COLOURS.get(key, self.pcolour),
                    size,
                    self,
                )
                button.bonusChanged.connect(self.updateBonusLabel)
                button.bonusChanged.connect(self.changed)
                self.bonusButtons[key] = button
                row.addWidget(button)
            if last:
                row.addWidget(self.bonusLabel)
            row.addStretch()

        self.setColour(self.pcolour)
        self.retranslateUI()

    def retranslateUI(self) -> None:
        for key, button in self.bonusButtons.items():
            button.setToolTip(bonusLabel(key))

    def setColour(self, colour: QColor) -> None:
        self.pcolour = colour
        r, g, b = colour.red(), colour.green(), colour.blue()
        self.setStyleSheet(f"""
            QGroupBox {{ font-size: 24px; font-weight: bold; color: rgb({r},{g},{b}); }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                subcontrol-position: top center;
                padding: 0 10px;
                background-color: transparent;
            }}
        """)
        self.bonusLabel.setStyleSheet(
            f"font-size: 18px; font-weight: bold; color: rgb({r},{g},{b});"
        )
        self.scoreSpinBox.setColour(colour)
        for key, button in self.bonusButtons.items():
            button.setColour(BONUS_COLOURS.get(key, colour))

    def reset(self) -> None:
        """Clear the score and bonuses; bonuses only once they are possible."""
        self.scoreSpinBox.setValue(None)
        allowed = self.engine.bonusesAllowed()
        for button in self.bonusButtons.values():
            button.setChecked(False)
            button.setEnabled(allowed)
        self.updateBonusLabel()

    def updateBonusLabel(self, *_args) -> None:
        """Show the points the selected bonuses add to the round."""
        points = self.engine.bonusPoints(self.getBonuses())
        self.bonusLabel.setText(f"+{points}" if points else "")

    def getBonuses(self) -> dict[str, int]:
        return {key: b.getValue() for key, b in self.bonusButtons.items()}

    def getScore(self) -> int | None:
        """Return the round's wall points plus bonuses, or None if not entered."""
        points = self.scoreSpinBox.value()
        if points is None:
            return None
        return points + self.engine.bonusPoints(self.getBonuses())

    def getPlayer(self) -> str:
        return self.player


class AzulRoundsDetail(GameRoundsDetail):
    """Rounds detail panel for Azul, with each player's end-of-game bonuses
    once the game has finished."""

    def __init__(self, engine, parent: QWidget | None = None) -> None:
        self.bgcolors = [0xCCFF99, 0xFFCC99]
        super().__init__(engine, parent)
        self.setCurrentWidget(self.plot)

    def initUI(self) -> None:
        """Build the base tabs plus the bonus totals table."""
        super().initUI()
        bonuses = cast("AzulEngine", self.engine).getBonuses()
        self.totalsLabel = QLabel("", self)
        self.tableContainerLayout.addWidget(self.totalsLabel)
        self.totals = StatsTable(len(bonuses), len(self.engine.getPlayers()))
        self.totals.setEditTriggers(StatsTable.EditTrigger.NoEditTriggers)
        self.totals.setVerticalHeader(
            ColourIconHeader(
                [ICONS[key] for key in bonuses],
                self.totals,
                [BONUS_COLOURS.get(key) for key in bonuses],
            )
        )
        for row in range(len(bonuses)):
            self.totals.setVerticalHeaderItem(row, QTableWidgetItem(""))
        self.tableContainerLayout.addWidget(self.totals)
        self.totals.setMaximumHeight(self.totals.sizeHint().height())

    def retranslateUI(self) -> None:
        for row, key in enumerate(cast("AzulEngine", self.engine).getBonuses()):
            header = self.totals.verticalHeaderItem(row)
            if header:
                header.setToolTip(bonusLabel(key))
        self.totalsLabel.setText(self.tr("Bonuses"))
        super().retranslateUI()

    def updateRound(self) -> None:
        """Rebuild the base table and, once the game is over, the bonuses."""
        super().updateRound()
        finished = bool(self.engine.getWinner())
        self.totalsLabel.setVisible(finished)
        self.totals.setVisible(finished)
        if not finished:
            return
        engine = cast("AzulEngine", self.engine)
        players = engine.getListPlayers()
        self.totals.setHorizontalHeaderLabels(players)
        self.totals.clearContents()
        for col, player in enumerate(players):
            bonuses = engine.getPlayerBonuses(player)
            for row, (key, count) in enumerate(bonuses.items()):
                points = engine.bonusPoints({key: count})
                if engine.getMaxBonuses() == 1:
                    # A bonus earned at most once: just its points.
                    text = f"+{points}" if count else ""
                else:
                    text = f"{count} (+{points})" if count else "0"
                item = QTableWidgetItem(text)
                item.setTextAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
                self.totals.setItem(row, col, item)

    def createRoundTable(self, engine, parent: QWidget | None = None):
        return AzulRoundTable(self.engine, self.bgcolors, parent)

    def createRoundPlot(self, engine, parent: QWidget | None = None):
        return AzulRoundPlot(self.engine, self)

    def createQSBox(self, parent: QWidget | None = None):
        return AzulQSTW(
            self.engine.getGame(),  # pyright: ignore[reportArgumentType]
            self.engine.getListPlayers(),
            self,
        )


class AzulRoundTable(GameRoundTable):
    """Per-round score table, showing any bonuses in the final round."""

    def __init__(self, engine, bgcolors, parent: QWidget | None = None) -> None:
        self.bgcolors = bgcolors
        super().__init__(engine, parent)

    def insertRound(self, r) -> None:
        """Append a row for round ``r`` with each player's score."""
        rnd = cast("AzulRound", r)
        i = rnd.getNumRound() - 1
        self.insertRow(i)
        for j, player in enumerate(self.engine.getListPlayers()):
            item = QTableWidgetItem()
            item.setFlags(item.flags() ^ QtCore.Qt.ItemFlag.ItemIsEditable)
            item.setTextAlignment(
                QtCore.Qt.AlignmentFlag.AlignVCenter
                | QtCore.Qt.AlignmentFlag.AlignCenter
            )
            score = rnd.getPlayerScore(player)
            bonuses = rnd.getBonuses(player)
            bonus = self.engine.bonusPoints(bonuses)
            text = str(score)
            if bonus:
                text += f" (+{bonus})"
                item.setToolTip(
                    "\n".join(
                        f"{bonusLabel(key)}: {count}"
                        for key, count in bonuses.items()
                        if count
                    )
                )
            background = self.bgcolors[0] if score > 0 else self.bgcolors[1]
            item.setBackground(QtGui.QBrush(QtGui.QColor(background)))
            item.setForeground(QtGui.QBrush(QtGui.QColor(0, 0, 0)))
            item.setText(text)
            self.setItem(i, j, item)
        self.scrollToBottom()


class AzulRoundPlot(GameRoundPlot):
    """Cumulative score plot."""

    def updatePlot(self) -> None:
        super().updatePlot()
        if not self.isPlotInited():
            return
        initial = self.engine.getInitialScore()
        scores = {}
        for player in self.engine.getPlayers():
            scores[player] = [initial]

        for rnd in self.engine.getRounds():
            for player in self.engine.getPlayers():
                accumscore = scores[player][-1] + rnd.getPlayerScore(player)
                scores[player].append(accumscore)

        self.canvas.clearPlotContents()
        for player in self.engine.getListPlayers():
            self.canvas.addSeries(scores[player], player)


class AzulQSTW(QuickStatsTW):
    """Quick-stats tab set for Azul and Azul: Summer Pavilion."""

    def initStatsWidgets(self) -> None:
        self.gs = AzulQSBox(self.game, self)
        self.ps = AzulPQSBox(self.game, self)


class AzulQSBox(GeneralQuickStats):
    """General quick-stats page: best end-of-game bonus per match size and
    per player, without the lowest and total player scores."""

    QCoreApplication.translate("AzulQSBox", "Max bonus")

    def __init__(self, gname: str, parent: QWidget | None = None) -> None:
        super().__init__(gname, parent)
        self.matchStatsKeys.append("maxbonus")
        self.matchStatsHeaders.append("Max bonus")
        for key in ("minscore", "sumscore"):
            i = self.playerStatsKeys.index(key)
            del self.playerStatsKeys[i]
            del self.playerStatsHeaders[i]
        self.playerStatsKeys.append("maxbonus")
        self.playerStatsHeaders.append("Max bonus")


class AzulPQSBox(AzulQSBox, ParticularQuickStats):
    """Player-filtered variant of the Azul quick-stats page."""
