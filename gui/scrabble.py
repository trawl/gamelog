from PySide6 import QtCore, QtGui
from PySide6.QtGui import QShortcut
from PySide6.QtWidgets import (
    QGroupBox,
    QHBoxLayout,
    QMessageBox,
    QPushButton,
    QSizePolicy,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from controllers.scrabbleengine import ScrabbleEngine
from gui.game import (
    BonusButton,
    GameNotImplementedException,
    GamePlayerWidget,
    GameRoundPlot,
    GameRoundsDetail,
    GameRoundTable,
    GameWidget,
    PlayerColours,
    ScoreSpinBox,
)
from gui.gamestats import GeneralQuickStats, ParticularQuickStats, QuickStatsTW


class ScrabbleWidget(GameWidget):
    def createEngine(self):
        if self.game != "Scrabble":
            raise GameNotImplementedException(f"No engine for game {self.game}")
        self.engine = ScrabbleEngine()

    def initUI(self):
        super().initUI()
        # self.roundTitleLabel.hide()
        self.dealerPolicyCheckBox.hide()
        self.finishButton = QPushButton(self.roundGroup)
        self.buttonGroupLayout.insertWidget(
            self.buttonGroupLayout.count() - 1, self.finishButton
        )
        self.finishButton.clicked.connect(self.finish)

        if not self.gameInput:
            self.gameInput = self.createGameInputWidget(self)
        self.gameInput.enterPressed.connect(self.commitRound)
        self.gameInput.scoreChanged.connect(self.guardCommitButton)
        self._commit_round_connection = False
        self.guardCommitButton()
        self.focussc = QShortcut(
            QtGui.QKeySequence("Ctrl+A"), self, self.gameInput.setFocus
        )
        self.roundLayout.addWidget(self.gameInput)

        self.undoButton = QPushButton(self)
        self.undoButton.pressed.connect(self.undoCommit)
        self.undoButton.setEnabled(self.engine.getNumRound() > 1)
        self.undoButton.setSizePolicy(
            QSizePolicy.Policy.MinimumExpanding, QSizePolicy.Policy.Preferred
        )
        self.gameInput.placeCommitButton(self.commitRoundButton)
        self.gameInput.placeUndoButton(self.undoButton)
        self.commitRoundButton.setSizePolicy(
            QSizePolicy.Policy.MinimumExpanding, QSizePolicy.Policy.Preferred
        )

        self.detailGroup = ScrabbleEntriesDetail(self.engine, self)
        # self.widgetLayout.addWidget(self.detailGroup, 1, 0)
        self.leftLayout.addWidget(self.detailGroup)
        self.detailGroup.edited.connect(self.updatePanel)

        self.playersLayout = QVBoxLayout()
        self.matchGroupLayout.addLayout(self.playersLayout)
        # self.playersLayout.addStretch()
        self.playerGroupBox = {}
        dealer = self.engine.getDealer()
        for i, player in enumerate(self.engine.getListPlayers()):
            pw = GamePlayerWidget(player, PlayerColours[i], self.matchGroup)
            if player == dealer:
                pw.setDealer()
            pw.updateDisplay(self.engine.getScoreFromPlayer(player))
            self.playersLayout.addWidget(pw)
            self.playerGroupBox[player] = pw

        # self.playersLayout.addStretch()
        self.retranslateUI()
        QtCore.QTimer.singleShot(1000, self.gameInput.setFocus)

    def createGameInputWidget(self, parent=None):  # pyright: ignore[reportIncompatibleMethodOverride]
        return ScrabbleInputWidget(self.engine, parent)

    def retranslateUI(self):
        super().retranslateUI()
        self.commitRoundButton.setText("▼")
        self.undoButton.setText("⎌")
        self.finishButton.setText(self.tr("&Finish Game"))
        self.gameInput.retranslateUI()
        self.detailGroup.retranslateUI()

    def setRoundTitle(self):
        game = self.engine.getGame()
        if game is None:
            game = ""
        self.roundTitleLabel.setText(game)

    def updatePanel(self):
        super().updatePanel()
        self.updateScores()
        if self.engine.getWinner():
            self.finishButton.setDisabled(True)
            self.gameInput.hide()
            self.detailGroup.updateStats()
        else:
            self.detailGroup.updateRound()
        self.undoButton.setEnabled(self.engine.getNumRound() > 1)
        self.guardCommitButton()

    def checkPlayerScore(self, player, score, extras=None):
        return bool(score)

    def guardCommitButton(self):
        player = self.gameInput.getPlayer()
        bonuses = self.gameInput.getBonuses()
        score = self.gameInput.getScore()
        if not self.checkPlayerScore(player, score, bonuses):
            self.commitRoundButton.setDisabled(True)
            if self._commit_round_connection:
                self.gameInput.enterPressed.disconnect(self.commitRound)
                self._commit_round_connection = False

        else:
            self.commitRoundButton.setDisabled(False)
            self.gameInput.enterPressed.connect(self.commitRound)
            self._commit_round_connection = True

    def commitRound(self):
        player = self.gameInput.getPlayer()
        bonuses = self.gameInput.getBonuses()
        score = self.gameInput.getScore()
        if player == "":
            msg = self.tr("You must select a player")
            QMessageBox.warning(self, self.game, msg)
            return

        if not self.checkPlayerScore(player, score, bonuses):
            msg = self.tr("{} score is not valid").format(player)
            QMessageBox.warning(self, self.game, msg)
            return

        # Once here, we can commit round
        self.unsetDealer()
        self.engine.addEntry(player, score, bonuses)
        self.engine.printStats()
        self.updatePanel()
        if not self.engine.getWinner():
            self.setDealer()
        elif self.hideInputOnFinish:
            self.gameInput.hide()

    def undoCommit(self):
        try:
            last_entry = self.engine.getRounds()[-1]
        except IndexError:
            return

        title = self.tr("Delete Entry")
        msg = self.tr(
            "Are you sure you want to delete the last entry for {} ({})?"
        ).format(last_entry.getPlayer(), last_entry.getScore()[last_entry.getPlayer()])
        ret = QMessageBox.question(
            self,
            title,
            msg,
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.Yes,
        )
        if ret == QMessageBox.StandardButton.No:
            return
        self.unsetDealer()
        self.engine.deleteRound(len(self.engine.getRounds()))
        self.updatePanel()
        self.setDealer()

    def finish(self):
        title = self.tr("Finish game")
        msg = self.tr("Are you sure you want to finish the current game?")
        ret = QMessageBox.question(
            self,
            title,
            msg,
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.Yes,
        )

        if ret == QMessageBox.StandardButton.No:
            return
        self.engine.finishGame()
        self.updatePanel()

    def updateScores(self):
        for player in self.players:
            score = self.engine.getScoreFromPlayer(player)
            self.playerGroupBox[player].updateDisplay(score)

    def setWinner(self):
        super().setWinner()
        winner = self.engine.getWinner()
        if winner in self.players:
            self.playerGroupBox[winner].setWinner()

    def unsetDealer(self):
        self.playerGroupBox[self.engine.getDealer()].unsetDealer()

    def setDealer(self):
        self.playerGroupBox[self.engine.getDealer()].setDealer()
        self.gameInput.reset()

    def updatePlayerOrder(self):
        GameWidget.updatePlayerOrder(self)
        # self.playersLayout.addStretch()
        for i, player in enumerate(self.engine.getListPlayers()):
            self.playersLayout.removeWidget(self.playerGroupBox[player])
            self.playersLayout.addWidget(self.playerGroupBox[player])
            self.playerGroupBox[player].setColour(PlayerColours[i])
        # self.playersLayout.addStretch()
        self.detailGroup.updateRound()


class ScrabbleInputWidget(QWidget):
    enterPressed = QtCore.Signal()
    spacePressed = QtCore.Signal()
    scoreChanged = QtCore.Signal()

    def __init__(self, engine, parent):
        super().__init__(parent)
        self.engine = engine
        self.parent = parent
        self.active_player = self.engine.getDealer()
        self.setStyleSheet("QGroupBox { font-size: 18px; font-weight: bold; }")
        self.initUI()

    def initUI(self):
        self.widgetLayout = QHBoxLayout(self)
        self.currentPlayerBox = QGroupBox(self)
        self.widgetLayout.addWidget(self.currentPlayerBox, 2)
        self.currentPlayerBoxLayout = QHBoxLayout(self.currentPlayerBox)
        self.scoreSpinBox = ScoreSpinBox(self.currentPlayerBox)
        self.scoreSpinBox.setRange(-60, 400, 0)
        self.currentPlayerBoxLayout.addWidget(self.scoreSpinBox)
        self.scoreSpinBox.valueChanged.connect(self.scoreChanged)
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
            bb.bonusChanged.connect(self.scoreChanged)

    def retranslateUI(self):
        pass

    def placeCommitButton(self, cb):
        cb.setStyleSheet("""
            QPushButton {
                font-size: 48px;
                font-weight: bold;
            }
            """)
        self.widgetLayout.addWidget(cb, 1)

    def placeUndoButton(self, ub):
        ub.setStyleSheet("""
            QPushButton {
                font-size: 48px;
                font-weight: bold;
            }
            """)
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

    def keyPressEvent(self, event):
        if event.key() == QtCore.Qt.Key.Key_Return:
            self.enterPressed.emit()
            event.accept()
        return super().keyPressEvent(event)


class ScrabbleEntriesDetail(GameRoundsDetail):
    def __init__(self, engine, parent=None):
        super().__init__(engine, parent)
        self.container.setCurrentWidget(self.plot)

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
