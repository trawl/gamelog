"""Qt scoreboard widgets for Parchis: entry input, table, plot and stats."""

from __future__ import annotations

import logging
from collections import Counter
from typing import cast

from PySide6 import QtCore
from PySide6.QtGui import QColor, QKeyEvent
from PySide6.QtWidgets import (
    QButtonGroup,
    QFrame,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from core.engine.settings import appsettings
from core.model.base import GenericRound
from core.ui.game import (
    GameInputWidget,
    GameNotImplementedException,
    GameRoundPlot,
    GameRoundsDetail,
    GameRoundTable,
    GameWidget,
    QuickStatsTW,
    ScoreSpinBox,
)
from core.ui.gamestats import GeneralQuickStats, ParticularQuickStats, StatsTable
from games.parchis.engine import ParchisEngine
from games.parchis.model import ParchisEntry

_PARCHIS_COLOURS = [
    # QColor(255, 200, 0),  # Yellow
    QColor(222, 198, 16),
    QColor(123, 164, 218),  # Blue
    QColor(220, 30, 30),  # Red
    QColor(0, 160, 50),  # Green
    QColor(255, 165, 79),  # Orange
    QColor(147, 112, 219),  # Purple
]

logger = logging.getLogger(__name__)


class ParchisWidget(GameWidget):
    """Scoreboard tab for Parchis, scored one feature entry at a time."""

    player_colours = _PARCHIS_COLOURS

    def createEngine(self) -> None:
        if self.game != "Parchis":
            raise GameNotImplementedException(f"No engine for game {self.game}")
        self.engine = ParchisEngine()

    def initUI(self) -> None:
        """Build the scoreboard and dock the commit/undo buttons into the input."""
        super().initUI()
        if not self.gameInput:
            self.gameInput = self.createGameInputWidget(self)

        self.commitRoundButton.setSizePolicy(
            QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred
        )
        self.commitRoundButton.setMinimumWidth(60)
        self.undoButton.setSizePolicy(
            QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred
        )
        self.gameInput.placeCommitButton(self.commitRoundButton)
        self.gameInput.placeUndoButton(self.undoButton)

        self.retranslateUI()
        QtCore.QTimer.singleShot(1000, self.gameInput.setFocus)

    def retranslateUI(self) -> None:
        super().retranslateUI()
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
        self.commitRoundButton.setStyleSheet(css)
        self.undoButton.setStyleSheet(css)

    def createGameInputWidget(
        self, parent: QWidget | None = None
    ) -> ParchisInputWidget:
        return ParchisInputWidget(self.engine, parent)

    def createRoundsDetail(self, parent: QWidget | None = None) -> ParchisEntriesDetail:
        return ParchisEntriesDetail(self.engine, parent)

    def getPlayerExtraInfo(self, player: str) -> dict:
        """Return the selected kills for the current entry, if any."""
        kills = self.gameInput.getKills()
        if kills:
            return {"kills": kills}
        else:
            return {}

    def checkPlayerScore(
        self, player: str, score: int, extras: dict | None = None
    ) -> bool:
        return 0 <= score <= 4

    def commitRoundSanityCheck(self, interactive: bool = False) -> bool:
        """Check that a player, a kind and a valid score are all selected."""
        player = self.gameInput.getPlayer()
        score = self.gameInput.getScore()
        if player == "":
            msg = self.tr("You must select a player")
            if interactive:
                QMessageBox.warning(self, self.game, msg)
            logger.debug(f"[commitRoundSanityCheck] {msg}")
            return False

        if not self.checkPlayerScore(player, score):
            msg = self.tr(f"{player} score is not valid")
            if interactive:
                QMessageBox.warning(self, self.game, msg)
            logger.debug(f"[commitRoundSanityCheck] {msg} {score}")
            return False

        # Empty entry, no score, no kills
        if score == 0 and not self.gameInput.getKills():
            msg = self.tr("Empty entry, add at least a goal or a kill")
            if interactive:
                QMessageBox.warning(self, self.game, msg)
            logger.debug(f"[commitRoundSanityCheck] {msg}")
            return False

        logger.debug("[commitRoundSanityCheck] Ready to commit")
        return True

    def commitRound(self) -> None:
        """Record the selected player's scoring entry and refresh the board."""
        if not self.commitRoundSanityCheck(interactive=True):
            return
        player = self.gameInput.getPlayer()
        score = self.gameInput.getScore()
        try:
            self.playerGroupBox[self.engine.getDealer()].unsetDealer()
        except KeyError:
            pass
        cast("ParchisEngine", self.engine).addEntry(
            player, score, self.getPlayerExtraInfo(player)
        )
        self.engine.printStats()
        self.updatePanel()


class ParchisInputWidget(GameInputWidget):
    """Player/kind/score selectors for entering a single Parchis score."""

    player_colours = _PARCHIS_COLOURS
    enterPressed = QtCore.Signal()

    def __init__(self, engine, parent) -> None:
        super().__init__(engine, parent)

    def initUI(self) -> None:
        """Lay out the player, kind and score selector groups."""
        self.setStyleSheet("QGroupBox { font-size: 18px; font-weight: bold; }")
        self.widgetLayout = QHBoxLayout(self)
        self.playerGroup = QGroupBox(self)
        self.widgetLayout.addWidget(self.playerGroup)
        self.playerButtonGroup = QButtonGroup(self)
        self.playerGroupLayout = QGridLayout(self.playerGroup)

        b = QPushButton("", self.playerGroup)
        b.setCheckable(True)
        self.playerButtonGroup.addButton(b, 0)
        self.playerButtons = [b]
        b.hide()
        for i, player in enumerate(self.engine.getListPlayers(), 1):
            b = QPushButton(f"{i}. {player}", self.playerGroup)
            b.setCheckable(True)
            if len(self.engine.getListPlayers()) > 2:
                self.playerGroupLayout.addWidget(b, (i - 1) % 2, (i - 1) // 2)
            else:
                self.playerGroupLayout.addWidget(b, 0, (i - 1) % 2)
            self.playerButtonGroup.addButton(b, i)
            self.playerButtons.append(b)
            b.setStyleSheet(self._playerButtonStyle(self.player_colours[i - 1]))

        self.playerButtonGroup.idToggled.connect(self.changed)
        self.playerButtonGroup.idToggled.connect(self.updateGoalsColour)

        self.goalsSpinBox = ScoreSpinBox(self)
        self.goalsSpinBox.setRange(0, 4, 0)
        self.goalsSpinBox.setHideMinimum(False)
        self.goalsSpinBox.setSizePolicy(
            QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Preferred
        )
        self.goalsSpinBox.valueChanged.connect(self.changed)

        self.goalsGroup = QGroupBox(self)
        self.widgetLayout.addWidget(self.goalsGroup)
        self.goalsGroupLayout = QHBoxLayout(self.goalsGroup)

        self.goalsGroupLayout.addWidget(self.goalsSpinBox)

        self.killsGroup = QGroupBox(self)
        self.widgetLayout.addWidget(self.killsGroup)
        self.killsGroupLayout = QGridLayout(self.killsGroup)
        self.killBoxes = []
        for i, _ in enumerate(self.engine.getListPlayers()):
            ksb = ScoreSpinBox(self)
            ksb.setRange(0, 4, 0)
            ksb.setHideMinimum(False)
            ksb.setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Preferred)
            ksb.setFixedWidth(130)
            ksb.valueChanged.connect(self.changed)
            if len(self.engine.getListPlayers()) > 2:
                self.killsGroupLayout.addWidget(ksb, (i) % 2, (i) // 2)
            else:
                self.killsGroupLayout.addWidget(ksb, 0, (i) % 2)
            self.killBoxes.append(ksb)

        self.changed.connect(self.ensureInputGuardRails)
        self.reset()
        self.retranslateUI()

    def _playerButtonStyle(self, colour: QColor) -> str:
        r, g, b = colour.red(), colour.green(), colour.blue()
        return f"""
            QPushButton {{
                font-weight: bold;
                font-size: 18px;
                color: rgb({r},{g},{b});
                border: 1px solid rgba({r},{g},{b},80);
                border-radius: 6px;
                padding: 6px 6px;
                background: transparent;
                text-align: left;
            }}
            QPushButton:checked {{
                background: rgb({r},{g},{b});
                color: white;
                border: 1px solid rgb({r},{g},{b});
            }}
            QPushButton:hover:!checked {{
                background: rgba({r},{g},{b},30);
                color: rgb({r},{g},{b});
                border: 1px solid rgba({r},{g},{b},150);
            }}
        """

    def retranslateUI(self) -> None:
        super().retranslateUI()
        self.playerGroup.setTitle(self.tr("Select Player"))
        self.goalsGroup.setTitle(self.tr("Select number of goals"))
        self.killsGroup.setTitle(self.tr("Select Kills"))

    def placeCommitButton(self, cb) -> None:
        self.widgetLayout.addWidget(cb, 2)

    def placeUndoButton(self, ub) -> None:
        self.widgetLayout.addWidget(ub, 1)

    def getPlayer(self) -> str:
        """Return the selected player's name, or ``""`` if none is selected."""
        pid = self.playerButtonGroup.checkedId()
        if not pid:
            return ""
        player = self.engine.getListPlayers()[pid - 1]
        return str(player)

    def getKills(self) -> list[str]:
        """Return the sequence of kills"""
        kills = []
        for p, bsk in enumerate(self.killBoxes):
            for _ in range(0, bsk.value()):
                kills.append(self.engine.getListPlayers()[p])
        return kills

    def getScore(self) -> int:
        return cast("int", self.goalsSpinBox.value())

    def reset(self) -> None:
        """Clear the player/kind selection and reset the score to zero."""
        self.playerButtons[0].setChecked(True)
        self.goalsSpinBox.setValue(0)
        for i, ksb in enumerate(self.killBoxes):
            ksb.setColour(self.player_colours[i])
            ksb.setValue(0)
        self.changed.emit()
        self.setFocus()

    def keyPressEvent(self, event: QKeyEvent) -> None:
        """Route number keys to the player then kind selection, Return commits."""
        numberkeys = [
            QtCore.Qt.Key.Key_1,
            QtCore.Qt.Key.Key_2,
            QtCore.Qt.Key.Key_3,
            QtCore.Qt.Key.Key_4,
            QtCore.Qt.Key.Key_5,
            QtCore.Qt.Key.Key_6,
        ]
        try:
            number = numberkeys.index(cast("QtCore.Qt.Key", event.key())) + 1
        except ValueError:
            number = 0
        if event.key() == QtCore.Qt.Key.Key_Return:
            self.enterPressed.emit()
        elif number:
            if not self.getPlayer():
                if number <= len(self.engine.getPlayers()):
                    self.playerButtons[number].setChecked(True)
                    self.changed.emit()

        return super().keyPressEvent(event)

    def updatePlayerOrder(self) -> None:
        """Rebuild the player radio buttons in the current player order."""
        trash = QWidget()
        trash.setLayout(self.playerGroupLayout)

        self.playerButtonGroup = QButtonGroup(self)
        self.playerGroupLayout = QGridLayout(self.playerGroup)
        b = QPushButton("", self.playerGroup)
        b.setCheckable(True)
        self.playerButtonGroup.addButton(b, 0)
        self.playerButtons = [b]
        b.hide()

        for i, player in enumerate(self.engine.getListPlayers(), 1):
            b = QPushButton(f"{i}. {player}", self.playerGroup)
            b.setCheckable(True)
            if len(self.engine.getListPlayers()) > 2:
                self.playerGroupLayout.addWidget(b, (i - 1) % 2, (i - 1) // 2)
            else:
                self.playerGroupLayout.addWidget(b, 0, (i - 1) % 2)
            self.playerButtonGroup.addButton(b, i)
            self.playerButtons.append(b)
            b.setStyleSheet(self._playerButtonStyle(self.player_colours[i - 1]))

        self.reset()

    def updateGoalsColour(self, id) -> None:
        colours = [QColor(128, 128, 128)] + self.player_colours
        self.goalsSpinBox.setColour(colours[id])
        self.goalsSpinBox.setFocus()

    def ensureInputGuardRails(self) -> None:
        """Ensure game input only allows to introduce sensible values."""
        pid = self.playerButtonGroup.checkedId()
        self.goalsSpinBox.setEnabled(bool(pid))
        for kb in self.killBoxes:
            kb.setEnabled(bool(pid))
        if not pid:
            return
        for i, kb in enumerate(self.killBoxes):
            if pid - 1 == i:
                kb.setEnabled(True)
                kb.setRange(0, 1, 0)
            else:
                if self.killBoxes[pid - 1].value() == 0:
                    kb.setEnabled(True)
                else:
                    kb.setValue(0)
                    kb.setEnabled(False)
                kb.setRange(0, 4, 0)


class ParchisEntriesDetail(GameRoundsDetail):
    """Rounds-detail panel for Parchis, adding a killer summary table."""

    def __init__(self, engine, parent: QWidget | None = None) -> None:
        super().__init__(engine, parent)

    def initUI(self) -> None:
        super().initUI()
        self.liveStats = ParchisLiveStats(self.engine, self)
        self.insertTab(0, self.liveStats, "")
        self.setCurrentIndex(0)

    def retranslateUI(self) -> None:
        super().retranslateUI()
        if appsettings["text_in_buttons"]:
            self.setTabText(self.indexOf(self.liveStats), self.tr("Live Statistics"))
        else:
            self.setTabText(self.indexOf(self.liveStats), "✝")
        self.liveStats.retranslateUI()

    def updateRound(self) -> None:
        """Rebuild live stats."""
        super().updateRound()
        self.liveStats.updateContent()

    def createRoundTable(self, engine, parent: QWidget | None = None):
        return ParchisRoundTable(self.engine, parent)

    def createRoundPlot(self, engine, parent: QWidget | None = None):
        return ParchisEntriesPlot(self.engine, self)

    def createQSBox(self, parent: QWidget | None = None):
        return ParchisQSTW(
            self.engine.getGame(),  # pyright: ignore[reportArgumentType]
            self.engine.getListPlayers(),
            self,
        )


class ParchisLiveStats(QWidget):
    """Live stats for a Parchis Match"""

    def __init__(self, engine, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.engine = engine
        self.initUI()

    def initUI(self) -> None:
        self.superlayout = QVBoxLayout(self)
        self.scrollarea = QScrollArea()
        self.scrollarea.setWidgetResizable(True)
        self.scrollarea.setFrameShape(QFrame.Shape.NoFrame)
        self.scrollarea.setObjectName("liveStatsScrollArea")
        self.superlayout.addWidget(self.scrollarea)
        self.container = QWidget(self)
        self.container.setObjectName("liveStatsContainer")
        self.setStyleSheet("""QWidget#liveStatsContainer {
            background: transparent;
        }
        QScrollArea#liveStatsScrollArea {
            background: transparent;
        }""")
        self.widgetLayout = QVBoxLayout(self.container)
        self.scrollarea.setWidget(self.container)
        title_css = """QLabel { font-weight: bold; font-size: 18px; margin-top: 10px; margin-bottom: 5px;}"""
        self.comboTableTitle = QLabel(self)
        self.comboTableTitle.setStyleSheet(title_css)
        self.comboTableTitle.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.widgetLayout.addWidget(self.comboTableTitle)
        self.comboTable = StatsTable(self)
        self.widgetLayout.addWidget(self.comboTable)
        self.widgetLayout.addSpacing(20)
        self.killsTableTitle = QLabel(self)
        self.killsTableTitle.setStyleSheet(title_css)
        self.killsTableTitle.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.widgetLayout.addWidget(self.killsTableTitle)
        self.killsTable = StatsTable(self)
        self.widgetLayout.addWidget(self.killsTable)
        self.widgetLayout.addStretch()
        self.retranslateUI()

    def retranslateUI(self) -> None:
        """Apply translated title strings and refresh the displayed content."""
        self.killsTableTitle.setText(self.tr("Killer table"))
        self.comboTableTitle.setText(self.tr("Summary"))
        self.updateContent()

    def updateContent(self) -> None:
        """Reload statistics from the engine and repopulate."""
        players = self.engine.getListPlayers()
        kills_tally = self.engine.getKillsTally()
        combo_tally = self.engine.getComboTally()
        sum_table_headers = {
            "kills": self.tr("kills"),
            "deaths": self.tr("deaths"),
            "suicides": self.tr("suicides"),
            "fav_target": self.tr("fav_target"),
            "combos": self.tr("combos"),
        }
        self.killsTable.setVerticalHeaderLabels(players)
        self.killsTable.setRowCount(len(players))
        self.killsTable.setColumnCount(len(players))
        self.killsTable.setHorizontalHeaderLabels(players)
        self.comboTable.setVerticalHeaderLabels(list(sum_table_headers.values()))
        self.comboTable.setRowCount(len(sum_table_headers))
        self.comboTable.setColumnCount(len(players))
        self.comboTable.setHorizontalHeaderLabels(players)
        for i, killer in enumerate(players):
            for j, dead in enumerate(players):
                item = QTableWidgetItem()
                item.setData(
                    QtCore.Qt.ItemDataRole.DisplayRole, str(kills_tally[killer][dead])
                )
                item.setTextAlignment(
                    QtCore.Qt.AlignmentFlag.AlignVCenter
                    | QtCore.Qt.AlignmentFlag.AlignHCenter
                )
                item.setFlags(item.flags() ^ QtCore.Qt.ItemFlag.ItemIsEditable)
                self.killsTable.setItem(i, j, item)

        self.killsTable.setFixedHeight(self.killsTable.sizeHint().height() + 10)
        self.killsTable.setMinimumWidth(self.killsTable.sizeHint().width())

        top_combos = max(combo_tally)
        top_kills = max(sum(kills_tally[player].values()) for player in kills_tally)
        top_deaths = max(
            sum(row[player] for row in kills_tally.values()) for player in kills_tally
        )
        top_suicides = max(kills_tally[player][player] for player in kills_tally)
        for i, stat in enumerate(sum_table_headers.keys()):
            for j, player in enumerate(players):
                val = ""
                bold = False
                if stat == "combos":
                    val = combo_tally[player]
                    bold = val == top_combos and val != 0
                elif stat == "kills":
                    val = sum(kills_tally[player].values())
                    bold = val == top_kills and val != 0
                elif stat == "deaths":
                    val = sum(row[player] for row in kills_tally.values())
                    bold = val == top_deaths and val != 0
                elif stat == "suicides":
                    val = kills_tally[player][player]
                    bold = val == top_suicides and val != 0
                elif stat == "fav_target":
                    max_kills = max(kills_tally[player].values())
                    val = "-"
                    if max_kills:
                        targets = [
                            key
                            for key, value in kills_tally[player].items()
                            if value == max_kills
                        ]
                        val = f"{', '.join(sorted(targets))} ({max_kills})"
                item = QTableWidgetItem()
                item.setData(QtCore.Qt.ItemDataRole.DisplayRole, str(val))
                item.setTextAlignment(
                    QtCore.Qt.AlignmentFlag.AlignVCenter
                    | QtCore.Qt.AlignmentFlag.AlignHCenter
                )
                if bold:
                    font = item.font()
                    font.setBold(True)
                    item.setFont(font)
                item.setFlags(item.flags() ^ QtCore.Qt.ItemFlag.ItemIsEditable)
                self.comboTable.setItem(i, j, item)

        self.comboTable.setFixedHeight(self.comboTable.sizeHint().height() + 10)
        self.comboTable.setMinimumWidth(self.comboTable.sizeHint().width())


class ParchisRoundTable(GameRoundTable):
    """Entry-by-entry score table for Parchis, coloured by feature kind."""

    def __init__(self, engine, parent: QWidget | None = None) -> None:
        super().__init__(engine, parent)

    def insertRound(self, entry: GenericRound) -> None:
        """Append a row for ``entry``, highlighting the scoring player's cell."""
        entry = cast("ParchisEntry", entry)
        score = entry.getPlayerScore()
        kills = entry.getKills()
        # background = self.bgcolors[kinds.index(kind)]
        i = entry.getNumRound() - 1
        self.insertRow(i)
        for j, player in enumerate(self.engine.getListPlayers()):
            item = QTableWidgetItem()
            item.setFlags(item.flags() ^ QtCore.Qt.ItemFlag.ItemIsEditable)
            item.setTextAlignment(
                QtCore.Qt.AlignmentFlag.AlignVCenter
                | QtCore.Qt.AlignmentFlag.AlignCenter
            )

            text = ""
            text_elems = []
            if player == entry.getPlayer():
                if score:
                    text_elems.append(f"{'◉' * entry.getPlayerScore()}")
                if kills:
                    text_elems.append(
                        ", ".join(
                            f"{name} {'†' * count}"
                            for name, count in sorted(Counter(kills).items())
                        )
                    )
                text = ", ".join(text_elems)
                font = item.font()
                font.setBold(True)
                item.setFont(font)
            item.setText(text)
            self.setItem(i, j, item)
        self.scrollToBottom()


class ParchisEntriesPlot(GameRoundPlot):
    """Cumulative score-over-entries plot for Parchis."""

    player_colours = _PARCHIS_COLOURS

    def updatePlot(self) -> None:
        """Redraw the running-total series, one line per player."""
        if not self.isPlotInited():
            return
        super().updatePlot()
        scores = {}
        for player in self.engine.getPlayers():
            scores[player] = [0]

        for entry in self.engine.getRounds():
            if not entry.getPlayerScore():
                continue
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


class ParchisQSTW(QuickStatsTW):
    """Quick-stats tab set for Parchis."""

    def initStatsWidgets(self) -> None:
        self.gs = ParchisQSBox(self)
        self.ps = ParchisPQSBox(self)


class ParchisQSBox(GeneralQuickStats):
    """General quick-stats page adding max-kills and max-combo columns."""

    def __init__(self, parent=None) -> None:
        self.game = "Parchis"
        super().__init__(self.game, parent)
        self.matchStatsKeys.append("max_kills")
        self.matchStatsHeaders.append(self.tr("Max Kills"))
        self.matchStatsKeys.append("max_combo")
        self.matchStatsHeaders.append(self.tr("Max Combo"))

        self.playerStatsKeys.append("max_kills")
        self.playerStatsHeaders.append(self.tr("Max Kills"))
        self.playerStatsKeys.append("max_combo")
        self.playerStatsHeaders.append(self.tr("Max Combo"))


class ParchisPQSBox(ParchisQSBox, ParticularQuickStats):
    """Player-filtered variant of the Parchis quick-stats page."""
