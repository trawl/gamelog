"""Qwirkle board widget, built by specialising the Scrabble widgets."""

from __future__ import annotations

from typing import cast

from PySide6 import QtCore
from PySide6.QtWidgets import QWidget

from core.ui.game import (
    BonusButton,
    GameNotImplementedException,
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

    def createEngine(self) -> None:
        if self.game != "Qwirkle":
            raise GameNotImplementedException(f"No engine for game {self.game}")
        self.engine = QwirkleEngine()

    def createGameInputWidget(self, parent: QWidget | None = None):  # pyright: ignore[reportIncompatibleMethodOverride]
        return QwirkleInputWidget(self.engine, parent)

    def createRoundsDetail(self, parent: QWidget | None = None):
        return QwirkleEntriesDetail(self.engine, parent)

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
        self.currentPlayerBoxLayout.insertSpacing(0, 64)
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
