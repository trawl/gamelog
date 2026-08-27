from typing import cast

from PySide6 import QtCore
from PySide6.QtWidgets import (
    QGroupBox,
    QHBoxLayout,
    QMessageBox,
    QSizePolicy,
    QTableWidgetItem,
)

from controllers.scrabbleengine import ScrabbleEngine
from core.engine.settings import appsettings
from core.ui.game import (
    BonusButton,
    GameInputWidget,
    GameNotImplementedException,
    GameRoundPlot,
    GameRoundsDetail,
    GameRoundTable,
    GameWidget,
    PlayerColours,
    ScoreSpinBox,
)
from core.ui.gamestats import GeneralQuickStats, ParticularQuickStats, QuickStatsTW


class ScrabbleWidget(GameWidget):
    def createEngine(self):
        if self.game != "Scrabble":
            raise GameNotImplementedException(f"No engine for game {self.game}")
        self.engine = ScrabbleEngine()

    def initUI(self):
        super().initUI()
        self.dealerPolicyCheckBox.hide()

        cast(ScrabbleInputWidget, self.gameInput).placeCommitButton(
            self.commitRoundButton
        )
        cast(ScrabbleInputWidget, self.gameInput).placeUndoButton(self.undoButton)
        for b in (self.commitRoundButton, self.undoButton):
            b.setSizePolicy(
                QSizePolicy.Policy.MinimumExpanding, QSizePolicy.Policy.Preferred
            )
        self.retranslateUI()

    def createGameInputWidget(self, parent=None):  # pyright: ignore[reportIncompatibleMethodOverride]
        return ScrabbleInputWidget(self.engine, parent)

    def createRoundsDetail(self, parent=None):
        return ScrabbleEntriesDetail(self.engine, parent)

    # def retranslateUI(self):
    #     super().retranslateUI()
    #     # self.commitRoundButton.setText("▼")
    #     self.commitRoundButton.setText("↵")
    #     self.undoButton.setText("⎌")

    #     self.gameInput.retranslateUI()
    #     self.detailGroup.retranslateUI()

    def checkPlayerScore(self, player, score, extras=None):
        return bool(score)

    def commitRoundSanityCheck(self, interactive=False):
        gi = cast(ScrabbleInputWidget, self.gameInput)
        player = gi.getPlayer()
        bonuses = gi.getBonuses()
        score = gi.getScore()
        if player == "":
            msg = self.tr("You must select a player")
            if interactive:
                QMessageBox.warning(self, self.game, msg)
            else:
                print(f"[sanity] {msg}")
            return False

        if not self.checkPlayerScore(player, score, bonuses):
            msg = self.tr("{} score is not valid").format(player)
            if interactive:
                QMessageBox.warning(self, self.game, msg)
            else:
                print(f"[sanity] {msg}")
            return False
        return True

    def commitRound(self):
        if not self.commitRoundSanityCheck(interactive=True):
            return
        # Once here, we can commit round
        self.unsetDealer()
        gi = cast(ScrabbleInputWidget, self.gameInput)
        player = gi.getPlayer()
        bonuses = gi.getBonuses()
        score = gi.getScore()
        self.engine.addEntry(player, score, bonuses)
        self.engine.printStats()
        self.updatePanel()
        if not self.engine.getWinner():
            self.setDealer()
        elif self.hideInputOnFinish:
            self.gameInput.hide()

    def setDealer(self):
        super().setDealer()
        self.gameInput.reset()


class ScrabbleInputWidget(GameInputWidget):
    def __init__(self, engine, parent):
        self.active_player = engine.getDealer()
        super().__init__(engine, parent)

    def initUI(self):
        self.setStyleSheet("QGroupBox { font-size: 18px; font-weight: bold; }")
        self.widgetLayout = QHBoxLayout(self)
        self.currentPlayerBox = QGroupBox(self)
        self.widgetLayout.addWidget(self.currentPlayerBox, 2)
        self.currentPlayerBoxLayout = QHBoxLayout(self.currentPlayerBox)
        self.scoreSpinBox = ScoreSpinBox(self.currentPlayerBox)
        self.scoreSpinBox.setRange(-60, 400, 0)
        self.currentPlayerBoxLayout.addWidget(self.scoreSpinBox)
        self.scoreSpinBox.valueChanged.connect(self.changed)
        self.bonusButtons = {}
        self.createBonusButtons()
        self.reset()

    def createBonusButtons(self):
        for b, maxreps in self.engine.getBonuses().items():
            bb = BonusButton(
                b, maxreps, colour=None, size=32, parent=self.currentPlayerBox
            )
            self.bonusButtons[b] = bb
            self.currentPlayerBoxLayout.addWidget(bb)
            bb.bonusChanged.connect(self.changed)

    def retranslateUI(self):
        if appsettings["text_in_buttons"]:
            css = """
                QPushButton {
                    font-weight: normal;
                }
                """
        else:
            css = """
                QPushButton {
                    font-size: 48px;
                    font-weight: bold;
                }
                """
        self.commitButton.setStyleSheet(css)
        self.undoButton.setStyleSheet(css)

    def placeCommitButton(self, cb):
        # cb.setStyleSheet("""
        #     QPushButton {
        #         font-size: 48px;
        #         font-weight: bold;
        #     }
        #     """)
        self.commitButton = cb
        self.widgetLayout.addWidget(cb, 1)

    def placeUndoButton(self, ub):
        # ub.setStyleSheet("""
        #     QPushButton {
        #         font-size: 48px;
        #         font-weight: bold;
        #     }
        #     """)
        self.undoButton = ub
        self.widgetLayout.insertWidget(0, ub, 1)

    def getPlayer(self):
        return self.active_player

    def getBonuses(self):
        return {b: bb.getValue() for b, bb in self.bonusButtons.items()}

    def getScore(self):
        return self.scoreSpinBox.value()

    def setColour(self, colour):
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
        self.currentPlayerBox.setStyleSheet(
            css.format(colour.red(), colour.green(), colour.blue())
        )
        self.scoreSpinBox.setColour(colour)
        for bb in self.bonusButtons.values():
            bb.setColour(colour)

    def reset(self):
        self.active_player = self.engine.getDealer()
        self.setColour(
            PlayerColours[self.engine.getListPlayers().index(self.active_player)]
        )
        self.currentPlayerBox.setTitle(f"{self.active_player}")
        self.scoreSpinBox.reset()
        for bb in self.bonusButtons.values():
            bb.setChecked(False)
        self.scoreSpinBox.setFocus()

    def updatePlayerOrder(self):
        self.reset()

    # def keyPressEvent(self, event):
    #     if event.key() == QtCore.Qt.Key.Key_Return:
    #         self.enterPressed.emit()
    #         event.accept()
    #     return super().keyPressEvent(event)


