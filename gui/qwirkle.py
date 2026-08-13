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

from controllers.qwirkleengine import QwirkleEngine
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


class QwirkleWidget(GameWidget):
    def createEngine(self):
        if self.game != "Qwirkle":
            raise GameNotImplementedException(f"No engine for game {self.game}")
        self.engine = QwirkleEngine()

    def initUI(self):
        super().initUI()
        # self.roundTitleLabel.hide()
        self.dealerPolicyCheckBox.hide()
        self.finishButton = QPushButton(self.roundGroup)
        self.buttonGroupLayout.insertWidget(
            self.buttonGroupLayout.count() - 1, self.finishButton
        )
        self.finishButton.clicked.connect(self.finish)

        self.gameInput = QwirkleInputWidget(self.engine, self)
        self.gameInput.enterPressed.connect(self.commitRound)
        self.focussc = QShortcut(
            QtGui.QKeySequence("Ctrl+A"), self, self.gameInput.setFocus
        )
        self.roundLayout.addWidget(self.gameInput)

        self.undoButton = QPushButton(self)
        self.undoButton.pressed.connect(self.undoCommit)
        self.undoButton.setEnabled(False)
        self.undoButton.setSizePolicy(
            QSizePolicy.Policy.MinimumExpanding, QSizePolicy.Policy.Preferred
        )
        self.gameInput.placeCommitButton(self.commitRoundButton)
        self.gameInput.placeUndoButton(self.undoButton)
        self.commitRoundButton.setSizePolicy(
            QSizePolicy.Policy.MinimumExpanding, QSizePolicy.Policy.Preferred
        )

        self.detailGroup = QwirkleEntriesDetail(self.engine, self)
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

            if self.engine.getNumRound() == 1 and player == dealer:
                pw.setDealer()
            pw.updateDisplay(self.engine.getScoreFromPlayer(player))
            self.playersLayout.addWidget(pw)
            self.playerGroupBox[player] = pw

        # self.playersLayout.addStretch()
        self.retranslateUI()
        QtCore.QTimer.singleShot(1000, self.gameInput.setFocus)

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

    def checkPlayerScore(self, player, score, extras=None):
        try:
            if score < 0 or not extras:
                return False
            qwirkles = extras["qwirkles"]
            return score >= 12 * qwirkles
        except (KeyError, TypeError):
            return False

    def commitRound(self):
        player = self.gameInput.getPlayer()
        qwirkles = self.gameInput.getQwirkles()
        score = self.gameInput.getScore()
        if player == "":
            msg = self.tr("You must select a player")
            QMessageBox.warning(self, self.game, msg)
            return

        if not self.checkPlayerScore(player, score, {"qwirkles": qwirkles}):
            msg = self.tr("{} score is not valid").format(player)
            QMessageBox.warning(self, self.game, msg)
            return

        # Once here, we can commit round
        self.unsetDealer()
        self.engine.addEntry(player, score, {"qwirkles": qwirkles})
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
        self.engine.deleteRound(len(self.engine.getRounds()) - 1)
        self.engine.printStats()
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

    def updatePlayerOrder(self):
        GameWidget.updatePlayerOrder(self)
        # self.playersLayout.addStretch()
        for player in self.engine.getListPlayers():
            self.playersLayout.removeWidget(self.playerGroupBox[player])

        for i, player in enumerate(self.engine.getListPlayers()):
            self.playersLayout.addWidget(self.playerGroupBox[player])
            self.playerGroupBox[player].setColour(PlayerColours[i])
        # self.playersLayout.addStretch()
        self.detailGroup.updateRound()


class QwirkleInputWidget(QWidget):
    enterPressed = QtCore.Signal()
    spacePressed = QtCore.Signal()

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
        self.currentPlayerBoxLayout.addSpacing(64)
        self.scoreSpinBox = ScoreSpinBox(self.currentPlayerBox)
        self.scoreSpinBox.setRange(-1, 84)
        self.currentPlayerBoxLayout.addWidget(self.scoreSpinBox)
        self.qwirkleBonusButton = BonusButton(
            "qwirkle", 6, colour=None, size=64, parent=self.currentPlayerBox
        )
        self.currentPlayerBoxLayout.addWidget(self.qwirkleBonusButton)
        self.spacePressed.connect(self.qwirkleBonusButton.plusone)
        self.scoreSpinBox.spacePressed.connect(self.qwirkleBonusButton.plusone)
        self.reset()

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

    def getQwirkles(self):
        return self.qwirkleBonusButton.getValue()

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
        self.qwirkleBonusButton.setColour(colour)

    def reset(self):
        self.active_player = self.engine.getDealer()
        self.setColour(
            PlayerColours[self.engine.getListPlayers().index(self.active_player)]
        )
        self.currentPlayerBox.setTitle(f"{self.active_player}")
        self.scoreSpinBox.setValue(-1)
        self.qwirkleBonusButton.setChecked(False)
        self.scoreSpinBox.setFocus()

    def updatePlayerOrder(self):
        self.reset()

    def keyPressEvent(self, event):
        if event.key() == QtCore.Qt.Key.Key_Return:
            self.enterPressed.emit()
            event.accept()
        if event.key() == QtCore.Qt.Key.Key_Space:
            self.spacePressed.emit()
            event.accept()
        return super().keyPressEvent(event)


class QwirkleEntriesDetail(GameRoundsDetail):
    def __init__(self, engine, parent=None):
        super().__init__(engine, parent)
        self.container.setCurrentWidget(self.plot)

    def createRoundTable(self, engine, parent=None):
        return QwirkleRoundTable(self.engine, parent)

    def createRoundPlot(self, engine, parent=None):
        return QwirkleEntriesPlot(self.engine, self)

    def createQSBox(self, parent=None):
        return QwirkleQSTW(self.engine.getGame(), self.engine.getListPlayers(), self)


class QwirkleRoundTable(GameRoundTable):
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
            text = "{} {}".format(entry.getPlayerScore(), "*" * entry.getQwirkles())
            if entry.getQwirkles():
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


class QwirkleEntriesPlot(GameRoundPlot):
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
