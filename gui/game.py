#!/usr/bin/env python
# -*- coding: utf-8 -*-
from PyQt5 import QtCore, QtGui
from PyQt5.QtWidgets import (QAction, QApplication, QCheckBox, QFrame,
                             QGridLayout, QGroupBox, QHBoxLayout, QHeaderView,
                             QLCDNumber, QLabel, QMenu, QMessageBox,
                             QPushButton, QSizePolicy, QSpinBox, QTabWidget,
                             QTableWidget, QToolBox, QVBoxLayout, QWidget)
import ctypes

from gui.tab import Tab
from gui.clock import GameClock
from gui.plots import PlotView
from gui.gamestats import QuickStatsTW
from gui.playerlist import PlayerOrderDialog

i18n = QApplication.translate

PlayerColours = [QtGui.QColor(237, 44, 48),
                #  QtGui.QColor(23, 89, 169),
                 QtGui.QColor(123, 164, 218),
                 QtGui.QColor(0, 140, 70),
                 QtGui.QColor(243, 124, 33),
                 QtGui.QColor(147, 112, 219),
                #  QtGui.QColor(101, 43, 145),
                #  QtGui.QColor(161, 29, 33),
                 QtGui.QColor(255, 0, 255)
                 ]


class GameWidget(Tab):

    i18n("GameWidget","Scoreboard")

    def __init__(self, game, players, engine=None, parent=None):
        super(GameWidget, self).__init__(parent)
        self.game = game
        if engine is not None:
            self.engine = engine
            self.players = self.engine.getListPlayers()
        else:
            self.players = players
            self.createEngine()
            for nick in players:
                self.engine.addPlayer(nick)
            self.engine.begin()
        self.engine.printStats()
        self.gameInput = None
        self.finished = False
        self.toggleScreenLock()
        self.initUI()

    def initUI(self):
        # Set up the main grid
        self.setStyleSheet("QGroupBox { font-size: 120%; font-weight: bold; }")
        # self.widgetLayout = QGridLayout(self)
        self.widgetLayout = QHBoxLayout(self)
        self.leftLayout = QVBoxLayout()
        self.rightLayout = QVBoxLayout()
        self.widgetLayout.addLayout(self.leftLayout)
        self.widgetLayout.addLayout(self.rightLayout)
        self.roundGroup = QGroupBox(self)
        self.leftLayout.addWidget(self.roundGroup)
        self.matchGroup = QGroupBox(self)
        self.rightLayout.addWidget(self.matchGroup)

        # Round Group
        self.roundLayout = QVBoxLayout(self.roundGroup)
        self.buttonGroupLayout = QHBoxLayout()
        self.roundLayout.addLayout(self.buttonGroupLayout)

        self.cancelMatchButton = QPushButton(self.roundGroup)
        self.buttonGroupLayout.addWidget(self.cancelMatchButton)
        self.cancelMatchButton.clicked.connect(self.cancelMatch)

        self.restartMatchButton = QPushButton(self.roundGroup)
        self.buttonGroupLayout.addWidget(self.restartMatchButton)
        self.restartMatchButton.clicked.connect(self.restartMatch)

        self.pauseMatchButton = QPushButton(self.roundGroup)
        self.buttonGroupLayout.addWidget(self.pauseMatchButton)
        self.pauseMatchButton.clicked.connect(self.pauseMatch)

        self.playerOrderButton = QPushButton(self.roundGroup)
        self.buttonGroupLayout.addWidget(self.playerOrderButton)
        self.playerOrderButton.clicked.connect(self.changePlayerOrder)

        self.commitRoundButton = QPushButton(self.roundGroup)
        self.buttonGroupLayout.addWidget(self.commitRoundButton)
        self.commitRoundButton.clicked.connect(self.commitRound)

        self.gameStatusLabel = QLabel(self.roundGroup)
        self.gameStatusLabel.setAlignment(QtCore.Qt.AlignCenter)
        self.roundLayout.addWidget(self.gameStatusLabel)

        # Match Group
        self.matchGroup.setTitle(i18n("GameWidget", "Game Time"))
        self.matchGroupLayout = QVBoxLayout(self.matchGroup)

        self.clock = GameClock(self.engine.getGameSeconds(), self)
        self.clock.setMinimumHeight(100)
        # Set size policy to Fixed in the vertical direction
        size_policy = self.matchGroup.sizePolicy()
        size_policy.setVerticalPolicy(QSizePolicy.Fixed)
        self.matchGroup.setSizePolicy(size_policy)
        self.matchGroupLayout.addWidget(self.clock)

        dpolicy = self.engine.getDealingPolicy()
        if dpolicy not in (self.engine.NoDealer, self.engine.StarterDealer):
            self.dealerPolicyCheckBox = QCheckBox(self.matchGroup)
            if self.engine.getDealingPolicy() == self.engine.WinnerDealer:
                self.dealerPolicyCheckBox.setChecked(True)
            else:
                self.dealerPolicyCheckBox.setChecked(False)
            self.dealerPolicyCheckBox.setStyleSheet(
                "QCheckBox { font-weight: bold; }")
            self.dealerPolicyCheckBox.stateChanged.connect(
                self.changeDealingPolicy)
            self.dealerPolicyCheckBox.setDisabled(
                self.engine.getNumRound() > 1)
            self.matchGroupLayout.addWidget(self.dealerPolicyCheckBox)

    def retranslateUI(self):
        self.setRoundTitle()
        self.matchGroup.setTitle(i18n("GameWidget", "Game Time"))
        self.pauseMatchButton.setText(
            i18n("GameWidget", "&Pause/Play"))
        self.cancelMatchButton.setText(
            i18n("GameWidget", "&Cancel Match"))
        self.restartMatchButton.setText(
            i18n("GameWidget", "Restart &Match"))
        self.commitRoundButton.setText(
            i18n("GameWidget", "Commit &Round"))
        self.playerOrderButton.setText(
            i18n("GameWidget", "Player &Order"))
        if self.engine.getDealingPolicy() not in (
                self.engine.NoDealer, self.engine.StarterDealer):
            self.dealerPolicyCheckBox.setText(
                i18n("GameWidget", "Winner deals"))
        self.updateGameStatusLabel()

    def updateGameStatusLabel(self):
        self.gameStatusLabel.setStyleSheet(
            "QLabel { font-size: 16px; font-weight:bold; color: red;}")
        winner = self.engine.getWinner()
        if winner:
            self.gameStatusLabel.setText(i18n(
                "GameWidget", "{} won this match!").format(winner))
        elif self.engine.isPaused():
            self.gameStatusLabel.setText(
                i18n("GameWidget", "Game is paused"))
        else:
            self.gameStatusLabel.setText(
                i18n("GameWidget", ""))

    def cancelMatch(self):
        if not self.isFinished():
            tit = i18n("GameWidget", 'Cancel Match')
            msg = i18n(
                'GameWidget', 'Do you want to save the current {} match?')
            msg = msg.format(self.game)
            ret = QMessageBox.question(self, tit, msg,
                                       QMessageBox.Yes | QMessageBox.No |
                                       QMessageBox.Cancel, QMessageBox.Cancel)

            if ret == QMessageBox.Cancel:
                return
            if ret == QMessageBox.No:
                self.closeMatch()
            else:
                self.saveMatch()

        self.toggleScreenLock(True)
        self.requestClose()

    def restartMatch(self):
        if not self.isFinished():
            tit = i18n("GameWidget", 'Restart Match')
            msg = i18n(
                'GameWidget', 'Do you want to save the current {} match?')
            msg = msg.format(self.game)
            ret = QMessageBox.question(self, tit, msg,
                                       QMessageBox.Yes | QMessageBox.No |
                                       QMessageBox.Cancel,
                                       QMessageBox.Cancel)

            if ret == QMessageBox.Cancel:
                return
            if ret == QMessageBox.Yes:
                self.saveMatch()
        self.toggleScreenLock(True)
        self.requestRestart()

    def pauseMatch(self):
        if self.engine.isPaused():
            self.clock.unpauseTimer()
            self.commitRoundButton.setEnabled(True)
            self.gameInput.setEnabled(True)
            self.engine.unpause()
            self.toggleScreenLock()
        else:
            self.clock.pauseTimer()
            self.commitRoundButton.setDisabled(True)
            self.gameInput.setDisabled(True)
            self.engine.pause()
            self.toggleScreenLock(True)
        self.updateGameStatusLabel()

    def commitRound(self):

        nround = self.engine.getNumRound()
        print("Opening round {}".format(nround))
        self.engine.openRound(nround)
        winner = self.gameInput.getWinner()
        if not winner:
            msg = i18n("GameWidget", "No winner selected")
            QMessageBox.warning(self, self.game, msg)

            return
        else:
            self.engine.setRoundWinner(winner)
        scores = self.gameInput.getScores()
        for player, score in scores.items():
            if not self.checkPlayerScore(player, score):
                msg = i18n(
                    "GameWidget", "{0} score is not valid").format(player)
                QMessageBox.warning(self, self.game, msg)
                return
            extras = self.getPlayerExtraInfo(player)
            if extras is None:
                return
            self.engine.addRoundInfo(player, score, extras)

        # Everything ok so far, let's confirm
        tit = i18n("GameWidget", 'Commit Round')
        msg = i18n(
            "GameWidget", "Are you sure you want to commit the current round?")
        ret = QMessageBox.question(self, tit, msg,
                                   QMessageBox.Yes | QMessageBox.No,
                                   QMessageBox.Yes)

        if ret == QMessageBox.No:
            return

        # Once here, we can commit round
        self.unsetDealer()
        self.engine.commitRound()
        self.engine.printStats()
        self.updatePanel()
        if not self.engine.getWinner():
            self.setDealer()

    def changeDealingPolicy(self, *args, **kwargs):
        if self.dealerPolicyCheckBox.isChecked():
            self.engine.setDealingPolicy(self.engine.WinnerDealer)
        else:
            self.engine.setDealingPolicy(self.engine.RRDealer)

    def closeMatch(self): self.engine.cancelMatch()

    def saveMatch(self): self.engine.save()

    def checkPlayerScore(self, player, score):
        if score >= 0:
            return True
        else:
            return False

    def setRoundTitle(self):
        try:
            nround = self.engine.getNumRound()
            self.roundGroup.setTitle(i18n(
                "GameWidget", "Round {0}").format(str(nround)))
        except AttributeError:
            pass

    def updatePanel(self):
        self.gameInput.reset()
        try:
            self.dealerPolicyCheckBox.setEnabled(False)
        except AttributeError:
            pass
        if self.engine.getWinner():
            self.setWinner()
        else:
            self.setRoundTitle()

    def getGameName(self): return self.game

    def isFinished(self): return self.finished

    # To be implemented in subclasses
    def createEngine(self): pass

    def getPlayerExtraInfo(self, player): return {}

    def unsetDealer(self): pass

    def setDealer(self): pass

    def setWinner(self):
        self.finished = True
        self.pauseMatchButton.setDisabled(True)
        self.clock.stopTimer()
        self.commitRoundButton.setDisabled(True)
        self.playerOrderButton.setDisabled(True)
        self.updateGameStatusLabel()
        self.gameInput.setDisabled(True)
        self.toggleScreenLock(True)

    def changePlayerOrder(self):
        originaldealer = self.engine.getDealer()
        pod = PlayerOrderDialog(self.engine, self)
