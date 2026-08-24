import ctypes
import shutil
import subprocess
import sys
from typing import cast

from PySide6 import QtCore, QtGui
from PySide6.QtCore import (
    QCoreApplication,
    QEasingCurve,
    QEvent,
    QFile,
    QObject,
    QPropertyAnimation,
    QRectF,
    QSize,
)
from PySide6.QtGui import (
    QAction,
    QColor,
    QFont,
    QImage,
    QPainter,
    QPainterPath,
    QShortcut,
)
from PySide6.QtSvg import QSvgRenderer
from PySide6.QtWidgets import (
    QApplication,
    QFrame,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLCDNumber,
    QLineEdit,
    QMenu,
    QMessageBox,
    QPushButton,
    QSizePolicy,
    QStackedLayout,
    QTableWidget,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from controllers.baseengine import EntryGameEngine
from controllers.settings import appsettings
from gui.clock import GameClock
from gui.gamelogapplication import GamelogApplication
from gui.gamestats import QuickStatsTW
from gui.languagechooser import LanguageButton
from gui.matchedit import MatchTimesEditDialog
from gui.playerlist import PlayerOrderDialog
from gui.plots import PlotView
from gui.settings import SettingsDialog
from gui.tab import Tab

# i18n = QApplication.translate

PlayerColours = [
    QtGui.QColor(237, 44, 48),
    #  QtGui.QColor(23, 89, 169),
    QtGui.QColor(123, 164, 218),
    QtGui.QColor(0, 140, 70),
    QtGui.QColor(243, 124, 33),
    QtGui.QColor(147, 112, 219),
    #  QtGui.QColor(101, 43, 145),
    #  QtGui.QColor(161, 29, 33),
    QtGui.QColor(255, 0, 255),
    QtGui.QColor(0, 200, 200),  # Cyan / Teal
    QtGui.QColor(255, 215, 0),  # Gold / Yellow
    QtGui.QColor(0, 255, 127),  # Spring Green
    QtGui.QColor(255, 105, 180),  # Hot Pink
    QtGui.QColor(173, 216, 230),  # Light Blue
    QtGui.QColor(255, 165, 79),  # Light Orange
]


class GameWidget(Tab):
    QCoreApplication.translate("GameWidget", "Scoreboard")

    def __init__(self, game, players, engine=None, parent=None):
        super().__init__(parent)
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
        self.finished = False
        self.hideInputOnFinish = True

        self.screen_blocker = SleepBlocker()
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
        self.matchGroup.setMinimumWidth(220)
        self.rightLayout.addWidget(self.matchGroup)

        # Round Group
        self.roundLayout = QVBoxLayout(self.roundGroup)
        self.buttonGroupLayout = QHBoxLayout()
        self.roundLayout.addLayout(self.buttonGroupLayout)

        self.cancelMatchButton = QPushButton(self.roundGroup)
        self.buttonGroupLayout.addWidget(self.cancelMatchButton, 3)
        self.cancelMatchButton.clicked.connect(self.cancelMatch)

        self.restartMatchButton = QPushButton(self.roundGroup)
        self.buttonGroupLayout.addWidget(self.restartMatchButton, 3)
        self.restartMatchButton.clicked.connect(self.restartMatch)

        self.pauseMatchButton = QPushButton(self.roundGroup)
        self.buttonGroupLayout.addWidget(self.pauseMatchButton, 3)
        self.pauseMatchButton.clicked.connect(self.pauseMatch)

        self.playerOrderButton = QPushButton(self.roundGroup)
        self.buttonGroupLayout.addWidget(self.playerOrderButton, 3)
        self.playerOrderButton.clicked.connect(self.changePlayerOrder)

        self.separator1 = QWidget(self.roundGroup)
        self.buttonGroupLayout.addWidget(self.separator1)

        self.languageButton = LanguageButton(self.roundGroup)
        self.buttonGroupLayout.addWidget(self.languageButton)

        self.settingsButton = QPushButton(self)
        self.settingsButton.setSizePolicy(
            QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Maximum
        )
        self.buttonGroupLayout.addWidget(self.settingsButton)
        self.settingsButton.clicked.connect(self.onSettings)

        self.separator2 = QWidget(self.roundGroup)
        self.buttonGroupLayout.addWidget(self.separator2)

        self.commitRoundButton = QPushButton(self.roundGroup)
        self.buttonGroupLayout.addWidget(self.commitRoundButton, 3)
        # self.commitRoundButton.setMinimumWidth(64)
        self.commitRoundButton.clicked.connect(self.commitRound)

        self.undoButton = QPushButton(self.roundGroup)
        self.buttonGroupLayout.addWidget(self.undoButton, 2)
        self.undoButton.setEnabled(
            self.engine.getNumRound() > 1 and not self.engine.getWinner()
        )
        self.undoButton.clicked.connect(self.undoCommit)

        self.finishButton = QPushButton(self.roundGroup)
        self.buttonGroupLayout.addWidget(self.finishButton, 3)
        self.finishButton.clicked.connect(self.finish)
        self.finishButton.setVisible(self.engine.requiresExplicitFinish())

        self.gameStatusLabel = QLabel(self.roundGroup)
        self.gameStatusLabel.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        # self.gameStatusLabel.hide()
        self.roundLayout.addWidget(self.gameStatusLabel)

        # Match Group
        # self.matchGroup.setTitle(self.tr("Game Time"))
        self.matchGroupLayout = QVBoxLayout(self.matchGroup)

        self.roundTitleLabel = QLabel(self)
        self.roundTitleLabel.setSizePolicy(
            QSizePolicy.Policy.Preferred,  # horizontal
            QSizePolicy.Policy.Maximum,  # vertical
        )
        css = """
        QLabel {
            font-size: 18px;
            font-weight: bold;
            qproperty-alignment: AlignCenter;
        }
        """
        self.roundTitleLabel.setStyleSheet(css)
        self.matchGroupLayout.addWidget(self.roundTitleLabel)

        self.clock = GameClock(self.engine.getGameSeconds(), self)
        self.clock.setMinimumHeight(70)
        self.clock.doubleClicked.connect(self.editGameTime)
        # self.clock.setMinimumWidth(200)
        self.clock.setSizePolicy(
            QSizePolicy.Policy.Preferred,  # horizontal
            QSizePolicy.Policy.Maximum,  # vertical
        )
        # Set size policy to Fixed in the vertical direction
        # size_policy = self.matchGroup.sizePolicy()
        # size_policy.setVerticalPolicy(QSizePolicy.Policy.Fixed)
        # self.matchGroup.setSizePolicy(size_policy)
        self.matchGroupLayout.addWidget(self.clock)

        dpolicy = self.engine.getDealingPolicy()
        if dpolicy not in (self.engine.NoDealer, self.engine.StarterDealer):
            # self.dealerPolicyCheckBox = QCheckBox(self.matchGroup)
            self.dealerPolicyCheckBox = QPushButton(self.matchGroup)
            self.dealerPolicyCheckBox.setCheckable(True)
            if self.engine.getDealingPolicy() == self.engine.WinnerDealer:
                self.dealerPolicyCheckBox.setChecked(True)
            else:
                self.dealerPolicyCheckBox.setChecked(False)
            # self.dealerPolicyCheckBox.stateChanged.connect(self.changeDealingPolicy)
            self.dealerPolicyCheckBox.toggled.connect(self.changeDealingPolicy)
            self.dealerPolicyCheckBox.setDisabled(self.engine.getNumRound() > 1)
            # self.dealerPolicyCheckBox.setSizePolicy(
            #     QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed
            # )
            self.dealerPolicyCheckBox.setSizePolicy(
                QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Maximum
            )
            self.dealerPolicyCheckBox.setProperty("textStateOnly", True)

            # self.dealerPolicyCheckBox.setStyleSheet("""
            #     QPushButton {
            #         border: 2px solid #888;
            #         border-radius: 6px;
            #         padding: 6px 6px;
            #         background: transparent;
            #         color: white;
            #     }

            #     /* Checked (enabled) */
            #     QPushButton:checked:enabled {
            #         background: #888;
            #     }

            #     /* Unchecked (enabled) */
            #     QPushButton:!checked:enabled {
            #         background: transparent;
            #     }

            #     /* Disabled but checked */
            #     QPushButton:checked:disabled {
            #         background: #666;
            #         border-color: #666;
            #     }

            #     /* Disabled and unchecked */
            #     QPushButton:disabled:!checked {
            #         border-color: #555;
            #     }
            #     """)
            self.matchGroupLayout.addWidget(
                self.dealerPolicyCheckBox,
                # alignment=QtCore.Qt.AlignmentFlag.AlignHCenter,
            )
        self.gameInput = self.createGameInputWidget(self)
        self._commit_round_connection = False
        self.guardCommitButton()
        self.gameInput.changed.connect(self.guardCommitButton)
        self.focussc = QShortcut(
            QtGui.QKeySequence("Ctrl+A"), self, self.gameInput.setFocus
        )
        self.roundLayout.addWidget(self.gameInput)
        self.detailGroup = self.createRoundsDetail(self)
        # self.widgetLayout.addWidget(self.detailGroup, 1, 0)
        self.leftLayout.addWidget(self.detailGroup)
        self.detailGroup.edited.connect(self.updatePanel)

        self.addExtraConfig()
        self.addPlayerWidgets()

        QtCore.QTimer.singleShot(500, self.gameInput.setFocus)

    def retranslateUI(self):
        self.setRoundTitle()
        # self.matchGroup.setTitle(self.tr("Game Time"))
        if appsettings["text_in_buttons"]:
            self.pauseMatchButton.setText(self.tr("&Pause/Play"))
            self.cancelMatchButton.setText(self.tr("&Leave Match"))
            self.restartMatchButton.setText(self.tr("Restart &Match"))
            if isinstance(self.engine, EntryGameEngine):
                self.commitRoundButton.setText(self.tr("Commit &Entry"))
            else:
                self.commitRoundButton.setText(self.tr("Commit &Round"))
            self.undoButton.setText(self.tr("Rollback"))
            self.playerOrderButton.setText(self.tr("Player &Order"))
            self.finishButton.setText(self.tr("&Finish Game"))
        else:
            self.pauseMatchButton.setText("⏸")
            self.cancelMatchButton.setText("⎋")
            self.restartMatchButton.setText("↻")
            self.commitRoundButton.setText("⏺")
            self.undoButton.setText("⎌")
            self.playerOrderButton.setText("♟↕")
            self.finishButton.setText("⏹")
        self.settingsButton.setText("⚙")
        self.gameInput.retranslateUI()
        if self.engine.getDealingPolicy() not in (
            self.engine.NoDealer,
            self.engine.StarterDealer,
        ):
            self.changeDealingPolicy()
        self.detailGroup.retranslateUI()
        self.updateGameStatusLabel()

    def createGameInputWidget(self, parent=None):
        return GameInputWidget(self.engine, parent)

    def createRoundsDetail(self, parent=None):
        return GameRoundsDetail(self.engine, parent)

    def onSettings(self):
        sd = SettingsDialog(parent=self)
        sd.settingChanged.connect(self.watchSettingChange)
        # sd.settingChanged.connect(self.retranslateUI)
        sd.exec()

    def watchSettingChange(self, name, value):
        if name == "language":
            self.languageButton.changeLanguage(value)
        elif name == "theme":
            app = QApplication.instance()
            if app:
                cast(GamelogApplication, app).themeManager.set_theme(value)
        else:
            self.retranslateUI()

    def addPlayerWidgets(self):
        self.playersLayout = QVBoxLayout()
        self.matchGroupLayout.addLayout(self.playersLayout)
        self.playerGroupBox = {}
        for i, player in enumerate(self.players):
            pw = GamePlayerWidget(player, PlayerColours[i], self.matchGroup)
            pw.updateDisplay(self.engine.getScoreFromPlayer(player))
            if player == self.engine.getDealer():
                pw.setDealer()
            self.playersLayout.addWidget(pw)
            self.playerGroupBox[player] = pw

    def addExtraConfig(self):
        pass

    def updateGameStatusLabel(self):
        self.gameStatusLabel.setStyleSheet(
            "QLabel { font-size: 16px; font-weight:bold; color: red;}"
        )
        winner = self.engine.getWinner()
        if winner:
            # self.gameStatusLabel.show()
            self.gameStatusLabel.setText(self.tr("{} won this match!").format(winner))
        elif self.engine.isPaused():
            self.gameStatusLabel.setText(self.tr("Game is paused"))
            # self.gameStatusLabel.show()
        else:
            self.gameStatusLabel.setText(self.tr(""))
            # self.gameStatusLabel.hide()

    def cancelMatch(self):
        if not self.isFinished():
            tit = self.tr("Leave Match")
            msg = self.tr("Do you want to save the current {} match?")
            msg = msg.format(self.game)
            ret = QMessageBox.question(
                self,
                tit,
                msg,
                QMessageBox.StandardButton.Yes
                | QMessageBox.StandardButton.No
                | QMessageBox.StandardButton.Cancel,
                QMessageBox.StandardButton.Cancel,
            )

            if ret == QMessageBox.StandardButton.Cancel:
                return
            if ret == QMessageBox.StandardButton.No:
                self.closeMatch()
            else:
                self.saveMatch()

        self.toggleScreenLock(True)
        self.requestClose()

    def restartMatch(self):
        if not self.isFinished():
            tit = self.tr("Restart Match")
            msg = self.tr("Do you want to save the current {} match?")
            msg = msg.format(self.game)
            ret = QMessageBox.question(
                self,
                tit,
                msg,
                QMessageBox.StandardButton.Yes
                | QMessageBox.StandardButton.No
                | QMessageBox.StandardButton.Cancel,
                QMessageBox.StandardButton.Cancel,
            )

            if ret == QMessageBox.StandardButton.Cancel:
                return
            if ret == QMessageBox.StandardButton.Yes:
                self.saveMatch()
        self.toggleScreenLock(True)
        self.requestRestart()

    def pauseMatch(self):
        if self.engine.isPaused():
            self.clock.unpauseTimer()
            self.commitRoundButton.setEnabled(self.commitRoundSanityCheck())
            self.gameInput.setEnabled(True)
            self.engine.unpause()
            self.toggleScreenLock()
            if not appsettings["text_in_buttons"]:
                self.pauseMatchButton.setText("⏸")
        else:
            self.clock.pauseTimer()
            self.commitRoundButton.setDisabled(True)
            self.gameInput.setDisabled(True)
            self.engine.pause()
            self.toggleScreenLock(True)
            if not appsettings["text_in_buttons"]:
                self.pauseMatchButton.setText("▶")
        self.updateGameStatusLabel()

    def guardCommitButton(self):
        if self.commitRoundSanityCheck() and not self.engine.getWinner():
            self.commitRoundButton.setDisabled(False)
            self.gameInput.enterPressed.connect(self.commitRound)
            self._commit_round_connection = True
        else:
            self.commitRoundButton.setDisabled(True)
            if self._commit_round_connection:
                self.gameInput.enterPressed.disconnect(self.commitRound)
                self._commit_round_connection = False

    def commitRoundSanityCheck(self, interactive=False):

        winner = self.gameInput.getWinner()
        if not winner:
            msg = self.tr("No winner selected")
            if interactive:
                QMessageBox.warning(self, self.game, msg)
            else:
                print(f"SANITYCHECK: {msg}", file=sys.stderr)
            return False
        print(f"SANITYCHECK: winner={winner}", file=sys.stderr)
        scores = self.gameInput.getScores()
        for player, score in scores.items():
            if not self.checkPlayerScore(player, score):
                msg = self.tr("{} score is not valid").format(player)
                if interactive:
                    QMessageBox.warning(self, self.game, msg)
                else:
                    print(f"SANITYCHECK: {msg}", file=sys.stderr)
                    return False
            extras = self.getPlayerExtraInfo(player)
            if extras is None:
                msg = self.tr("No extras")
                print(f"SANITYCHECK: {msg}", file=sys.stderr)
                return False
        print("SANITYCHECK: Ready to commit", file=sys.stderr)
        return True

    def commitRound(self):
        if not self.commitRoundSanityCheck(interactive=True):
            return
        nround = self.engine.getNumRound()
        print(f"Opening round {nround}")
        self.engine.openRound(nround)
        winner = self.gameInput.getWinner()
        self.engine.setRoundWinner(winner)
        scores = self.gameInput.getScores()
        for player, score in scores.items():
            extras = self.getPlayerExtraInfo(player)
            self.engine.addRoundInfo(player, score, extras)

        # Everything ok so far, let's confirm
        # tit = self.tr('Commit Round')
        # msg = i18n(
        #     "GameWidget", "Are you sure you want to commit the current round?")
        # ret = QMessageBox.question(self, tit, msg,
        #                            QMessageBox.Yes | QMessageBox.No,
        #                            QMessageBox.Yes)

        # if ret == QMessageBox.No:
        #     return

        # Once here, we can commit round
        self.unsetDealer()
        self.engine.commitRound()
        self.engine.printStats()
        self.updatePanel()
        if not self.engine.getWinner():
            self.setDealer()
        elif self.hideInputOnFinish:
            self.gameInput.hide()

    def undoCommit(self):
        if len(self.engine.getRounds()) == 0:
            return

        title = self.tr("Rollback")
        msg = self.tr("Are you sure you want to undo the last entry?")
        ret = QMessageBox.question(
            self,
            title,
            msg,
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.Yes,
        )
        if ret == QMessageBox.StandardButton.No:
            return
        try:
            self.unsetDealer()
        except KeyError:
            pass
        self.engine.deleteRound(len(self.engine.getRounds()))
        self.updatePanel()
        try:
            self.setDealer()
        except KeyError:
            pass

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

    def changeDealingPolicy(self, *args, **kwargs):
        if self.dealerPolicyCheckBox.isChecked():
            self.dealerPolicyCheckBox.setText(self.tr("Winner deals"))
            self.engine.setDealingPolicy(self.engine.WinnerDealer)
        else:
            self.dealerPolicyCheckBox.setText(self.tr("Next player deals"))
            self.engine.setDealingPolicy(self.engine.RRDealer)

    def closeMatch(self):
        self.engine.cancelMatch()

    def saveMatch(self):
        self.engine.save()

    def checkPlayerScore(self, player, score, extras=None):
        return score >= 0

    def setRoundTitle(self):
        game = self.engine.getGame()
        if game is None:
            game = ""
        if isinstance(self.engine, EntryGameEngine):
            self.roundTitleLabel.setText(game)
        else:
            try:
                nround = self.engine.getNumRound()
                # self.roundGroup.setTitle(self.tr("Round {0}").format(str(nround)))
                self.roundTitleLabel.setText(
                    self.tr("{} - Round {}").format(game, str(nround))
                )
            except AttributeError:
                self.roundTitleLabel.setText(game)

    def updatePanel(self):
        self.updateScores()
        self.gameInput.reset()
        self.undoButton.setEnabled(
            self.engine.getNumRound() > 1 and not self.engine.getWinner()
        )
        dpolicy = self.engine.getDealingPolicy()
        if dpolicy not in (self.engine.NoDealer, self.engine.StarterDealer):
            self.dealerPolicyCheckBox.setDisabled(self.engine.getNumRound() > 1)
        if self.engine.getWinner():
            self.setWinner()
            try:
                self.detailGroup.updateStats()  # pyright: ignore[reportAttributeAccessIssue]
            except AttributeError:
                pass
        else:
            self.setRoundTitle()
            self.gameInput.setFocus()
            try:
                self.detailGroup.updateRound()  # pyright: ignore[reportAttributeAccessIssue]
            except AttributeError:
                pass
        if self.engine.getWinner() and self.engine.requiresExplicitFinish():
            self.finishButton.setDisabled(True)
        self.guardCommitButton()

    def getGameName(self):
        return self.game

    def isFinished(self):
        return self.finished

    # To be implemented in subclasses
    def createEngine(self):
        pass

    def getPlayerExtraInfo(self, player):
        return {}

    def unsetDealer(self):
        try:
            self.playerGroupBox[self.engine.getDealer()].unsetDealer()
        except (AttributeError, KeyError):
            pass

    def setDealer(self):
        try:
            self.playerGroupBox[self.engine.getDealer()].setDealer()
        except (AttributeError, KeyError):
            pass

    def updateScores(self):
        try:
            for player in self.players:
                score = self.engine.getScoreFromPlayer(player)
                self.playerGroupBox[player].updateDisplay(score)
        except (AttributeError, KeyError):
            pass

    def setWinner(self):
        self.finished = True
        self.pauseMatchButton.setDisabled(True)
        self.clock.stopTimer()
        self.commitRoundButton.setDisabled(True)
        self.playerOrderButton.setDisabled(True)
        self.updateGameStatusLabel()
        self.gameInput.setDisabled(True)
        if self.hideInputOnFinish:
            self.gameInput.hide()
        self.toggleScreenLock(True)
        winner = self.engine.getWinner()
        try:
            if winner in self.players:
                self.playerGroupBox[winner].setWinner()
        except (AttributeError, KeyError):
            pass

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
        try:
            for player in self.engine.getListPlayers():
                self.playersLayout.removeWidget(self.playerGroupBox[player])

            for i, player in enumerate(self.engine.getListPlayers()):
                self.playersLayout.addWidget(self.playerGroupBox[player])
                self.playerGroupBox[player].setColour(PlayerColours[i])
        except AttributeError:
            pass
        try:
            self.detailGroup.updatePlayerOrder()  # pyright: ignore[reportAttributeAccessIssue]
        except AttributeError:
            pass
        self.gameInput.updatePlayerOrder()

    def toggleScreenLock(self, on=False):
        if not on:
            self.screen_blocker.start()
            print("Enabled Screensaver")
        else:
            self.screen_blocker.stop()
            print("Disabled Screensaver")

    def editGameTime(self):
        if self.finished:
            mted = MatchTimesEditDialog(self.engine, self)
            mted.exec_()
            self.clock.showTime(self.engine.getGameSeconds())


class GameInputWidget(QWidget):
    enterPressed = QtCore.Signal()
    changed = QtCore.Signal()

    def __init__(self, engine, parent=None):
        super().__init__(parent)
        self.engine = engine
        self.winnerSelected = ""
        self.playerInputList = {}
        self.initUI()

    def initUI(self):
        pass

    def retranslateUI(self):
        pass

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
        print(f"Changing winner to {winner}")
        winner = str(winner)
        if self.winnerSelected != "":
            self.playerInputList[self.winnerSelected].reset()
        self.winnerSelected = winner

    def keyPressEvent(self, event):
        if event.key() in (QtCore.Qt.Key.Key_Return, QtCore.Qt.Key.Key_Enter):
            self.enterPressed.emit()
            event.accept()
        return super().keyPressEvent(event)

    def mousePressEvent(self, event):
        self.setFocus()
        return super().mousePressEvent(event)

    def updatePlayerOrder(self):
        pass


class GamePlayerWidget(QGroupBox):
    def __init__(self, nick, colour=None, parent=None):
        if not colour:
            colour = QtGui.QColor()
        super().__init__(parent)
        self.player = nick
        self.pcolour = colour
        self.initUI()

    def initUI(self):
        self.setTitle(self.player)
        #        self.setMinimumWidth(300)
        self.mainLayout = QHBoxLayout(self)
        #         self.mainLayout.addStretch()
        self.scoreLCD = QLCDNumber(self)
        self.scoreLCD.setSegmentStyle(QLCDNumber.SegmentStyle.Flat)
        self.scoreLCD.setFrameStyle(QFrame.Shape.NoFrame)
        self.mainLayout.addWidget(self.scoreLCD)
        self.scoreLCD.setDigitCount(3)
        # self.scoreLCD.setFixedSize(75, 45)
        # self.scoreLCD.setMaximumHeight(60)
        # self.scoreLCD.setMinimumHeight(30)
        self.scoreLCD.setMinimumWidth(50)
        self.scoreLCD.display(0)
        self.title_size = 28
        self.css = """
            QGroupBox {{ font-size: {3}px; font-weight: bold; color:rgb({0},{1},{2});}}

            QGroupBox[ko="true"] {{
                color: rgba({0},{1},{2},70);   /* lower alpha */
            }}

            QGroupBox::title {{
                subcontrol-origin: margin;
                subcontrol-position: top center;
                padding: 0 {4}px;
                background-color: transparent;
            }}
            QGroupBox QLCDNumber {{ color:rgb({0},{1},{2});}}
        """
        self.setColour(self.pcolour)

        self.dealerPixmap = QtGui.QPixmap(":/icons/cards.png")
        self.nonDealerPixmap = QtGui.QPixmap()
        self.winnerPixmap = QtGui.QPixmap(":/icons/winner.png")

        self.background = None
        self.bg_opacity = 1
        self.bg_size = 40
        self.unsetDealer()

    def updateDisplay(self, points):
        if points >= 1000 or points <= -100:
            self.scoreLCD.setDigitCount(4)
        else:
            self.scoreLCD.setDigitCount(3)
        self.scoreLCD.display(points)

    def setDealer(self):
        self.background = self.dealerPixmap
        self.update()

    def unsetDealer(self):
        self.background = None
        self.update()

    def setWinner(self):
        self.background = self.winnerPixmap
        self.update()

    def setColour(self, colour=None):
        if colour:
            self.pcolour = colour
        self.setStyleSheet(
            self.css.format(
                self.pcolour.red(),
                self.pcolour.green(),
                self.pcolour.blue(),
                self.title_size,
                self.title_size,
            )
        )

    def paintEvent(self, event):
        super().paintEvent(event)
        if not self.background:
            return
        painter = QPainter(self)
        painter.setOpacity(self.bg_opacity)

        scaled = self.background.scaled(
            max(self.bg_size, min(self.height() // 4, self.width() // 4)),
            max(self.bg_size, min(self.height() // 4, self.width() // 4)),
            QtCore.Qt.AspectRatioMode.KeepAspectRatio,
            QtCore.Qt.TransformationMode.SmoothTransformation,
        )

        # x = (self.width() - scaled.width()) // 2
        painter.drawPixmap(0, 0, scaled)


class GameRoundsDetail(QTabWidget):
    edited = QtCore.Signal()

    def __init__(self, engine, parent=None):
        super().__init__(parent)
        self.engine = engine
        self.initUI()

    def initUI(self):
        self.setStyleSheet("QGroupBox { font-size: 18px; font-weight: bold; }")
        self.widgetLayout = QVBoxLayout(self)

        self.tableContainer = QFrame(self)
        self.tableContainerLayout = QVBoxLayout(self.tableContainer)
        # self.tableContainer.setAutoFillBackground(True)
        self.addTab(self.tableContainer, "")

        self.table = self.createRoundTable(self.engine, self)
        self.tableContainerLayout.addWidget(self.table, stretch=1)
        self.table.edited.connect(self.updateRound)
        self.table.edited.connect(self.edited.emit)

        self.plot = self.createRoundPlot(self.engine, self)
        # self.plot.setAutoFillBackground(True)
        self.addTab(self.plot, "")

        self.gamestats = self.createQSBox()
        self.addTab(self.gamestats, "")

    def retranslateUI(self):
        # self.setTitle(i18n("GameRoundsDetail",'Details'))
        if appsettings["text_in_buttons"]:
            self.setTabText(self.indexOf(self.tableContainer), self.tr("Table"))
            self.setTabText(self.indexOf(self.plot), self.tr("Plot"))
            self.setTabText(self.indexOf(self.gamestats), self.tr("Statistics"))
        else:
            self.setTabText(self.indexOf(self.tableContainer), "☷")
            self.setTabText(self.indexOf(self.plot), "∿")
            self.setTabText(self.indexOf(self.gamestats), "σ")
        self.gamestats.retranslateUI()
        self.plot.retranslateUI()
        self.updateRound()
        # self.updateStats()

    def updatePlot(self):
        self.plot.updatePlot()

    def updateRound(self):
        self.table.resetClear()
        for r in self.engine.getRounds():
            self.table.insertRound(r)
        self.updatePlot()

    def updateStats(self):
        try:
            self.gamestats.updateContent(
                self.engine.getGame(), self.engine.getListPlayers()
            )
        except Exception as e:  # noqa: BLE001 # noqa: BLE001
            print(f"[UpdateStats] {e}", file=sys.stderr)
            self.gamestats.update()

    def deleteRound(self, _nround):
        self.plot.updatePlot()

    # Implement in subclasses if necessary
    def createRoundTable(self, _engine, parent):
        return GameRoundTable(self, parent)

    def createRoundPlot(self, _engine, parent):
        return GameRoundPlot(self, parent)

    def createQSBox(self):
        return QuickStatsTW(self.engine.getGame(), self.engine.getListPlayers(), self)

    def updatePlayerOrder(self):
        self.updateRound()


class GameRoundTable(QTableWidget):
    edited = QtCore.Signal()

    def __init__(self, engine, parent=None):
        super().__init__(parent)
        self.engine = engine
        self.setColumnCount(len(self.engine.getListPlayers()))
        self.initUI()

    def initUI(self):
        self.setHorizontalHeaderLabels(self.engine.getListPlayers())
        self.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.setContextMenuPolicy(QtCore.Qt.ContextMenuPolicy.CustomContextMenu)
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
        ic = QtGui.QIcon(":/icons/delete.png")
        msg = self.tr("Delete Entry")
        deleteEntryAction = QAction(ic, msg, self)
        menu.addAction(deleteEntryAction)
        action = menu.exec_(self.mapToGlobal(position))
        if action == deleteEntryAction:
            title = self.tr("Delete Entry")
            msg = self.tr("Are you sure you want to delete this entry?")
            ret = QMessageBox.question(
                self,
                title,
                msg,
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.Yes,
            )
            if ret == QMessageBox.StandardButton.No:
                return
            self.engine.deleteRound(nentry)
            self.removeRow(item.row())
            self.edited.emit()

    # ReImplement in subclasses
    def insertRound(self, _rnd):
        pass


class GameRoundPlot(QWidget):
    def __init__(self, engine, parent):
        super().__init__(parent)
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
        super().paintEvent(event)
        self.canvas.viewport().repaint()

    def retranslateUI(self):
        self.retranslatePlot()

    def isPlotInited(self):
        return self.plotinited

    def updatePlot(self):
        pass

    def retranslatePlot(self):
        pass


class SpaceFilter(QtCore.QObject):
    spacePressed = QtCore.Signal()

    def eventFilter(self, obj, event):
        if (
            event.type() == QtCore.QEvent.Type.KeyPress
            and event.key() == QtCore.Qt.Key.Key_Space
        ):
            self.spacePressed.emit()
            return True  # swallow the event
        return False


class ScoreSpinBox(QWidget):
    valueChanged = QtCore.Signal(object)
    spacePressed = QtCore.Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._value = 0
        self._minimum = 0
        self._maximum = 200
        self._start = 0
        self._step = 1
        self._hideMinimum = True
        self.pcolour = None
        self.initUI()

    def initUI(self):
        self.line_edit = QLineEdit()
        self.line_edit.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.line_edit.setInputMethodHints(QtCore.Qt.InputMethodHint.ImhDigitsOnly)
        self.line_edit.setMinimumWidth(40)
        self.line_edit.setSizePolicy(
            QSizePolicy.Policy.MinimumExpanding, QSizePolicy.Policy.Preferred
        )
        # self.line_edit.installEventFilter(self)
        # self.line_edit.setMaximumWidth(120)

        self._validator = QtGui.QIntValidator(self._minimum, self._maximum, self)
        self.line_edit.setValidator(self._validator)

        self.space_filter = SpaceFilter()
        self.line_edit.installEventFilter(self.space_filter)
        self.space_filter.spacePressed.connect(self.onSpacePressed)

        self.up_button = QPushButton()
        self.down_button = QPushButton()
        self.up_button.setSizePolicy(
            QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred
        )
        self.down_button.setSizePolicy(
            QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred
        )
        # self.down_button.setMaximumWidth(120)
        # self.up_button.setMaximumWidth(120)

        self.up_button.setText("▲")
        self.down_button.setText("▼")

        self.up_button.setAutoRepeat(True)
        self.down_button.setAutoRepeat(True)

        group = QHBoxLayout()
        group.setSpacing(4)
        group.setContentsMargins(0, 0, 0, 0)
        group.addWidget(self.down_button, stretch=1)
        group.addWidget(self.line_edit, stretch=2)
        group.addWidget(self.up_button, stretch=1)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        # layout.addStretch()
        layout.addLayout(group)
        # layout.addStretch()
        # ---- Styling (safe defaults) ----
        self._text_css = """
            QLineEdit {{
                font-size: 24px;
                font-weight: bold;
                padding: 2px;
                color:rgb({0},{1},{2});
            }}
            QLineEdit:focus {{
                border: 2px solid rgb({0},{1},{2}) ;   /* highlight color */
            }}
            QLineEdit:focus:hover {{
                border: 2px solid rgb({0},{1},{2}) ;   /* highlight color */
            }}
            QLineEdit:hover {{
                border: 1px solid rgba({0},{1},{2},150) ;   /* highlight color */
            }}
        """
        self._text_css_colourless = """
            QLineEdit {
                font-weight: bold;
                padding: 2px;
            }
            QLineEdit:focus {
                border: 2px solid ;   /* highlight color */
            }
            QLineEdit:focus:hover {
                border: 2px solid ;   /* highlight color */
            }
            QLineEdit:hover {
                border: 1px solid ;   /* highlight color */
            }
        """

        # self._text_css = """
        #     QLineEdit {{
        #         font-size: 24px;
        #         font-weight: bold;
        #         padding: 2px;
        #         border-radius: 6px;
        #         border: 1px solid #555555 ;
        #         background: transparent;
        #         color:rgb({0},{1},{2});
        #     }}
        #     QLineEdit:focus {{
        #         border: 2px solid rgb({0},{1},{2}) ;   /* highlight color */
        #     }}
        #     QLineEdit:focus:hover {{
        #         border: 2px solid rgb({0},{1},{2}) ;   /* highlight color */
        #     }}
        #     QLineEdit:hover {{
        #         border: 1px solid rgba({0},{1},{2},150) ;   /* highlight color */
        #     }}
        # """
        self._updateStyle()

        # self.up_button.setStyleSheet(self._button_style())
        # self.down_button.setStyleSheet(self._button_style())

        # ---- Connections ----
        self.up_button.clicked.connect(self.step_up)
        self.down_button.clicked.connect(self.step_down)
        self.line_edit.textChanged.connect(self._commit_text)
        self.line_edit.editingFinished.connect(self._snap_to_step)

        if self._value is not None:
            self.setValue(self._value)

    # ------------------------------------------------------------------
    # Styling helper
    # ------------------------------------------------------------------
    def _button_style(self):
        return """
        QToolButton {
            font-size: 18px;
            font-weight: bold;
            border: 1px solid #555555;
            border-radius: 6px;
        }
        """

    def setHideMinimum(self, hidemin):
        self._hideMinimum = hidemin

    def setColour(self, colour):
        self.pcolour = colour
        self._updateStyle()

    def _updateStyle(self):
        if self.pcolour:
            self.line_edit.setStyleSheet(
                self._text_css.format(
                    self.pcolour.red(), self.pcolour.green(), self.pcolour.blue()
                )
            )
        else:
            self.line_edit.setStyleSheet(self._text_css_colourless)

    def value(self):
        return self._value

    def setValue(self, value: int | None):
        if value is None:
            if value != self._value:
                self.valueChanged.emit(value)
            self._value = None
            self.line_edit.setText("")
        else:
            value = max(self._minimum, min(self._maximum, value))
            if value != self._value:
                self._value = value
                if self._hideMinimum and value == self._minimum:
                    self.line_edit.setText("")
                else:
                    self.line_edit.setText(str(value))
                self.valueChanged.emit(value)
        self._update_buttons()

    def setStep(self, step):
        self._step = step

    def setFocus(self, reason=QtCore.Qt.FocusReason.OtherFocusReason):
        self.line_edit.setFocus(reason)

    def _snap_to_step(self):
        if self._value is not None and self._step > 1:
            offset = self._value - self._minimum
            new_value = self._minimum + (offset // self._step) * self._step
            if self._value != new_value:
                self.setValue(new_value)

    def step_up(self):
        self.line_edit.setFocus()
        if self._value is None:
            self.setValue(self._start)
        else:
            self.setValue(self._value + self._step)

    def step_down(self):
        self.line_edit.setFocus()
        if self._value is None:
            self.setValue(self._start)
        else:
            self.setValue(self._value - self._step)

    def _commit_text(self):
        try:
            value = int(self.line_edit.text())
        except ValueError:
            value = self._value
        self.setValue(value)

    def setRange(self, minimum: int, maximum: int, start=None):
        self._minimum = minimum
        self._maximum = maximum
        self._start = minimum if start is None else start
        self._validator = QtGui.QIntValidator(self._minimum, self._maximum, self)
        self.line_edit.setValidator(self._validator)
        self.setValue(self._value)

    def setMinimum(self, minimum: int):
        self.setRange(minimum, self._maximum)

    def setMaximum(self, maximum: int):
        self.setRange(self._minimum, maximum)

    def setSingleStep(self, step: int):
        self._step = max(1, step)

    def clear(self):
        self.line_edit.clear()

    def reset(self):
        self.setValue(None)

    def setReadOnly(self, ro):
        self.line_edit.setReadOnly(ro)
        self.up_button.setDisabled(ro)
        self.down_button.setDisabled(ro)

    def lineEdit(self):
        return self.line_edit

    def _update_buttons(self):
        if not self.line_edit.isReadOnly():
            self.up_button.setEnabled(
                self._value is None or self._value < self._maximum
            )
            self.down_button.setEnabled(
                self._value is None or self._value > self._minimum
            )

    def wheelEvent(self, event):
        if self.line_edit.isReadOnly():
            return
        if event.angleDelta().y() > 0:
            self.step_up()
        else:
            self.step_down()
        event.accept()

    def textChangedAction(self, text):
        try:
            self.valueChanged.emit(int(text))
        except ValueError:
            pass

    def onSpacePressed(self):
        self.spacePressed.emit()

    def setDisabled(self, o):
        super().setDisabled(o)
        if o:
            self.setValue(self._start)


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
    def setDisabled(self, b):
        pass

    def setEnabled(self, b):
        pass


class BonusButton(QPushButton):
    bonusChanged = QtCore.Signal(str, object)

    def __init__(
        self,
        bonus_name: str,
        maximum: int = 1,
        colour=None,
        size=32,
        parent=None,
    ):
        super().__init__(parent)

        self.bonus_name = bonus_name
        self.maximum = maximum
        self.count = 0
        self.button_size = size
        self.highlight_colour = colour if colour else QColor(200, 0, 0)

        # Keep SVGs as SVGs and render them directly in paintEvent().
        self.svg_renderer = None

        svg_path = f":/icons/{bonus_name}.svg"
        png_path = f":/icons/{bonus_name}.png"

        if QFile.exists(svg_path):
            self.svg_renderer = QSvgRenderer(svg_path)

            if not self.svg_renderer.isValid():
                self.svg_renderer = None

        if self.svg_renderer is None and QFile.exists(png_path):
            original_image = QImage(png_path)

            self.image = original_image.scaled(
                self.button_size,
                self.button_size,
                QtCore.Qt.AspectRatioMode.KeepAspectRatio,
                QtCore.Qt.TransformationMode.SmoothTransformation,
            )

            self.grey_image = self.image.convertToFormat(
                QImage.Format.Format_Grayscale8
            )

        elif self.svg_renderer is None:
            # No SVG or PNG exists, so create a fallback icon.
            original_image = QImage(
                self.button_size,
                self.button_size,
                QImage.Format.Format_ARGB32_Premultiplied,
            )
            original_image.fill(QtCore.Qt.GlobalColor.transparent)

            painter = QPainter(original_image)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)

            # Light grey circle
            painter.setBrush(QColor("#D3D3D3"))
            painter.setPen(QtCore.Qt.PenStyle.NoPen)

            painter.drawEllipse(
                2,
                2,
                self.button_size - 4,
                self.button_size - 4,
            )

            # Bonus name
            painter.setPen(QColor("#333333"))
            painter.setFont(
                QFont(
                    "Arial",
                    int(self.button_size * 0.4),
                    QFont.Weight.Bold,
                )
            )

            painter.drawText(
                original_image.rect(),
                QtCore.Qt.AlignmentFlag.AlignCenter,
                bonus_name.upper(),
            )

            painter.end()

            self.image = original_image
            self.grey_image = original_image.convertToFormat(
                QImage.Format.Format_Grayscale8
            )

        self.setCheckable(True)
        self.setFlat(True)
        self.setStyleSheet("border: none;")

        self.setFixedSize(
            self.button_size,
            self.button_size,
        )

        self._fade_alpha = 0.0

        self.fade_anim = QPropertyAnimation(
            self,
            b"fade_alpha",
        )
        self.fade_anim.setDuration(400)
        self.fade_anim.setEasingCurve(QEasingCurve.Type.OutCubic)

        self.clicked.connect(self.plusone)

    def setColour(self, colour):
        self.highlight_colour = colour

    def plusone(self):
        old_value = self.count

        self.count = (self.count + 1) % (self.maximum + 1)

        self.setChecked(self.count > 0)

        # Transition 0 -> >0
        if old_value == 0 and self.count > 0:
            self.fade_anim.stop()
            self.fade_anim.setStartValue(0.0)
            self.fade_anim.setEndValue(1.0)
            self.fade_anim.start()

        # Transition >0 -> 0
        elif old_value > 0 and self.count == 0:
            self.fade_anim.stop()
            self.fade_anim.setStartValue(1.0)
            self.fade_anim.setEndValue(0.0)
            self.fade_anim.start()

        self.bonusChanged.emit(
            self.bonus_name,
            self,
        )
        self.update()

    def get_fade_alpha(self):
        return self._fade_alpha

    def set_fade_alpha(self, value):
        self._fade_alpha = float(value)
        self.update()

    fade_alpha = QtCore.Property(
        float,
        get_fade_alpha,
        set_fade_alpha,
    )

    def getValue(self):
        return self.count if self.isEnabled() else 0

    def setChecked(self, checked):
        if not checked:
            self.count = 0

        super().setChecked(checked)

    def sizeHint(self):
        return QtCore.QSize(
            self.button_size,
            self.button_size,
        )

    def setMaximum(self, maximum):
        self.maximum = maximum

        if self.count > self.maximum:
            self.count = self.maximum

            if self.count == 0:
                self.setChecked(False)

            self.update()

    def paintEvent(self, event):
        painter = QPainter(self)

        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)

        # --------------------------------------------------
        # Circular clipping
        # --------------------------------------------------

        path = QPainterPath()

        radius = (
            min(
                self.width(),
                self.height(),
            )
            / 2
        )

        center = self.rect().center()

        path.addEllipse(
            center,
            radius,
            radius,
        )

        painter.setClipPath(path)

        # --------------------------------------------------
        # Draw icon
        # --------------------------------------------------

        if self.svg_renderer is not None:
            # Render the SVG directly at the widget's
            # current size. This avoids intermediate
            # low-resolution rasterisation.
            self.svg_renderer.render(
                painter,
                QRectF(self.rect()),
            )

        else:
            if self.isEnabled():
                img_to_draw = self.image
            else:
                img_to_draw = self.grey_image
                self.setChecked(False)

            painter.drawImage(
                self.rect(),
                img_to_draw,
            )

        # --------------------------------------------------
        # Active outline
        # --------------------------------------------------

        if self.count > 0:
            alpha = int(255 * self._fade_alpha)

            ring_radius = radius - 2

            colour = QColor(self.highlight_colour)
            colour.setAlpha(alpha)

            pen = painter.pen()
            pen.setColor(colour)
            pen.setWidth(4)

            painter.setPen(pen)
            painter.setBrush(QtCore.Qt.BrushStyle.NoBrush)

            painter.drawEllipse(
                center,
                ring_radius,
                ring_radius,
            )

        # --------------------------------------------------
        # Count overlay
        # --------------------------------------------------

        if self.count >= 1 and self.maximum > 1:
            # Semi-transparent dark circle
            # behind the number.
            overlay_color = QColor(
                0,
                0,
                0,
                120,
            )

            painter.setBrush(overlay_color)
            painter.setPen(QtCore.Qt.PenStyle.NoPen)

            circle_diameter = (
                min(
                    self.width(),
                    self.height(),
                )
                * 0.45
            )

            circle_rect = QRectF(
                (self.width() - circle_diameter) / 2,
                (self.height() - circle_diameter) / 2,
                circle_diameter,
                circle_diameter,
            )

            painter.drawEllipse(circle_rect)

            # Number
            painter.setPen(self.highlight_colour)

            font = QFont(
                "Arial",
                int(circle_diameter * 0.9),
                QFont.Weight.Bold,
            )

            painter.setFont(font)

            painter.drawText(
                self.rect(),
                QtCore.Qt.AlignmentFlag.AlignCenter,
                str(self.count),
            )

        painter.end()


class SleepBlocker:
    def __init__(self):
        self.platform = sys.platform
        self.proc = None
        self.active = False

        # Windows constants
        self.ES_CONTINUOUS = 0x80000000
        self.ES_SYSTEM_REQUIRED = 0x00000001
        self.ES_DISPLAY_REQUIRED = 0x00000002

    def start(self):
        if self.active:
            return

        if self.platform == "darwin":
            self._start_macos()
        elif self.platform.startswith("win"):
            self._start_windows()
        elif self.platform.startswith("linux"):
            self._start_linux()

        self.active = True

    def stop(self):
        if not self.active:
            return

        if self.platform == "darwin":
            self._stop_macos()
        elif self.platform.startswith("win"):
            self._stop_windows()
        elif self.platform.startswith("linux"):
            self._stop_linux()

        self.active = False

    # -------- macOS --------
    def _start_macos(self):
        self.proc = subprocess.Popen(
            ["caffeinate", "-dims"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

    def _stop_macos(self):
        if self.proc:
            self.proc.terminate()
            self.proc = None

    # -------- Windows --------
    def _start_windows(self):
        ctypes.windll.kernel32.SetThreadExecutionState(
            self.ES_CONTINUOUS | self.ES_SYSTEM_REQUIRED | self.ES_DISPLAY_REQUIRED
        )

    def _stop_windows(self):
        ctypes.windll.kernel32.SetThreadExecutionState(self.ES_CONTINUOUS)

    # -------- Linux (X11 only) --------
    def _start_linux(self):
        if shutil.which("xset"):
            subprocess.call(["xset", "s", "off"])
            subprocess.call(["xset", "-dpms"])

    def _stop_linux(self):
        if shutil.which("xset"):
            subprocess.call(["xset", "s", "on"])
            subprocess.call(["xset", "+dpms"])


class GameNotImplementedException(Exception):
    pass


class CardWidget(QWidget):
    ASPECT_RATIO = 2.5 / 3.5
    MAX_WIDTH = 20
    MAX_HEIGHT = int(MAX_WIDTH / ASPECT_RATIO)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMaximumSize(self.MAX_WIDTH, self.MAX_HEIGHT)
        self.reset()

    def sizeHint(self):
        return QSize(self.MAX_WIDTH, self.MAX_HEIGHT)

    def minimumSizeHint(self):
        return QSize(20, int(20 / self.ASPECT_RATIO))

    def hasHeightForWidth(self):
        return True

    def heightForWidth(self, width):
        return int(width / self.ASPECT_RATIO)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Scale everything according to the current card width.
        corner_radius = self.width() * 0.20
        font_size = self.width() * 0.90

        # Card
        painter.setBrush(self._colour)
        painter.setPen(QtCore.Qt.GlobalColor.black)
        painter.drawRoundedRect(self.rect(), corner_radius, corner_radius)

        # Character
        if self._character:
            font = QFont("Arial")
            font.setPixelSize(int(font_size))
            font.setBold(True)
            painter.setFont(font)
            painter.setPen(QtCore.Qt.GlobalColor.black)

            painter.drawText(
                self.rect(), QtCore.Qt.AlignmentFlag.AlignCenter, self._character
            )

    def getColour(self):
        return self._colour

    def setColour(self, colour):
        if type(colour) == str:
            self._colour = QColor(colour)
        else:
            self._colour = colour
        self.update()

    def getChar(self):
        return self._character

    def setChar(self, character):
        self._character = character
        self.update()

    def reset(self, colour=None, char=None):
        self._colour = colour if colour else QColor("grey")
        self._character = str(char) if char else ""
        self.update()


class ToggleGroupBox(QGroupBox):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.current = 0
        self.screens = []
        self.widgetLayout = QStackedLayout(self)

    def addScreen(self, widget):
        self._install_event_filters(widget)
        self.screens.append(widget)
        self.widgetLayout.addWidget(widget)

    def _install_event_filters(self, widget):
        widget.installEventFilter(self)

        for child in widget.findChildren(QObject):
            child.installEventFilter(self)

    def eventFilter(self, watched, event):
        if (
            event.type() == QEvent.Type.MouseButtonPress
            and event.button() == QtCore.Qt.MouseButton.LeftButton
        ):
            self.toggle()
            return True

        return super().eventFilter(watched, event)

    def toggle(self):
        if len(self.screens) < 2:
            return
        self.current = (self.current + 1) % len(self.screens)
        self.widgetLayout.setCurrentIndex(self.current)
        # for i, screen in enumerate(self.screens):
        #     screen.setVisible(i == self.current)
