from PySide6 import QtCore

from controllers.qwirkleengine import QwirkleEngine
from gui.game import (
    BonusButton,
    GameNotImplementedException,
    GameRoundsDetail,
)
from gui.gamestats import GeneralQuickStats, ParticularQuickStats, QuickStatsTW
from gui.scrabble import (
    ScrabbleEntriesPlot,
    ScrabbleInputWidget,
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

    def checkPlayerScore(self, player, score, extras=None):
        try:
            if score < 0 or not extras:
                return False
            qwirkles = extras["qwirkles"]
            return score >= 12 * qwirkles
        except (KeyError, TypeError):
            return False


class QwirkleInputWidget(ScrabbleInputWidget):
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

    def keyPressEvent(self, event):
        if event.key() == QtCore.Qt.Key.Key_Space:
            self.spacePressed.emit()
            event.accept()
        return super().keyPressEvent(event)


class QwirkleEntriesDetail(GameRoundsDetail):
    def __init__(self, engine, parent=None):
        super().__init__(engine, parent)

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


class QwirkleQSTW(QuickStatsTW):
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