#         pod.dealerChanged.connect(self.changedDealer)
        if pod.exec_():
            newdealer = pod.getNewDealer()
            neworder = pod.getNewOrder()
            if self.players != neworder:
                # Do something
                self.engine.setListPlayers(neworder)
                self.players = neworder
                self.updatePlayerOrder()
            if originaldealer != newdealer:
                self.unsetDealer()
                self.engine.setDealer(newdealer)
                self.setDealer()

    def updatePlayerOrder(self):
        self.gameInput.updatePlayerOrder()

    def toggleScreenLock(self, on=False):
        ES_CONTINUOUS = 0x80000000
        ES_DISPLAY_REQUIRED = 0x00000002
        try:
            if not on:
                ctypes.windll.kernel32.SetThreadExecutionState(
                    ES_CONTINUOUS | ES_DISPLAY_REQUIRED)
                print("Disabled Screensaver")
            else:
                ctypes.windll.kernel32.SetThreadExecutionState(0)
                print("Enabled Screensaver")
        except Exception:
            pass


class GameInputWidget(QWidget):

    enterPressed = QtCore.pyqtSignal()

    def __init__(self, engine, parent=None):
        super(GameInputWidget, self).__init__(parent)
        self.engine = engine
        self.winnerSelected = ""
        self.playerInputList = {}

    def getWinner(self):
        maxScore = -1000000
        for player, score in self.getScores().items():
            if score > maxScore:
                maxScore = score
                self.winnerSelected = player
        return self.winnerSelected

    def getScores(self):
        scores = {}
        for player, piw in self.playerInputList.items():
            scores[player] = piw.getScore()
        return scores

    def reset(self):
        self.winnerSelected = ""
        for piw in self.playerInputList.values():
            piw.reset()

    def changedWinner(self, winner):
        print("Changing winner to {}".format(winner))
        winner = str(winner)
        if self.winnerSelected != "":
            self.playerInputList[self.winnerSelected].reset()
        self.winnerSelected = winner

    def keyPressEvent(self, event):
        if event.key() in (QtCore.Qt.Key_Return, QtCore.Qt.Key_Enter):
            self.enterPressed.emit()
            event.accept()
        return super(GameInputWidget, self).keyPressEvent(event)

    def mousePressEvent(self, event):
        self.setFocus()
        return QWidget.mousePressEvent(self, event)

    def updatePlayerOrder(self): pass


