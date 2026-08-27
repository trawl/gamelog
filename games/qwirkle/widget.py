from PySide6 import QtCore

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
    def createEngine(self):
        if self.game != "Qwirkle":
            raise GameNotImplementedException(f"No engine for game {self.game}")
        self.engine = QwirkleEngine()

    def createGameInputWidget(self, parent=None):  # pyright: ignore[reportIncompatibleMethodOverride]
        return QwirkleInputWidget(self.engine, parent)

    def createRoundsDetail(self, parent=None):
        return QwirkleEntriesDetail(self.engine, parent)

    def checkPlayerScore(self, player, score, extras=None):
        try:
            if score < 0 or not extras:
                return False
            qwirkles = extras["qwirkles"]
            return score >= 12 * qwirkles
        except (KeyError, TypeError):
            return False


class QwirkleInputWidget(ScrabbleInputWidget):
    spacePressed = QtCore.Signal()

    def initUI(self):
        super().initUI()
        self.scoreSpinBox.setRange(-1, 84, 0)
        self.reset()

    def createBonusButtons(self):
        self.currentPlayerBoxLayout.insertSpacing(0, 64)
        for b, maxreps in self.engine.getBonuses().items():
            bb = BonusButton(
                b, maxreps, colour=None, size=64, parent=self.currentPlayerBox
            )
            self.bonusButtons[b] = bb
            self.currentPlayerBoxLayout.addWidget(bb)
            self.spacePressed.connect(bb.plusone)
            self.scoreSpinBox.spacePressed.connect(bb.plusone)
            bb.bonusChanged.connect(self.changed)


class QwirkleEntriesDetail(ScrabbleEntriesDetail):
    def createRoundTable(self, engine, parent=None):
        return QwirkleRoundTable(self.engine, parent)

    def createRoundPlot(self, engine, parent=None):
        return QwirkleEntriesPlot(self.engine, self)

    def createQSBox(self, parent=None):
        return QwirkleQSTW(self.engine.getGame(), self.engine.getListPlayers(), self)


class QwirkleRoundTable(ScrabbleRoundTable):
    pass


class QwirkleEntriesPlot(ScrabbleEntriesPlot):
    pass


class QwirkleQSTW(ScrabbleQSTW):
    def initStatsWidgets(self):
        self.gs = QwirkleQSBox(self.game, self)
        self.ps = QwirklePQSBox(self.game, self)


class QwirkleQSBox(GeneralQuickStats):
    def __init__(self, gname, parent=None):
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
    pass
