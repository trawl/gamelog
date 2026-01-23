#!/usr/bin/env python
# -*- coding: utf-8 -*-

from typing import cast

from PySide6 import QtCore, QtGui
from PySide6.QtCore import QCoreApplication
from PySide6.QtGui import QShortcut
from PySide6.QtWidgets import (
    QButtonGroup,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QRadioButton,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from controllers.carcassonneengine import CarcassonneEngine, CarcassonneStatsEngine
from gui.game import (
    GamePlayerWidget,
    GameRoundPlot,
    GameRoundsDetail,
    GameRoundTable,
    GameWidget,
    PlayerColours,
    QuickStatsTW,
    ScoreSpinBox,
)
from gui.gamestats import GeneralQuickStats, ParticularQuickStats, StatsTable


class CarcassonneWidget(GameWidget):
    bgcolors = [0xFFCC99, 0xCCCCCC, 0xFFFF99, 0xCCFF99, 0xCCFFCC, 0xFFB6C1]

    def createEngine(self):
        if self.game != "Carcassonne":
            raise Exception("No engine for game {}".format(self.game))
        self.engine = CarcassonneEngine()

    def initUI(self):
        super(CarcassonneWidget, self).initUI()
        # self.roundTitleLabel.hide()
        self.finishButton = QPushButton(self.roundGroup)
        self.buttonGroupLayout.insertWidget(
            self.buttonGroupLayout.count() - 1, self.finishButton
        )
        self.finishButton.clicked.connect(self.finish)

        self.gameInput = CarcassonneInputWidget(self.engine, self.bgcolors, self)
        self.gameInput.enterPressed.connect(self.commitRound)
        self.focussc = QShortcut(
            QtGui.QKeySequence("Ctrl+A"), self, self.gameInput.setFocus
        )
        self.roundLayout.addWidget(self.gameInput)

        self.gameInput.placeCommitButton(self.commitRoundButton)

        self.detailGroup = CarcassonneEntriesDetail(self.engine, self.bgcolors, self)
        # self.widgetLayout.addWidget(self.detailGroup, 1, 0)
        self.leftLayout.addWidget(self.detailGroup)
        self.detailGroup.edited.connect(self.updatePanel)

        # self.playerGroup = QGroupBox(self)
        # # self.widgetLayout.addWidget(self.playerGroup, 1, 1)
        # self.rightLayout.addWidget(self.playerGroup)

        # self.playerGroup.setStyleSheet(
        #     "QGroupBox { font-size: 18px; font-weight: bold; }"
        # )
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
        super(CarcassonneWidget, self).retranslateUI()
        self.finishButton.setText(self.tr("&Finish Game"))
        self.gameInput.retranslateUI()
        self.detailGroup.retranslateUI()

    def setRoundTitle(self):
        game = self.engine.getGame()
        if game is None:
            game = ""
        self.roundTitleLabel.setText(game)

    def getPlayerExtraInfo(self, player):
        kind = self.gameInput.getKind()
        if kind:
            return {"kind": kind}
        else:
            return {}

    def updatePanel(self):
        super(CarcassonneWidget, self).updatePanel()
        self.updateScores()
        if self.engine.getWinner():
            self.finishButton.setDisabled(True)
            self.gameInput.hide()
            self.detailGroup.updateStats()
        else:
            self.detailGroup.updateRound()

    def checkPlayerScore(self, player, score):
        if score > 0:
            return True
        else:
            return False

    def commitRound(self):
        player = self.gameInput.getPlayer()
        kind = self.gameInput.getKind()
        score = self.gameInput.getScore()
        if player == "":
            msg = self.tr("You must select a player")
            QMessageBox.warning(self, self.game, msg)
            return

        if kind == "":
            msg = self.tr("You must select a kind")
            QMessageBox.warning(self, self.game, msg)
            return

        if not self.checkPlayerScore(player, score):
            msg = self.tr(f"{player} score is not valid")
            QMessageBox.warning(self, self.game, msg)
            return

        # Everything ok so far, let's confirm
        # title = i18n(
        #     "CarcassonneWidget", 'Commit Entry')
        # msg = i18n(
        #     "CarcassonneWidget", "Are you sure you want to commit this entry?")

        # ret = QMessageBox.question(self, title, msg,
        #                            QMessageBox.Yes | QMessageBox.No,
        #                            QMessageBox.Yes)

        # if ret == QMessageBox.No:
        #     return

        # Once here, we can commit round
        try:
            self.playerGroupBox[self.engine.getDealer()].unsetDealer()
        except KeyError:
            pass
        self.engine.addEntry(player, score, {"kind": kind})
        self.engine.printStats()

        self.updatePanel()

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
        super(CarcassonneWidget, self).setWinner()
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


class CarcassonneInputWidget(QWidget):
    enterPressed = QtCore.Signal()

    QCoreApplication.translate("CarcassonneInputWidget", "City")
    QCoreApplication.translate("CarcassonneInputWidget", "Road")
    QCoreApplication.translate("CarcassonneInputWidget", "Cloister")
    QCoreApplication.translate("CarcassonneInputWidget", "Field")
    QCoreApplication.translate("CarcassonneInputWidget", "Goods")
    QCoreApplication.translate("CarcassonneInputWidget", "Fair")

    def __init__(self, engine, bgcolors, parent):
        super(CarcassonneInputWidget, self).__init__(parent)
        self.engine = engine
        self.parent = parent
        self.bgcolors = bgcolors
        self.setStyleSheet("QGroupBox { font-size: 18px; font-weight: bold; }")
        self.initUI()

    def initUI(self):
        self.widgetLayout = QHBoxLayout(self)
        self.playerGroup = QGroupBox(self)
        self.widgetLayout.addWidget(self.playerGroup)
        self.playerButtonGroup = QButtonGroup(self)
        self.playerGroupLayout = QGridLayout(self.playerGroup)

        b = QRadioButton("", self.playerGroup)
        #        self.playerGroupLayout.addWidget(b)
        self.playerButtonGroup.addButton(b, 0)
        self.playerButtons = [b]
        b.hide()
        for i, player in enumerate(self.engine.getListPlayers(), 1):
            b = QRadioButton("{}. {}".format(i, player), self.playerGroup)
            if len(self.engine.getListPlayers()) > 2:
                self.playerGroupLayout.addWidget(b, (i - 1) % 2, (i - 1) // 2)
            else:
                self.playerGroupLayout.addWidget(b, 0, (i - 1) % 2)
            self.playerButtonGroup.addButton(b, i)
            self.playerButtons.append(b)

        self.kindGroup = QGroupBox(self)
        self.widgetLayout.addWidget(self.kindGroup)
        self.kindButtonGroup = QButtonGroup(self)
        self.kindGroupLayout = QGridLayout(self.kindGroup)

        b = QRadioButton("", self.kindGroup)
        #        self.kindGroupLayout.addWidget(b)
        self.kindButtonGroup.addButton(b, 0)
        self.kindButtons = [b]
        b.hide()

        self.scoreSpinBox = ScoreSpinBox(self)
        # self.scoreSpinBox.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        # self.scoreSpinBox.setMaximumWidth(120)
        self.scoreSpinBox.setRange(0, 300)

        for i, kind in enumerate(self.engine.getEntryKinds(), 1):
            lbl = self.tr(kind)
            b = QRadioButton("{}. {}".format(i, lbl), self.kindGroup)
            self.kindGroupLayout.addWidget(b, (i - 1) % 2, (i - 1) // 2)
            self.kindButtonGroup.addButton(b, i)
            b.clicked.connect(lambda x: self.scoreSpinBox.setFocus())
            self.kindButtons.append(b)

        self.kindButtons[3].toggled.connect(self.setCloisterPoints)
        self.kindButtons[5].toggled.connect(self.setGoodsPoints)
        self.kindButtons[6].toggled.connect(self.setFairPoints)

        self.scoreGroup = QGroupBox(self)
        self.widgetLayout.addWidget(self.scoreGroup)
        self.scoreGroupLayout = QHBoxLayout(self.scoreGroup)

        self.scoreGroupLayout.addWidget(self.scoreSpinBox)

        self.reset()
        self.retranslateUI()

    def retranslateUI(self):
        self.playerGroup.setTitle(self.tr("Select Player"))
        self.kindGroup.setTitle(self.tr("Select kind of entry"))
        self.scoreGroup.setTitle(self.tr("Points"))
        for i, kind in enumerate(self.engine.getEntryKinds(), 1):
            text = self.tr(kind)
            self.kindButtons[i].setText("{}. {}".format(i, text))

    def placeCommitButton(self, cb):
        self.scoreGroupLayout.addWidget(cb)

    def getPlayer(self):
        pid = self.playerButtonGroup.checkedId()
        if not pid:
            return ""
        player = self.engine.getListPlayers()[pid - 1]
        return str(player)

    def getKind(self):
        cid = self.kindButtonGroup.checkedId()
        if not cid:
            return ""
        kind = self.engine.getEntryKinds()[cid - 1]
        return str(kind)

    def getScore(self):
        return self.scoreSpinBox.value()

    def reset(self):
        self.playerButtons[0].setChecked(True)
        self.kindButtons[0].setChecked(True)
        self.scoreSpinBox.setValue(0)
        self.setFocus()

    def keyPressEvent(self, event):
        numberkeys = [
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
        try:
            number = numberkeys.index(event.key()) + 1
        except ValueError:
            number = 0
        if event.key() == QtCore.Qt.Key.Key_Return:
            self.enterPressed.emit()
        elif number:
            if not self.getPlayer():
                if number <= len(self.engine.getPlayers()):
                    self.playerButtons[number].setChecked(True)
            elif not self.getKind():
                if number <= len(self.engine.getEntryKinds()):
                    self.kindButtons[number].setChecked(True)
                    self.scoreSpinBox.setFocus()

        return super(CarcassonneInputWidget, self).keyPressEvent(event)

    def setCloisterPoints(self, doit):
        if doit:
            self.scoreSpinBox.setValue(9)
            self.scoreSpinBox.setMaximum(9)
            # self.scoreSpinBox.lineEdit().selectAll()
        else:
            self.scoreSpinBox.setValue(0)
            self.scoreSpinBox.setMaximum(300)

    def setGoodsPoints(self, doit):
        if doit:
            self.scoreSpinBox.setValue(10)
            self.scoreSpinBox.setReadOnly(True)

        else:
            self.scoreSpinBox.setReadOnly(False)
            self.scoreSpinBox.setValue(0)

    def setFairPoints(self, doit):
        if doit:
            self.scoreSpinBox.setValue(5)
            self.scoreSpinBox.setReadOnly(True)

        else:
            self.scoreSpinBox.setReadOnly(False)
            self.scoreSpinBox.setValue(0)

    def updatePlayerOrder(self):
        trash = QWidget()
        trash.setLayout(self.playerGroupLayout)

        self.playerButtonGroup = QButtonGroup(self)
        self.playerGroupLayout = QGridLayout(self.playerGroup)
        b = QRadioButton("", self.playerGroup)
        self.playerButtonGroup.addButton(b, 0)
        self.playerButtons = [b]
        b.hide()

        for i, player in enumerate(self.engine.getListPlayers(), 1):
            b = QRadioButton("{}. {}".format(i, player), self.playerGroup)
            if len(self.engine.getListPlayers()) > 2:
                self.playerGroupLayout.addWidget(b, (i - 1) % 2, (i - 1) // 2)
            else:
                self.playerGroupLayout.addWidget(b, 0, (i - 1) % 2)
            self.playerButtonGroup.addButton(b, i)
            self.playerButtons.append(b)

        self.reset()


class CarcassonneEntriesDetail(GameRoundsDetail):
    def __init__(self, engine, bgcolors, parent=None):
        self.bgcolors = bgcolors
        super(CarcassonneEntriesDetail, self).__init__(engine, parent)
        self.setStyleSheet("""
            QTableView::item:hover {
                background: transparent;
            }
            QTableView::item:selected {
                background: transparent;
            }
        """)

    def initUI(self):
        super(CarcassonneEntriesDetail, self).initUI()
        self.totalsLabel = QLabel("", self)
        self.tableContainerLayout.addWidget(self.totalsLabel)
        self.totals = StatsTable(
            len(self.engine.getEntryKinds()), len(self.engine.getPlayers())
        )
        self.tableContainerLayout.addWidget(self.totals)
        self.totals.setHorizontalHeaderLabels(self.engine.getListPlayers())
        self.totals.setMaximumHeight(self.totals.sizeHint().height())

    def retranslateUI(self):
        self.totals.setVerticalHeaderLabels(
            [
                QCoreApplication.translate("CarcassonneInputWidget", kind)
                for kind in self.engine.getEntryKinds()
            ]
        )
        self.totalsLabel.setText(self.tr("Totals"))
        super(CarcassonneEntriesDetail, self).retranslateUI()
        self.updateRound()

    def resetTotals(self):
        self.totals.setHorizontalHeaderLabels(self.engine.getListPlayers())
        self.totals.clearContents()
        for row in range(len(self.engine.getEntryKinds())):
            background = self.bgcolors[row]
            for col in range(len(self.engine.getListPlayers())):
                item = QTableWidgetItem()
                item.setFlags(item.flags() ^ QtCore.Qt.ItemFlag.ItemIsEditable)
                item.setTextAlignment(
                    QtCore.Qt.AlignmentFlag.AlignVCenter
                    | QtCore.Qt.AlignmentFlag.AlignCenter
                )
                item.setBackground(QtGui.QBrush(QtGui.QColor(background)))
                item.setForeground(QtGui.QBrush(QtGui.QColor(0, 0, 0)))
                item.setText("0")
                self.totals.setItem(row, col, item)

    def updateRound(self):
        super(CarcassonneEntriesDetail, self).updateRound()
        self.resetTotals()
        for r in self.engine.getRounds():
            self.updateTotal(r)
        self.recomputeMaxTotals()

    def updateTotal(self, entry):
        kinds = self.engine.getEntryKinds()
        players = self.engine.getListPlayers()
        totalItem = self.totals.item(
            kinds.index(entry.getKind()), players.index(entry.getPlayer())
        )
        if totalItem:
            totalItem.setText(str(int(totalItem.text()) + entry.getPlayerScore()))

    def recomputeMaxTotals(self):
        kinds = self.engine.getEntryKinds()
        players = self.engine.getListPlayers()
        for row in range(len(kinds)):
            maxvalue = 1
            for col in range(len(players)):
                item = self.totals.item(row, col)
                if item:
                    total = int(item.text())
                    if total > maxvalue:
                        maxvalue = total

            for col in range(len(players)):
                item = self.totals.item(row, col)
                if item:
                    font = item.font()
                    font.setBold(int(item.text()) == maxvalue)
                    item.setFont(font)

    def createRoundTable(self, engine, parent=None):
        return CarcassonneRoundTable(self.engine, self.bgcolors, parent)

    def createRoundPlot(self, engine, parent=None):
        return CarcassonneEntriesPlot(self.engine, self)

    def createQSBox(self, parent=None):
        return CarcassonneQSTW(
            self.engine.getGame(), self.engine.getListPlayers(), self
        )


class CarcassonneRoundTable(GameRoundTable):
    def __init__(self, engine, bgcolors, parent=None):
        self.bgcolors = bgcolors
        super(CarcassonneRoundTable, self).__init__(engine, parent)

    def insertRound(self, entry):
        kind = entry.getKind()
        kinds = self.engine.getEntryKinds()
        background = self.bgcolors[kinds.index(kind)]
        kind = QCoreApplication.translate("CarcassonneInputWidget", kind)
        i = entry.getNumRound() - 1
        self.insertRow(i)
        for j, player in enumerate(self.engine.getListPlayers()):
            item = QTableWidgetItem()
            item.setFlags(item.flags() ^ QtCore.Qt.ItemFlag.ItemIsEditable)
            item.setTextAlignment(
                QtCore.Qt.AlignmentFlag.AlignVCenter
                | QtCore.Qt.AlignmentFlag.AlignCenter
            )
            item.setBackground(QtGui.QBrush(QtGui.QColor(background)))
            item.setForeground(QtGui.QBrush(QtGui.QColor(0, 0, 0)))

            if player == entry.getPlayer():
                text = "{} ({})".format(entry.getPlayerScore(), kind)
                font = item.font()
                font.setBold(True)
                item.setFont(font)
            else:
                text = ""
            item.setText(text)
            self.setItem(i, j, item)
        self.scrollToBottom()


class CarcassonneEntriesPlot(GameRoundPlot):
    def updatePlot(self):
        if not self.isPlotInited():
            return
        super(CarcassonneEntriesPlot, self).updatePlot()
        scores = {}
        for player in self.engine.getPlayers():
            scores[player] = [0]

        for entry in self.engine.getRounds():
            for player in self.engine.getPlayers():
                if player == entry.getPlayer():
                    entryscore = entry.getPlayerScore()
                else:
                    entryscore = 0
                accumscore = scores[player][-1] + entryscore
                scores[player].append(accumscore)

        self.canvas.clearPlotContents()

        for player in self.engine.getListPlayers():
            self.canvas.addSeries(scores[player], player)

        self.canvas._scene.update()


class CarcassonneQSTW(QuickStatsTW):
    def initStatsWidgets(self):
        self.gs = CarcassonneQSBox(self)
        self.ps = CarcassonnePQSBox(self)


class CarcassonneQSBox(GeneralQuickStats):
    def __init__(self, parent=None):
        self.game = "Carcassonne"
        super(CarcassonneQSBox, self).__init__(self.game, parent)

    def initUI(self):
        self.singleRecordsLabel = QLabel(self)
        self.singleRecordsTable = StatsTable(self)
        self.matchRecordsLabel = QLabel(self)
        self.matchRecordsTable = StatsTable(self)

        super(CarcassonneQSBox, self).initUI()
        index = self.widgetLayout.count() - 1
        self.widgetLayout.insertWidget(index, self.singleRecordsLabel)
        self.widgetLayout.insertWidget(index + 1, self.singleRecordsTable)
        self.widgetLayout.insertWidget(index + 2, self.matchRecordsLabel)
        self.widgetLayout.insertWidget(index + 3, self.matchRecordsTable)

    def retranslateUI(self):
        self.singleRecordsLabel.setText(self.tr("Individual Records"))
        self.matchRecordsLabel.setText(self.tr("Match Records"))
        super(CarcassonneQSBox, self).retranslateUI()

    def updateContent(self, game=None):
        super(CarcassonneQSBox, self).updateContent(self.game)
        singleRecordStats = cast(
            "CarcassonneStatsEngine", self.stats
        ).getSingleKindRecords()
        matchRecordStats = cast(
            "CarcassonneStatsEngine", self.stats
        ).getMatchKindRecords()  # pyright: ignore[reportAttributeAccessIssue]

        if not singleRecordStats:
            self.singleRecordsLabel.hide()
        else:
            self.singleRecordsLabel.show()

        if not matchRecordStats:
            self.matchRecordsLabel.hide()
        else:
            self.matchRecordsLabel.show()

        for row in singleRecordStats:
            row["record"] = self.tr(row["record"])

        for row in matchRecordStats:
            row["record"] = self.tr(row["record"])

        keys = ["points", "player", "date"]
        headers = [
            self.tr("Record"),
            self.tr("Player"),
            self.tr("Date"),
        ]
        self.updateTable(
            self.singleRecordsTable, singleRecordStats, keys, "record", headers
        )
        self.updateTable(
            self.matchRecordsTable, matchRecordStats, keys, "record", headers
        )


class CarcassonnePQSBox(CarcassonneQSBox, ParticularQuickStats):
    pass