class ScoreSpinBox(QSpinBox):

    def __init__(self, *args, **kwargs):
        super(ScoreSpinBox, self).__init__(*args, **kwargs)
        self.setAccelerated(True)

    def valueFromText(self, text):
        if text == "":
            return self.minimum()
        else:
            return super(ScoreSpinBox, self).valueFromText(text)

    def textFromValue(self, value):
        if value == self.minimum():
            return ""
        else:
            return super(ScoreSpinBox, self).textFromValue(value)


class IconLabel(QLabel):
    #     def __init__(self,parent = None):
    #         super(IconLabel,self).__init__(parent)
    #         self._pixmap = None
    #     def setPixmap(self,pixmap):
    #         self._pixmap = pixmap
    #         super(IconLabel,self).setPixmap(pixmap)
    #     def resizeEvent(self, event):
    #         size = min(self.width(), self.height())
    #         self.setFixedSize(size,size)
    #         if self._pixmap and not self._pixmap.isNull():
    #             print(event)
    #             self.setPixmap(self._pixmap.scaled(size,
    #                            size,QtCore.Qt.KeepAspectRatio,
    #                            QtCore.Qt.SmoothTransformation))
    def setDisabled(self, b): pass

    def setEnabled(self, b): pass


class GamePlayerWidget(QGroupBox):

    def __init__(self, nick, colour=None, parent=None):
        super(GamePlayerWidget, self).__init__(parent)
        self.player = nick
        self.pcolour = colour
        self.initUI()

    def initUI(self):
        #        self.setMinimumWidth(300)
        self.mainLayout = QHBoxLayout(self)