class ScrabbleEntriesDetail(GameRoundsDetail):
    def __init__(self, engine, parent=None):
        super().__init__(engine, parent)
        self.setCurrentWidget(self.plot)

    def createRoundTable(self, engine, parent=None):
        return ScrabbleRoundTable(self.engine, parent)

    def createRoundPlot(self, engine, parent=None):
        return ScrabbleEntriesPlot(self.engine, self)

    def createQSBox(self, parent=None):
        return ScrabbleQSTW(self.engine.getGame(), self.engine.getListPlayers(), self)


class ScrabbleRoundTable(GameRoundTable):
    def insertRound(self, entry):
        players = self.engine.getListPlayers()
        i = (entry.getNumRound() - 1) // len(players)
        j = players.index(entry.getPlayer())
        if self.rowCount() <= i:
            self.insertRow(i)
            for col, _ in enumerate(self.engine.getListPlayers()):
                item = QTableWidgetItem()
                item.setFlags(item.flags() ^ QtCore.Qt.ItemFlag.ItemIsEditable)
                item.setTextAlignment(
                    QtCore.Qt.AlignmentFlag.AlignVCenter
                    | QtCore.Qt.AlignmentFlag.AlignCenter
                )
                item.setText("")
                self.setItem(i, col, item)

        item = self.item(i, j)
        if item:
            text = "{} {}".format(
                entry.getPlayerScore(), "*" * sum(entry.getBonuses().values())
            )
            if entry.getBonuses():
                font = item.font()
                font.setBold(True)
                item.setFont(font)
            item.setText(text)
        self.scrollToBottom()

    def openTableMenu(self, position):
        # Use Undo to remove
        return
        # players = self.engine.getListPlayers()
        # index = self.indexAt(position)
        # item = self.itemAt(position)
        # nentry = (index.row()) * len(players) + index.column()
        # print(f"right click on nentry {nentry}")
        # if nentry <= 0 or self.engine.getWinner():
        #     return

        # menu = QMenu()
        # ic = QtGui.QIcon(":/icons/delete.png")
        # msg = self.tr("Delete Entry")
        # deleteEntryAction = QAction(ic, msg, self)
        # menu.addAction(deleteEntryAction)
        # action = menu.exec_(self.mapToGlobal(position))
        # if action == deleteEntryAction:
        #     title = self.tr("Delete Entry")
        #     msg = self.tr("Are you sure you want to delete this entry?")
        #     ret = QMessageBox.question(
        #         self,
        #         title,
        #         msg,
        #         QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        #         QMessageBox.StandardButton.Yes,
        #     )
        #     if ret == QMessageBox.StandardButton.No:
        #         return
        #     self.engine.deleteRound(nentry)
        #     if item:
        #         item.setText("")
        #     self.edited.emit()


class ScrabbleEntriesPlot(GameRoundPlot):
    def updatePlot(self):
        if not self.isPlotInited():
            return
        super().updatePlot()
        scores = {}
        for player in self.engine.getPlayers():
            scores[player] = [0]

        for entry in self.engine.getRounds():
            for player in self.engine.getPlayers():
                if player == entry.getPlayer():
                    entryscore = entry.getPlayerScore()
                    accumscore = scores[player][-1] + entryscore
                    scores[player].append(accumscore)

        # Temporary pad for other players:
        max_len = max(len(series) for series in scores.values())
        for series in scores.values():
            series.extend([series[-1]] * (max_len - len(series)))

        self.canvas.clearPlotContents()

        for player in self.engine.getListPlayers():
            self.canvas.addSeries(scores[player], player)

        self.canvas._scene.update()


class ScrabbleQSTW(QuickStatsTW):
    def initStatsWidgets(self):
        self.gs = ScrabbleQSBox(self.game, self)
        self.ps = ScrabblePQSBox(self.game, self)


class ScrabbleQSBox(GeneralQuickStats):
    def __init__(self, gname, parent=None):
        super().__init__(gname, parent)
        self.playerStatsKeys.append("max_round_score")
        self.playerStatsHeaders.append(self.tr("Best Play"))
        self.playerStatsKeys.append("max_bonuses")
        self.playerStatsHeaders.append(self.tr("Max Bonus"))
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


class ScrabblePQSBox(ScrabbleQSBox, ParticularQuickStats):
    pass
