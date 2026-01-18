#!/usr/bin/env python
# -*- coding: utf-8 -*-

import re
from typing import cast

from PySide6 import QtCore, QtGui
from PySide6.QtCore import QCoreApplication
from PySide6.QtWidgets import (
    QCheckBox,
    QFrame,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLCDNumber,
    QPushButton,
    QSizePolicy,
    QSpinBox,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from controllers.phase10engine import Phase10Engine, Phase10MasterEngine
from gui.game import (
    GameInputWidget,
    GamePlayerWidget,
    GameRoundPlot,
    GameRoundsDetail,
    GameRoundTable,
    GameWidget,
    PlayerColours,
)
from gui.gamestats import GeneralQuickStats, ParticularQuickStats, QuickStatsTW
from gui.plots import PlotView


def getPhaseNames(phasecodes):
    types = {
        "s": {
            "2": [
                QCoreApplication.translate("Phase10Widget", "pair"),
                QCoreApplication.translate("Phase10Widget", "pairs"),
            ],
            "3": [
                QCoreApplication.translate(
                    "Phase10Widget", "three of a kind", "singular"
                ),
                QCoreApplication.translate(
                    "Phase10Widget", "three of a kind", "plural"
                ),
            ],
            "4": [
                QCoreApplication.translate(
                    "Phase10Widget", "four of a kind", "singular"
                ),
                QCoreApplication.translate("Phase10Widget", "four of a kind", "plural"),
            ],
            "5": [
                QCoreApplication.translate(
                    "Phase10Widget", "five of a kind", "singular"
                ),
                QCoreApplication.translate("Phase10Widget", "five of a kind", "plural"),
            ],
        },
        "c": QCoreApplication.translate("Phase10Widget", "cards of the same colour"),
        "r": [
            QCoreApplication.translate("Phase10Widget", "run of"),
            QCoreApplication.translate("Phase10Widget", "runs of"),
        ],
        "cr": [
            QCoreApplication.translate("Phase10Widget", "colour run of"),
            QCoreApplication.translate("Phase10Widget", "colour runs of"),
        ],
    }
    phases = []
    for code in phasecodes:
        first = True
        phase = ""
        for part in code.split():
            m = re.match(r"(\d)([src]|cr)(\d)", part)
            if m:
                n, tcode, cards = m.groups()
                if int(n) > 1:
                    plural = 1
                else:
                    plural = 0
                if not first:
                    phase += " + "
                first = False
                if tcode == "s":
                    phase += "{} {}".format(n, types[tcode][cards][plural])
                elif tcode == "c":
                    phase += "{} {}".format(cards, types[tcode])
                elif tcode in ["r", "cr"]:
                    phase += "{} {} {}".format(n, types[tcode][plural], cards)
        phases.append(phase)
    return phases


class Phase10Widget(GameWidget):
    def createEngine(self):
        if self.game == "Phase10Master":
            self.engine = Phase10MasterEngine()
        elif self.game == "Phase10":
            self.engine = Phase10Engine()
        else:
            raise Exception("No engine for game {}".format(self.game))

    def initUI(self):
        super(Phase10Widget, self).initUI()
        self.hideInputOnFinish = False
        self.roundTitleLabel.hide()
        self.phasesInOrderCheckBox = QCheckBox(self.matchGroup)
        self.phasesInOrderCheckBox.setChecked(self.engine.getPhasesInOrderFlag())
        self.phasesInOrderCheckBox.setStyleSheet("QCheckBox { font-weight: bold; }")
        self.phasesInOrderCheckBox.setDisabled(self.engine.getNumRound() > 1)
        self.phasesInOrderCheckBox.stateChanged.connect(self.phasesInOrderChanged)
        self.matchGroupLayout.addWidget(self.phasesInOrderCheckBox)

        self.gameInput = Phase10InputWidget(self.engine, self)
        self.gameInput.setAutoFillBackground(True)
        self.phasesInOrderCheckBox.toggled.connect(self.gameInput.switchPhasesInOrder)
        self.gameInput.enterPressed.connect(self.commitRound)

        self.details = Phase10RoundsDetail(self.engine, self.gameInput, self)
        self.details.edited.connect(self.updatePanel)
        # self.widgetLayout.addWidget(self.details, 1, 0)
        self.leftLayout.addWidget(self.details)

        self.extraGroup = QGroupBox(self)
        self.extraGroup.setSizePolicy(
            QSizePolicy.Policy.Preferred, QSizePolicy.Policy.MinimumExpanding
        )
        self.extraGroup.setStyleSheet(
            "QGroupBox { font-size: 18px; font-weight: bold; }"
        )
        # self.widgetLayout.addWidget(self.extraGroup, 1, 1)
        self.rightLayout.addWidget(self.extraGroup)
        self.extraGroupLayout = QVBoxLayout(self.extraGroup)

        self.phaseLabels = []
        for _ in range(len(self.engine.getPhases())):
            self.extraGroupLayout.addSpacing(10)
            label = QLabel(self)
            label.setStyleSheet("QLabel {font-weight: bold; }")
            #             label.setScaledContents(True)
            self.phaseLabels.append(label)
            self.extraGroupLayout.addWidget(label)

        self.setDealer()
        self.retranslateUI()

    def retranslateUI(self):
        super(Phase10Widget, self).retranslateUI()
        self.phasesInOrderCheckBox.setText(self.tr("Phases in order"))
        self.gameInput.retranslateUI()
        self.extraGroup.setTitle(self.tr("Phases"))
        self.details.retranslateUI()
        phaselabels = zip(getPhaseNames(self.engine.getPhases()), self.phaseLabels)
        for number, (phase, label) in enumerate(phaselabels, start=1):
            label.setText(f"{number} : {phase}")

    def checkPlayerScore(self, player, score):
        return super(Phase10Widget, self).checkPlayerScore(self, score) and not (
            score % 5 != 0
            or (score < 50 and not self.gameInput.hasPlayerCleared(player))
        )

    def getPlayerExtraInfo(self, player):
        cleared = self.gameInput.hasPlayerCleared(player)
        a_phase = self.gameInput.getPlayerAimedPhase(player)
        if a_phase:
            return {"aimedPhase": a_phase, "isCompleted": cleared}
        else:
            return {}

    def changeDealingPolicy(self, *args, **kwargs):
        if self.dealerPolicyCheckBox.isChecked():
            self.engine.setDealingPolicy(self.engine.WinnerDealer)
        else:
            self.engine.setDealingPolicy(self.engine.RRDealer)

    def updatePanel(self):
        super(Phase10Widget, self).updatePanel()
        self.phasesInOrderCheckBox.setEnabled(False)
        self.dealerPolicyCheckBox.setEnabled(False)
        self.gameInput.updatePanel()
        self.details.updateRound()
        if self.engine.getWinner():
            self.details.updateStats()

    def unsetDealer(self):
        self.gameInput.unsetDealer()

    def setDealer(self):
        self.gameInput.setDealer()

    def setWinner(self):
        super(Phase10Widget, self).setWinner()
        self.gameInput.setEnabled(True)
        self.gameInput.setWinner()

    def phasesInOrderChanged(self, state):
        if state == QtCore.Qt.CheckState.Unchecked:
            self.engine.setPhasesInOrderFlag(False)
        elif state == QtCore.Qt.CheckState.Checked:
            self.engine.setPhasesInOrderFlag(True)
        self.gameInput.updatePanel()

    def updatePlayerOrder(self):
        GameWidget.updatePlayerOrder(self)
        self.details.updatePlayerOrder()


class Phase10InputWidget(GameInputWidget):
    def __init__(self, engine, parent=None):
        super(Phase10InputWidget, self).__init__(engine, parent)
        self.initUI()

    def initUI(self):
        players = self.engine.getListPlayers()
        if len(players) >= 4:
            players_grid = True
            self.widgetLayout = QGridLayout(self)
        else:
            players_grid = False
            self.widgetLayout = QVBoxLayout(self)

        for np, player in enumerate(players):
            self.playerInputList[player] = Phase10PlayerWidget(
                player, self.engine, self
            )
            self.playerInputList[player].roundWinnerSet.connect(self.changedWinner)
            if players_grid:
                cast("QGridLayout", self.widgetLayout).addWidget(
                    self.playerInputList[player], np // 2, np % 2
                )
            else:
                cast("QVBoxLayout", self.widgetLayout).addWidget(
                    self.playerInputList[player]
                )

    def changedWinner(self, winner):
        super().changedWinner(winner)
        for player, piw in self.playerInputList.items():
            if player != winner and piw.getScore() == 0:
                piw.setScore(5)

    def retranslateUI(self):
        for piw in self.playerInputList.values():
            piw.retranslateUI()

    def switchPhasesInOrder(self, in_order):
        for player in self.engine.getListPlayers():
            self.playerInputList[player].switchPhasesInOrder(in_order)

    def hasPlayerCleared(self, player):
        return self.playerInputList[player].isRoundCleared()

    def getPlayerAimedPhase(self, player):
        return self.playerInputList[player].getRoundPhase()

    def updatePanel(self):
        for player in self.engine.getListPlayers():
            score = self.engine.getScoreFromPlayer(player)
            completed = self.engine.getCompletedPhasesFromPlayer(player)
            remaining = self.engine.getRemainingPhasesFromPlayer(player)
            self.playerInputList[player].updatePhase10Display(
                score, completed, remaining
            )

    def unsetDealer(self):
        self.playerInputList[self.engine.getDealer()].unsetDealer()

    def setDealer(self):
        self.playerInputList[self.engine.getDealer()].setDealer()

    def setWinner(self):
        winner = self.engine.getWinner()
        if winner in self.engine.getListPlayers():
            self.playerInputList[winner].setWinner()
            for pi in self.playerInputList.values():
                pi.finish()

    def getWinner(self):
        for player, piw in self.playerInputList.items():
            if piw.isRoundWinner():
                return player
        return None

    def updatePlayerOrder(self):
        trash = QWidget()
        current_layout = self.layout()
        if current_layout is not None:
            trash.setLayout(current_layout)
        players = self.engine.getListPlayers()
        if len(players) >= 4:
            players_grid = True
            self.widgetLayout = QGridLayout(self)
        else:
            players_grid = False
            self.widgetLayout = QVBoxLayout(self)

        trash_layout = trash.layout()
        for i, player in enumerate(self.engine.getListPlayers()):
            if trash_layout is not None:
                trash_layout.removeWidget(self.playerInputList[player])
            if players_grid:
                cast("QGridLayout", self.widgetLayout).addWidget(
                    self.playerInputList[player], i // 2, i % 2
                )
            else:
                cast("QVBoxLayout", self.widgetLayout).addWidget(
                    self.playerInputList[player]
                )
            self.playerInputList[player].setColour(PlayerColours[i])

    def mousePressEvent(self, event):
        return QWidget.mousePressEvent(self, event)


class Phase10ScoreSpinBox(QSpinBox):
    def __init__(self, parent=None):
        super(Phase10ScoreSpinBox, self).__init__(parent)
        self.setSingleStep(5)
        self.setRange(0, 200)
        self.setValue(5)
        # self.clear()
        self.fixed = False
        self.setSizePolicy(
            QSizePolicy.Policy.Fixed, QSizePolicy.Policy.MinimumExpanding
        )
        self.setFixedWidth(60)
        self.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.setValidDisplay()

    def validate(self, text, pos):
        # self.valueChanged.emit(self.value())
        res = QtGui.QValidator.State.Acceptable
        if text == "":
            res = QtGui.QValidator.State.Intermediate
        else:
            try:
                score = int(text)
                self.setValidDisplay()
                if score % 5 != 0:
                    res = QtGui.QValidator.State.Intermediate
            except ValueError:
                res = QtGui.QValidator.State.Invalid
        return (res, text, pos)

    def fixup(self, inp: str):
        if not inp:
            return "-5"
        if not self.hasAcceptableInput():
            newvalue = round(int(inp) / 5) * 5
            self.setValue(newvalue)
            self.fixed = True
            return str(newvalue)
        return inp

    def setDisabled(self, disable):
        if disable:
            self.clear()
        else:
            self.setValue(5)
        self.setValidDisplay()
        super(Phase10ScoreSpinBox, self).setDisabled(disable)

    def setEnabled(self, enable):
        self.setDisabled(not enable)

    def setValidDisplay(self):
        sh = "font-size: 24px; font-weight: bold;"
        sh = """
        QSpinBox {{ padding-top: 30px; padding-bottom: 30px; {} }}
        QSpinBox::up-button  {{subcontrol-origin: margin;
                               subcontrol-position: top; min-width: 60px;
                               max-width:100px; height: 30px; }}
        QSpinBox::down-button  {{subcontrol-origin: margin;
                                 subcontrol-position: bottom; min-width: 60px;
                                 max-width:100px; height: 30px; }}
        """.format(sh)
        self.setStyleSheet(sh)


class Phase10PlayerWidget(GamePlayerWidget):
    roundWinnerSet = QtCore.Signal(str)
    playerScoreChanged = QtCore.Signal()

    def __init__(self, nick, engine, parent=None):
        self.engine = engine
        self.current_phase = min(self.engine.getRemainingPhasesFromPlayer(nick))
        self.phases_in_order = self.engine.getPhasesInOrderFlag()
        super(Phase10PlayerWidget, self).__init__(
            nick, PlayerColours[self.engine.getListPlayers().index(nick)], parent
        )

    def initUI(self):
        self.setTitle(self.player)
        super(Phase10PlayerWidget, self).initUI()

        trashWidget = QWidget()
        trashWidget.setLayout(self.mainLayout)

        self.mainLayout = QVBoxLayout(self)
        self.mainLayout.addStretch()
        self.upperLayout = QHBoxLayout()
        self.mainLayout.addLayout(self.upperLayout)
        self.upperLayout.addStretch()
        self.phaseNameLabel = QLabel(self)
        css = "font-weight: bold; font-size: 24px; color:rgb({},{},{});"
        self.phaseNameLabel.setStyleSheet(
            css.format(self.pcolour.red(), self.pcolour.green(), self.pcolour.blue())
        )
        self.updatePhaseName()
        self.upperLayout.addWidget(self.phaseNameLabel)
        self.upperLayout.addStretch()
        self.lowerLayout = QHBoxLayout()
        self.mainLayout.addLayout(self.lowerLayout)
        self.mainLayout.addStretch()

        self.phaseLabelsLayout = QGridLayout()
        self.phaseLabelsLayout.setSpacing(5)

        self.scoreLCD = QLCDNumber(self)
        self.scoreLCD.setSegmentStyle(QLCDNumber.SegmentStyle.Flat)
        self.mainLayout.addWidget(self.scoreLCD)
        self.scoreLCD.setDigitCount(3)
        self.scoreLCD.setMinimumWidth(100)
        self.scoreLCD.setFrameStyle(QFrame.Shape.NoFrame)
        css = "QLCDNumber {{ color:rgb({},{},{});}}"
        self.scoreLCD.setStyleSheet(
            css.format(self.pcolour.red(), self.pcolour.green(), self.pcolour.blue())
        )

        self.lowerLayout.addWidget(self.scoreLCD)
        self.lowerLayout.addLayout(self.phaseLabelsLayout)

        self.scoreLCD.display(self.engine.getScoreFromPlayer(self.player))

        # Middle part - Phase list
        self.phaseLabels = list()
        for phase in range(1, 11):
            label = Phase10Label(phase, self)
            if phase == self.current_phase:
                label.setCurrent()
            elif self.engine.hasPhaseCompleted(self.player, phase):
                label.setPassed()
            self.phaseLabels.append(label)
            self.phaseLabelsLayout.addWidget(
                label, int((phase - 1) / 5), int((phase - 1) % 5), 1, 1
            )

        # Middle part - Inputs
        self.roundScore = Phase10ScoreSpinBox(self)
        self.roundScore.setMaximumWidth(90)
        self.roundScore.valueChanged.connect(self.updateRoundPhaseCleared)
        self.lowerLayout.addWidget(self.roundScore)

        self.roundPhaseClearedCheckbox = Phase10ClearedCheckBox(self)
        self.roundPhaseClearedCheckbox.setChecked(True)
        self.roundPhaseClearedCheckbox.setEnabled(False)
        self.roundPhaseClearedCheckbox.setMinimumSize(40, 40)
        self.lowerLayout.addWidget(self.roundPhaseClearedCheckbox)

        self.retranslateUI()

    def retranslateUI(self):
        # self.roundWinnerRadioButton.setText(self.tr("Winner"))
        # self.roundPhaseClearedCheckbox.setText(self.tr("Completed"))
        self.updatePhaseName()

    def updatePhase10Display(self, points, completed_phases, remaining_phases):
        if points >= 1000:
            self.scoreLCD.setDigitCount(4)
        self.scoreLCD.display(points)
        self.roundScore.setValue(5)
        self.roundPhaseClearedCheckbox.setChecked(True)
        if len(remaining_phases) == 0:
            self.current_phase = 0
            self.roundScore.clear()
        else:
            self.current_phase = min(remaining_phases)
        self.roundPhaseClearedCheckbox.setEnabled(False)

        for phase, label in enumerate(self.phaseLabels, start=1):
            if phase == self.current_phase and not self.engine.getWinner():
                if not label.isCurrent():
                    label.setCurrent()
            elif phase in completed_phases:
                if not label.isPassed():
                    label.setPassed()
            else:
                if not label.isRemaining():
                    label.setRemaining()
        self.updatePhaseName()

    def getScore(self):
        if self.isRoundWinner():
            return 0
        try:
            return int(self.roundScore.value())
        except Exception:
            return -1

    def setScore(self, score):
        self.roundScore.setValue(score)

    def switchPhasesInOrder(self, in_order):
        self.phases_in_order = in_order
        if not self.phases_in_order:
            return
        self.phaseLabels[self.current_phase - 1].setRemaining()
        for label in self.phaseLabels:
            if label.isRemaining():
                label.setCurrent()
                self.current_phase = label.getNumber()
                break

    def updatePhaseSelected(self, phaselabel):
        if phaselabel.isRemaining():
            self.current_phase = phaselabel.getNumber()
            for label in self.phaseLabels:
                if label.isCurrent():
                    label.setRemaining()
            phaselabel.setCurrent()
        self.updatePhaseName()

    def updatePhaseName(self):
        phasenames = getPhaseNames(self.engine.getPhases())
        self.phaseNameLabel.setText(phasenames[self.current_phase - 1])

    def updateRoundPhaseCleared(self, score):
        try:
            score = int(score)
        except Exception:
            self.roundPhaseClearedCheckbox.setChecked(False)
            return

        if score < 0:
            self.roundPhaseClearedCheckbox.setChecked(False)
            return

        if score % 5 != 0:
            return

        if score >= 50:
            self.roundPhaseClearedCheckbox.setEnabled(True)
            self.roundPhaseClearedCheckbox.setChecked(False)
        elif score == 0:
            self.roundPhaseClearedCheckbox.setChecked(True)
            self.roundPhaseClearedCheckbox.setEnabled(False)
            self.roundWinnerSet.emit(self.player)
        else:
            self.roundPhaseClearedCheckbox.setChecked(True)
            self.roundPhaseClearedCheckbox.setEnabled(False)

    def mousePressEvent(self, event):
        child = self.childAt(event.pos())
        if child is None:
            self.roundScore.setFocus()
        elif isinstance(child, Phase10Label) and not self.phases_in_order:
            self.updatePhaseSelected(child)
        return QGroupBox.mousePressEvent(self, event)

    #

    def isRoundWinner(self):
        return self.roundScore.value() == 0

    def getRoundPhase(self):
        return self.current_phase

    def isRoundCleared(self):
        return self.roundPhaseClearedCheckbox.isChecked()

    def roundWinnerSetAction(self, isset):
        self.roundPhaseClearedCheckbox.setChecked(True)
        if isset:
            self.roundWinnerSet.emit(self.player)
            self.roundScore.setValue(0)
        else:
            self.roundScore.setValue(5)

    def reset(self):
        pass

    def finish(self):
        self.roundPhaseClearedCheckbox.setDisabled(True)
        self.roundScore.setDisabled(True)


class Phase10ClearedCheckBox(QPushButton):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setCheckable(True)
        self.setSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self._checked_text = "✓"
        self._unchecked_text = "✕"

        self._update_text()
        # Update text automatically when state changes
        self.toggled.connect(self._update_text)

    def setChecked(self, checked):
        super().setChecked(checked)
        self._update_text()

    def _update_text(self, _=None):
        if self.isChecked():
            self.setText(self._checked_text)
            self.setStyleSheet("""
            QPushButton {
                border: 2px solid green;
                border-radius: 6px;
                background: green;
                font-size: 26px;
                font-weight: bold;
            }
            """)
        else:
            self.setText(self._unchecked_text)
            self.setStyleSheet("""
            QPushButton {
                border: 2px solid red;
                border-radius: 6px;
                background: red;
                font-size: 26px;
                font-weight: bold;
            }
            """)


class Phase10Label(QLabel):
    def __init__(self, number, parent=None):
        super(Phase10Label, self).__init__(parent)
        # self.setText(str(number).zfill(2))
        self.setText(str(number))
        self.setAutoFillBackground(False)
        self.setRemaining()
        self.setFrameShape(QFrame.Shape.StyledPanel)
        #         self.setFrameShadow(QFrame.Raised)
        self.setScaledContents(True)
        self.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.setWordWrap(False)
        self.setMinimumSize(20, 20)
        self.setSizePolicy(
            QSizePolicy.Policy.MinimumExpanding, QSizePolicy.Policy.MinimumExpanding
        )
        #         self.setFixedSize(QtCore.QSize(40,40))
        self.number = number

    def isPassed(self):
        return self.state == 1

    def isCurrent(self):
        return self.state == 2

    def isRemaining(self):
        return self.state == 0

    def setPassed(self):
        self.state = 1
        css = "QLabel { background-color: green;font-weight: bold; color:white; border-radius: 6px }"
        self.setStyleSheet(css)

    def setCurrent(self):
        self.state = 2
        css = "QLabel { background-color: orange; font-weight: bold; color:white; border-radius: 6px  }"
        self.setStyleSheet(css)

    def setRemaining(self):
        self.state = 0
        css = "QLabel { background-color: red; font-weight: bold; color:white; border-radius: 6px  }"
        self.setStyleSheet(css)

    def getNumber(self):
        return self.number


class Phase10RoundsDetail(GameRoundsDetail):
    def __init__(self, engine, iw, parent=None):
        self.iw = iw
        super(Phase10RoundsDetail, self).__init__(engine, parent)

    def initUI(self):
        super(Phase10RoundsDetail, self).initUI()
        self.container.insertTab(0, self.iw, "")
        self.container.setCurrentIndex(0)

    def retranslateUI(self):
        #         self.setTitle(i18n("GameRoundsDetail",'Details'))
        self.container.setTabText(0, self.tr("Score"))
        self.container.setTabText(1, self.tr("Table"))
        self.container.setTabText(2, self.tr("Plot"))
        self.container.setTabText(3, self.tr("Statistics"))
        self.gamestats.retranslateUI()
        self.plot.retranslateUI()
        self.updateRound()

    def createRoundTable(self, engine, parent=None):
        return Phase10RoundTable(self.engine, parent)

    def createRoundPlot(self, engine, parent=None):
        return Phase10RoundPlot(self.engine, self)

    def createQSBox(self, parent=None):
        return Phase10QSTW(self.engine.getGame(), self.engine.getListPlayers(), self)


class Phase10RoundTable(GameRoundTable):
    def insertRound(self, r):
        winner = r.getWinner()
        i = r.getNumRound() - 1
        self.insertRow(i)
        for j, player in enumerate(self.engine.getListPlayers()):
            item = QTableWidgetItem()
            item.setFlags(item.flags() ^ QtCore.Qt.ItemFlag.ItemIsEditable)
            item.setTextAlignment(
                QtCore.Qt.AlignmentFlag.AlignVCenter
                | QtCore.Qt.AlignmentFlag.AlignCenter
            )
            if player == winner:
                text = self.tr("Winner")
                font = item.font()
                font.setBold(True)
                item.setFont(font)
            else:
                text = str(r.getPlayerScore(player))
            a_phase = r.getPlayerAimedPhase(player)
            c_phase = r.getPlayerCompletedPhase(player)
            text += self.tr(" (Phase {})").format(a_phase)
            if c_phase != 0:
                background = 0xCCFF99  # green
            else:
                background = 0xFFCC99  # red
            item.setBackground(QtGui.QBrush(QtGui.QColor(background)))
            item.setForeground(QtGui.QBrush(QtGui.QColor(0, 0, 0)))
            item.setText(text)
            self.setItem(i, j, item)
        self.scrollToBottom()


class Phase10RoundPlot(GameRoundPlot):
    def initUI(self):
        super(Phase10RoundPlot, self).initUI()
        # self.setStyleSheet("QLabel {font-size: 18px; }")
        current_layout = self.layout()
        if current_layout is not None:
            QWidget().setLayout(current_layout)
        self.widgetLayout = QVBoxLayout()
        self.setLayout(self.widgetLayout)

        self.plotsLayout = QGridLayout()
        self.widgetLayout.addLayout(self.plotsLayout)

        self.phasesLabel = QLabel("", self)
        self.plotsLayout.addWidget(self.phasesLabel, 0, 0)
        self.scoreLabel = QLabel("", self)
        self.plotsLayout.addWidget(self.scoreLabel, 0, 1)

        self.canvas = PlotView(PlayerColours, self)
        self.canvas.setBackground(self.palette().color(self.backgroundRole()))
        self.canvas.addLinePlot()
        self.plotsLayout.addWidget(self.canvas, 1, 0)
        self.scorecanvas = PlotView(PlayerColours, self)
        self.scorecanvas.setBackground(self.palette().color(self.backgroundRole()))
        self.scorecanvas.addLinePlot()
        self.plotsLayout.addWidget(self.scorecanvas, 1, 1)

        self.playersListLayout = QHBoxLayout()
        self.widgetLayout.addLayout(self.playersListLayout)
        self.playersListLayout.addStretch()

        for i, player in enumerate(self.engine.getListPlayers()):
            colour = PlayerColours[i]
            label = QLabel(player)
            css = "QLabel {{ font-size: 28px; font-weight: bold; color:rgb({},{},{});}}"
            label.setStyleSheet(css.format(colour.red(), colour.green(), colour.blue()))
            self.playersListLayout.addWidget(label)
            self.playersListLayout.addStretch()

        self.retranslatePlot()
        self.updatePlot()

    def retranslatePlot(self):
        super(Phase10RoundPlot, self).retranslatePlot()
        self.phasesLabel.setText(self.tr("Phases"))
        self.scoreLabel.setText(self.tr("Scores"))

    #         self.playersTitleLabel.setText(i18n("Phase10RoundPlot",'Players') )

    def updatePlot(self):
        super(Phase10RoundPlot, self).updatePlot()
        if not self.isPlotInited():
            return
        scores = {}
        phases = {}
        for player in self.engine.getPlayers():
            scores[player] = [0]
            phases[player] = [0]

        for rnd in self.engine.getRounds():
            for player in self.engine.getPlayers():
                if player not in scores:
                    scores[player] = [0]
                rndscore = rnd.getPlayerScore(player)
                if rndscore >= 0:
                    accumscore = scores[player][-1] + rndscore
                    scores[player].append(accumscore)
                c_phase = rnd.getPlayerCompletedPhase(player)
                if c_phase > 0:
                    phases[player].append(phases[player][-1] + 1)
                else:
                    phases[player].append(phases[player][-1])

        self.canvas.clearPlotContents()
        self.scorecanvas.clearPlotContents()

        for player in self.engine.getListPlayers():
            self.canvas.addSeries(phases[player], player)
            self.scorecanvas.addSeries(scores[player], player)
        roundNames = self.getRoundNames()
        self.canvas.addHHeaders(roundNames)
        self.scorecanvas.addHHeaders(roundNames)
        self.updatePlayerOrder()

    def getRoundNames(self):
        return list(
            range(
                1,
                10
                + self.engine.getNumRound()
                - max(
                    len(self.engine.getCompletedPhasesFromPlayer(player))
                    for player in self.engine.getPlayers()
                ),
            )
        )

    def updatePlayerOrder(self):
        trash = QWidget()
        self.widgetLayout.removeItem(self.playersListLayout)
        trash.setLayout(self.playersListLayout)
        self.playersListLayout = QHBoxLayout()
        self.widgetLayout.addLayout(self.playersListLayout)

        self.playersListLayout.addStretch()

        for i, player in enumerate(self.engine.getListPlayers()):
            colour = PlayerColours[i]
            label = QLabel(player)
            css = "QLabel {{ font-size: 28px; font-weight: bold; color:rgb({},{},{});}}"
            label.setStyleSheet(css.format(colour.red(), colour.green(), colour.blue()))
            self.playersListLayout.addWidget(label)

            self.playersListLayout.addStretch()


class Phase10QSTW(QuickStatsTW):
    def initStatsWidgets(self):
        self.gs = Phase10QSBox(self.game, self)
        self.ps = Phase10PQSBox(self.game, self)


class Phase10QSBox(GeneralQuickStats):
    QCoreApplication.translate("AbstractQuickStatsBox", "Lowest phases")
    QCoreApplication.translate("AbstractQuickStatsBox", "Damned phase")

    def __init__(self, gname, parent):
        super(Phase10QSBox, self).__init__(gname, parent)
        self.playerStatsKeys.append("min_phases")
        self.playerStatsHeaders.append("Lowest phases")
        self.playerStatsKeys.append("damned_phase")
        self.playerStatsHeaders.append("Damned phase")


class Phase10PQSBox(Phase10QSBox, ParticularQuickStats):
    pass