#         self.mainLayout.addStretch()
        self.scoreLCD = QLCDNumber(self)
        self.scoreLCD.setSegmentStyle(QLCDNumber.Flat)
        self.mainLayout.addWidget(self.scoreLCD)
        self.scoreLCD.setNumDigits(3)
        self.scoreLCD.setFixedSize(100, 60)
        self.scoreLCD.display(0)
        css = "QLCDNumber {{ color:rgb({},{},{});}}"
        self.scoreLCD.setStyleSheet(css.format(self.pcolour.red(),
                                               self.pcolour.green(),
                                               self.pcolour.blue()))

        self.nameLabel = QLabel(self)
        self.nameLabel.setText(self.player)
        sh = ("QLabel {{ font-size: 32px; font-weight: "
              "bold; color:rgb({},{},{});}}")
        self.nameLabel.setStyleSheet(sh.format(self.pcolour.red(),
                                               self.pcolour.green(),
                                               self.pcolour.blue()))
        self.mainLayout.addWidget(self.nameLabel)

        self.dealerPixmap = QtGui.QPixmap('icons/cards.png')
        self.nonDealerPixmap = QtGui.QPixmap()
        self.winnerPixmap = QtGui.QPixmap('icons/winner.png')

        self.iconlabel = IconLabel(self)
        self.iconlabel.setFixedSize(50, 50)
        self.iconlabel.setScaledContents(True)
        self.mainLayout.insertWidget(0, self.iconlabel)
