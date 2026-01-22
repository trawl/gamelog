#!/usr/bin/env python
# -*- coding: utf-8 -*-
import ctypes
import shutil
import subprocess
import sys

from PySide6 import QtCore, QtGui
from PySide6.QtCore import QCoreApplication
from PySide6.QtGui import QAction, QPainter
from PySide6.QtWidgets import (
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
    QTableWidget,
    QTabWidget,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from gui.clock import GameClock
from gui.gamestats import QuickStatsTW
from gui.playerlist import PlayerOrderDialog
from gui.plots import PlotView
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
        self.gameInput = self.createGameInputWidget(self)
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
        self.gameStatusLabel.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.gameStatusLabel.hide()
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
            self.dealerPolicyCheckBox.setStyleSheet("QCheckBox { font-weight: bold; }")
            # self.dealerPolicyCheckBox.stateChanged.connect(self.changeDealingPolicy)
            self.dealerPolicyCheckBox.toggled.connect(self.changeDealingPolicy)
            self.dealerPolicyCheckBox.setDisabled(self.engine.getNumRound() > 1)
            # self.dealerPolicyCheckBox.setSizePolicy(
            #     QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed
            # )
            self.dealerPolicyCheckBox.setSizePolicy(
                QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Maximum
            )
            self.dealerPolicyCheckBox.setStyleSheet("""
                QPushButton {
                    border: 2px solid #888;
                    border-radius: 6px;
                    padding: 6px 6px;
                    background: transparent;
                    color: white;
                }

                /* Checked (enabled) */
                QPushButton:checked:enabled {
                    background: #888;
                }

                /* Unchecked (enabled) */
                QPushButton:!checked:enabled {
                    background: transparent;
                }

                /* Disabled but checked */
                QPushButton:checked:disabled {
                    background: #666;
                    border-color: #666;
                }

                /* Disabled and unchecked */
                QPushButton:disabled:!checked {
                    border-color: #555;
                }
                """)
            self.matchGroupLayout.addWidget(
                self.dealerPolicyCheckBox,
                # alignment=QtCore.Qt.AlignmentFlag.AlignHCenter,
            )

    def retranslateUI(self):
        self.setRoundTitle()
        # self.matchGroup.setTitle(self.tr("Game Time"))
        self.pauseMatchButton.setText(self.tr("&Pause/Play"))
        self.cancelMatchButton.setText(self.tr("&Cancel Match"))
        self.restartMatchButton.setText(self.tr("Restart &Match"))
        self.commitRoundButton.setText(self.tr("Commit &Round"))
        self.playerOrderButton.setText(self.tr("Player &Order"))
        if self.engine.getDealingPolicy() not in (
            self.engine.NoDealer,
            self.engine.StarterDealer,
        ):
            self.changeDealingPolicy()
        self.updateGameStatusLabel()

    def createGameInputWidget(self, parent=None):
        return GameInputWidget(self.engine, parent)

    def createRoundsDetail(self, parent=None):
        return GameRoundsDetail(self.engine, parent)

    def updateGameStatusLabel(self):
        self.gameStatusLabel.setStyleSheet(
            "QLabel { font-size: 16px; font-weight:bold; color: red;}"
        )
        winner = self.engine.getWinner()
        if winner:
            self.gameStatusLabel.show()
            self.gameStatusLabel.setText(self.tr("{} won this match!").format(winner))
        elif self.engine.isPaused():
            self.gameStatusLabel.setText(self.tr("Game is paused"))
            self.gameStatusLabel.show()
        else:
            self.gameStatusLabel.setText(self.tr(""))
            self.gameStatusLabel.hide()

    def cancelMatch(self):
        if not self.isFinished():
            tit = self.tr("Cancel Match")
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
            msg = self.tr("No winner selected")
            QMessageBox.warning(self, self.game, msg)

            return
        else:
            self.engine.setRoundWinner(winner)
        scores = self.gameInput.getScores()
        for player, score in scores.items():
            if not self.checkPlayerScore(player, score):
                msg = self.tr("{} score is not valid").format(player)
                QMessageBox.warning(self, self.game, msg)
                return
            extras = self.getPlayerExtraInfo(player)
            if extras is None:
                return
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

    def checkPlayerScore(self, player, score):
        if score >= 0:
            return True
        else:
            return False

    def setRoundTitle(self):
        try:
            nround = self.engine.getNumRound()
            # self.roundGroup.setTitle(self.tr("Round {0}").format(str(nround)))
            self.roundTitleLabel.setText(
                self.tr("{} - Round {}").format(self.engine.getGame(), str(nround))
            )
        except AttributeError:
            self.roundTitleLabel.setText(self.engine.getGame())

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
        pass

    def setDealer(self):
        pass

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
        if not on:
            self.screen_blocker.start()
            print("Enabled Screensaver")
        else:
            self.screen_blocker.stop()
            print("Disabled Screensaver")


class GameInputWidget(QWidget):
    enterPressed = QtCore.Signal()

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
        if event.key() in (QtCore.Qt.Key.Key_Return, QtCore.Qt.Key.Key_Enter):
            self.enterPressed.emit()
            event.accept()
        return super(GameInputWidget, self).keyPressEvent(event)

    def mousePressEvent(self, event):
        self.setFocus()
        return QWidget.mousePressEvent(self, event)

    def updatePlayerOrder(self):
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
    valueChanged = QtCore.Signal(int)
    spacePressed = QtCore.Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._value = 0
        self._minimum = 0
        self._maximum = 200
        self._step = 1
        self._hideMinimum = True
        self.pcolour = QtGui.QColor(255, 255, 255)
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

        self.up_button = QToolButton()
        self.down_button = QToolButton()
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
                border-radius: 6px;
                border: 1px solid #555555 ;
                background: transparent;
                color:rgb({0},{1},{2});
            }}
            QLineEdit:focus {{
                border: 2px solid rgb({0},{1},{2}) ;   /* highlight color */
            }}
        """
        self._updateStyle()

        self.up_button.setStyleSheet(self._button_style())
        self.down_button.setStyleSheet(self._button_style())

        # ---- Connections ----
        self.up_button.clicked.connect(self.step_up)
        self.down_button.clicked.connect(self.step_down)
        self.line_edit.editingFinished.connect(self._commit_text)
        self.line_edit.textChanged.connect(self.textChangedAction)

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
            color: #ffffff;              /* arrow color */
            background-color: #333333;  /* dark background */
            border: 1px solid #555555;
            border-radius: 6px;
        }
        QToolButton:hover {
            background-color: #444444;
        }
        QToolButton:pressed {
            background-color: #555555;
        }
        QToolButton:disabled {
            background-color: #222222;
            color: #777777;
            border-color: #444444;
        }
        """

    def setHideMinimum(self, hidemin):
        self._hideMinimum = hidemin

    def setColour(self, colour):
        self.pcolour = colour
        self._updateStyle()

    def _updateStyle(self):
        self.line_edit.setStyleSheet(
            self._text_css.format(
                self.pcolour.red(), self.pcolour.green(), self.pcolour.blue()
            )
        )

    def value(self):
        return self._value

    def setValue(self, value: int):
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

    def _snap_to_step(self, value: int) -> int:
        if self._step > 1:
            offset = value - self._minimum
            value = self._minimum + (offset // self._step) * self._step
        return value

    def step_up(self):
        self.line_edit.setFocus()
        self.setValue(self._value + self._step)

    def step_down(self):
        self.line_edit.setFocus()
        self.setValue(self._value - self._step)

    def _commit_text(self):
        try:
            value = int(self.line_edit.text())
        except ValueError:
            value = self._value

        self.setValue(self._snap_to_step(value))

    def setRange(self, minimum: int, maximum: int):
        self._minimum = minimum
        self._maximum = maximum
        self.setValue(self._value)

    def setMinimum(self, minimum: int):
        self.setRange(minimum, self._maximum)

    def setMaximum(self, maximum: int):
        self.setRange(self._minimum, maximum)

    def setSingleStep(self, step: int):
        self._step = max(1, step)

    def clear(self):
        self.line_edit.clear()

    def setReadOnly(self, ro):
        self.line_edit.setReadOnly(ro)
        self.up_button.setDisabled(ro)
        self.down_button.setDisabled(ro)

    def lineEdit(self):
        return self.line_edit

    def _update_buttons(self):
        if not self.line_edit.isReadOnly():
            self.up_button.setEnabled(self._value < self._maximum)
            self.down_button.setEnabled(self._value > self._minimum)

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
            self.setValue(self._minimum)


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


class GamePlayerWidget(QGroupBox):
    def __init__(self, nick, colour=QtGui.QColor(), parent=None):
        super(GamePlayerWidget, self).__init__(parent)
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

        self.dealerPixmap = QtGui.QPixmap("icons/cards.png")
        self.nonDealerPixmap = QtGui.QPixmap()
        self.winnerPixmap = QtGui.QPixmap("icons/winner.png")

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


class GameRoundsDetail(QGroupBox):
    edited = QtCore.Signal()

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
        self.container.addTab(self.tableContainer, "")

        self.table = self.createRoundTable(self.engine, self)
        self.tableContainerLayout.addWidget(self.table, stretch=1)
        self.table.edited.connect(self.updateRound)
        self.table.edited.connect(self.edited.emit)

        self.plot = self.createRoundPlot(self.engine, self)
        self.plot.setAutoFillBackground(True)
        #        self.container.addItem(self.plot,'')
        self.container.addTab(self.plot, "")

        self.statsFrame = QWidget(self)
        self.statsFrame.setAutoFillBackground(True)
        self.container.addTab(self.statsFrame, "")

        self.statsLayout = QVBoxLayout(self.statsFrame)
        self.gamestats = self.createQSBox()
        self.statsLayout.addWidget(self.gamestats)

    def retranslateUI(self):
        # self.setTitle(i18n("GameRoundsDetail",'Details'))
        self.container.setTabText(0, self.tr("Table"))
        self.container.setTabText(1, self.tr("Plot"))
        self.container.setTabText(2, self.tr("Statistics"))
        #        self.container.setItemText(0,i18n(
        #       "CarcassonneEntriesDetail","Table"))
        #        self.container.setItemText(1,i18n(
        #       "CarcassonneEntriesDetail","Plot"))
        #        self.container.setItemText(2,i18n(
        #       "CarcassonneEntriesDetail","Statistics"))
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
        except Exception:
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
        super(GameRoundTable, self).__init__(parent)
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
        ic = QtGui.QIcon("icons/delete.png")
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
        self.canvas.viewport().repaint()

    def retranslateUI(self):
        self.retranslatePlot()

    def isPlotInited(self):
        return self.plotinited

    def updatePlot(self):
        pass

    def retranslatePlot(self):
        pass


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
