"""Qwirkle board widget, built by specialising the Scrabble widgets."""

from __future__ import annotations

from typing import cast

from PySide6 import QtCore
from PySide6.QtWidgets import QHBoxLayout, QLabel, QSizePolicy, QWidget

from core.engine.settings import appsettings
from core.ui.game import (
    BonusButton,
    GameNotImplementedException,
    ScoreSpinBox,
)
from core.ui.gamestats import GeneralQuickStats, ParticularQuickStats
from games.qwirkle.engine import QwirkleEngine
from games.scrabble.widget import (
    ScrabbleEntriesDetail,
    ScrabbleEntriesPlot,
    ScrabbleInputWidget,
    ScrabbleQSTW,
    ScrabbleRoundTable,
    ScrabbleWidget,
)


class QwirkleWidget(ScrabbleWidget):
    """Board widget for Qwirkle (Scrabble-style entry scoring with qwirkles)."""

    dealer_policy_setting_key = "qwirkle_dealer_policy"

    def createEngine(self) -> None:
        if self.game != "Qwirkle":
            raise GameNotImplementedException(f"No engine for game {self.game}")
        self.engine = QwirkleEngine()

    def createGameInputWidget(self, parent: QWidget | None = None):  # pyright: ignore[reportIncompatibleMethodOverride]
        return QwirkleInputWidget(self.engine, parent)

    def createRoundsDetail(self, parent: QWidget | None = None):
        return QwirkleEntriesDetail(self.engine, parent)

    def addExtraConfig(self) -> None:
        """Add the per-turn countdown spin box, using the Qwirkle-specific setting."""
        # Build the same layout as ScrabbleWidget.addExtraConfig but with our key.
        self.turnTimeLayout = QHBoxLayout()
        self.matchGroupLayout.addLayout(self.turnTimeLayout)
        self.turnTimeLabel = QLabel("⏱", self.matchGroup)
        self.turnTimeLabel.setSizePolicy(
            QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred
        )
        self.turnTimeLayout.addWidget(self.turnTimeLabel)
        saved_time = int(appsettings["qwirkle_turn_time"] or 120)
        self.turnSecondsBox = ScoreSpinBox(self.matchGroup)
        self.turnSecondsBox.setRange(10, 600, saved_time)
        self.turnSecondsBox.setValue(saved_time)
        self.turnSecondsBox.lineEdit().setFocusPolicy(QtCore.Qt.FocusPolicy.ClickFocus)
        self.turnSecondsBox.setSizePolicy(
            QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Maximum
        )
        self.turnSecondsBox.valueChanged.connect(self.changeTurnSeconds)
        self.turnTimeLayout.addWidget(self.turnSecondsBox)

    def changeTurnSeconds(self, value: int | None = None) -> None:
        """Apply the new turn duration, persist it, and reset the countdown."""
        if value is None:
            value = self.turnSecondsBox.value()
        if value is None:
            return
        appsettings.set("qwirkle_turn_time", int(value))
        gi = cast("ScrabbleInputWidget", self.gameInput)
        gi.countdown.reset(int(value))
        gi.countdown.start()

    def checkPlayerScore(
        self, player: str, score: int, extras: dict | None = None
    ) -> bool:
        """Validate a Qwirkle entry: non-negative and consistent with qwirkles."""
        try:
            if score < 0 or not extras:
                return False
            qwirkles = extras["qwirkles"]
            return score >= 12 * qwirkles
        except (KeyError, TypeError):
            return False


class QwirkleInputWidget(ScrabbleInputWidget):
    """Score-entry widget adding qwirkle bonus buttons."""

    spacePressed = QtCore.Signal()

    def initUI(self) -> None:
        super().initUI()
        self.scoreSpinBox.setRange(-1, 84, 0)
        self.reset()

    def createBonusButtons(self) -> None:
        """Build one bonus button per configured qwirkle bonus."""
        # self.currentPlayerBoxLayout.insertSpacing(0, 64)
        for b, maxreps in cast("QwirkleEngine", self.engine).getBonuses().items():
            bb = BonusButton(
                b, maxreps, colour=None, size=64, parent=self.currentPlayerBox
            )
            self.bonusButtons[b] = bb
            self.currentPlayerBoxLayout.addWidget(bb)
            self.spacePressed.connect(bb.plusone)
            self.scoreSpinBox.spacePressed.connect(bb.plusone)
            bb.bonusChanged.connect(self.changed)


class QwirkleEntriesDetail(ScrabbleEntriesDetail):
    """Rounds-detail tab set for Qwirkle."""

    def createRoundTable(self, engine, parent: QWidget | None = None):
        return QwirkleRoundTable(self.engine, parent)

    def createRoundPlot(self, engine, parent: QWidget | None = None):
        return QwirkleEntriesPlot(self.engine, self)

    def createQSBox(self, parent: QWidget | None = None):
        return QwirkleQSTW(
            self.engine.getGame(),  # pyright: ignore[reportArgumentType]
            self.engine.getListPlayers(),
            self,
        )


class QwirkleRoundTable(ScrabbleRoundTable):
    """Per-entry score table for Qwirkle."""


class QwirkleEntriesPlot(ScrabbleEntriesPlot):
    """Score-over-time plot for Qwirkle."""


class QwirkleQSTW(ScrabbleQSTW):
    """Quick-stats tab set for Qwirkle."""

    def initStatsWidgets(self) -> None:
        self.gs = QwirkleQSBox(self.game, self)
        self.ps = QwirklePQSBox(self.game, self)


class QwirkleQSBox(GeneralQuickStats):
    """General quick-stats page adding best-play and max-qwirkles columns."""

    def __init__(self, gname: str, parent: QWidget | None = None) -> None:
        super().__init__(gname, parent)
        self.playerStatsKeys.append("max_round_score")
        self.playerStatsHeaders.append(self.tr("Best Play"))
        self.playerStatsKeys.append("max_qwirkles")
        self.playerStatsHeaders.append(self.tr("Max Qs"))
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


class QwirklePQSBox(QwirkleQSBox, ParticularQuickStats):
    """Player-filtered variant of the Qwirkle quick-stats page."""