#         self.mainLayout.addStretch()
        self.unsetDealer()

    def updateDisplay(self, points):
        if points >= 1000 or points <= -100:
            self.scoreLCD.setNumDigits(4)
        else:
            self.scoreLCD.setNumDigits(3)
        self.scoreLCD.display(points)

    def setDealer(self): self.iconlabel.setPixmap(self.dealerPixmap)

    def unsetDealer(self): self.iconlabel.setPixmap(self.nonDealerPixmap)

    def setWinner(self): self.iconlabel.setPixmap(self.winnerPixmap)

    def setColour(self, colour):
        self.pcolour = colour
        css = "QLCDNumber {{ color:rgb({},{},{});}}"
        self.scoreLCD.setStyleSheet(css.format(self.pcolour.red(),
                                               self.pcolour.green(),
                                               self.pcolour.blue()))
        sh = ("QLabel {{ font-size: 32px; font-weight: bold; "
              "color:rgb({},{},{});}}")
        self.nameLabel.setStyleSheet(sh.format(self.pcolour.red(),
                                               self.pcolour.green(),
                                               self.pcolour.blue()))


class GameRoundsDetail(QGroupBox):

    edited = QtCore.pyqtSignal()

    def __init__(self, engine, parent=None):
        super(GameRoundsDetail, self).__init__(parent)
        self.engine = engine
        self.initUI()

    def initUI(self):
        self.setStyleSheet("QGroupBox { font-size: 18px; font-weight: bold; }")
        self.widgetLayout = QVBoxLayout(self)
#        self.container = QToolBox(self)
        self.container = QTabWidget(self)
        self.widgetLayout.addWidget(self.container)

        self.tableContainer = QFrame(self)
        self.tableContainerLayout = QVBoxLayout(self.tableContainer)
        self.tableContainer.setAutoFillBackground(True)
        self.container.addTab(self.tableContainer, '')

        self.table = self.createRoundTable(self.engine, self)
        self.tableContainerLayout.addWidget(self.table, stretch=1)
        self.table.edited.connect(self.updateRound)
        self.table.edited.connect(self.edited.emit)

        self.plot = self.createRoundPlot(self.engine, self)
        self.plot.setAutoFillBackground(True)
#        self.container.addItem(self.plot,'')
        self.container.addTab(self.plot, '')

        self.statsFrame = QWidget(self)
        self.statsFrame.setAutoFillBackground(True)
        self.container.addTab(self.statsFrame, '')

        self.statsLayout = QVBoxLayout(self.statsFrame)
        self.gamestats = self.createQSBox(self.statsFrame)
        self.statsLayout.addWidget(self.gamestats)

    def retranslateUI(self):
        # self.setTitle(i18n("GameRoundsDetail",'Details'))
        self.container.setTabText(
            0, i18n("GameRoundsDetail", "Table"))
        self.container.setTabText(
            1, i18n("GameRoundsDetail", "Plot"))
        self.container.setTabText(2, i18n(
            "GameRoundsDetail", "Statistics"))
#        self.container.setItemText(0,i18n(
        #       "CarcassonneEntriesDetail","Table"))
#        self.container.setItemText(1,i18n(
        #       "CarcassonneEntriesDetail","Plot"))
#        self.container.setItemText(2,i18n(
        #       "CarcassonneEntriesDetail","Statistics"))
        self.gamestats.retranslateUI()
        self.plot.retranslateUI()
        self.updateRound()

    def updatePlot(self):
        self.plot.updatePlot()

    def updateRound(self):
        self.table.resetClear()
        for r in self.engine.getRounds():
            self.table.insertRound(r)
        self.updatePlot()

    def updateStats(self):
        try:
            self.gamestats.update(self.engine.getGame(),
                                  self.engine.getListPlayers())
        except Exception:
            self.gamestats.update()

    def deleteRound(self, nround):
        self.plot.updatePlot()

    # Implement in subclasses if necessary
    def createRoundTable(
        self, engine, parent=None): return GameRoundTable(self)

    def createRoundPlot(self, engine, parent=None): return GameRoundPlot(self)

    def createQSBox(self, parent=None): return QuickStatsTW(
        self.engine.getGame(), self.engine.getListPlayers(), self)

    def updatePlayerOrder(self):
        self.updateRound()


class GameRoundTable(QTableWidget):

    edited = QtCore.pyqtSignal()

    def __init__(self, engine, parent=None):
        super(GameRoundTable, self).__init__(parent)
        self.engine = engine
        self.setColumnCount(len(self.engine.getListPlayers()))
        self.initUI()

    def initUI(self):
        self.setHorizontalHeaderLabels(self.engine.getListPlayers())
        self.horizontalHeader().setSectionResizeMode(
            QHeaderView.Stretch)
        self.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.openTableMenu)

    def resetClear(self):
        self.setHorizontalHeaderLabels(self.engine.getListPlayers())
        self.clearContents()
        self.setRowCount(0)

    def openTableMenu(self, position):
        item = self.indexAt(position)
        nentry = item.row() + 1
        if nentry <= 0 or self.engine.getWinner():
            return

        menu = QMenu()
        ic = QtGui.QIcon('icons/delete.png')
        msg = i18n("GameRoundTable", "Delete Entry")
        deleteEntryAction = QAction(ic, msg, self)
        menu.addAction(deleteEntryAction)
        action = menu.exec_(self.mapToGlobal(position))
        if action == deleteEntryAction:
            title = i18n("GameRoundTable", 'Delete Entry')
            msg = i18n("GameRoundTable", "Are you sure you want to \
                        delete this entry?")
            ret = QMessageBox.question(self, title, msg,
                                       QMessageBox.Yes | QMessageBox.No,
                                       QMessageBox.Yes)
            if ret == QMessageBox.No:
                return
            self.engine.deleteRound(nentry)
            self.removeRow(item.row())
            self.edited.emit()

    # ReImplement in subclasses
    def insertRound(self, rnd): pass


class GameRoundPlot(QWidget):
    def __init__(self, engine, parent=None):
        super(GameRoundPlot, self).__init__(parent)
        self.plotinited = False
        self.engine = engine
        self.parent = parent
        self.axiswidth = 0
        self.initUI()

    def initUI(self):
        self.widgetLayout = QHBoxLayout(self)
        self.canvas = PlotView(PlayerColours, self)
        self.canvas.setBackground(self.palette().color(self.backgroundRole()))
        self.canvas.addLinePlot()
        self.widgetLayout.addWidget(self.canvas)
        self.plotinited = True
    
    def paintEvent(self, event):
        self.canvas.setBackground(self.palette().color(self.backgroundRole()))
        QWidget.paintEvent(self, event)

    def retranslateUI(self): self.retranslatePlot()

    def isPlotInited(self): return self.plotinited

    def updatePlot(self): pass

    def retranslatePlot(self): pass
