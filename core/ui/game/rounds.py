"""Round detail panel: table, plot and quick statistics tabs."""

from __future__ import annotations

import logging

from PySide6 import QtCore
from PySide6.QtCore import QEvent, QObject
from PySide6.QtGui import QAction, QColor, QIcon, QPaintEvent
from PySide6.QtWidgets import (
    QFrame,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QMenu,
    QMessageBox,
    QStackedLayout,
    QTableWidget,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from core.engine.engine import RoundGameEngine
from core.engine.settings import appsettings
from core.model.match import GenericRound
from core.ui.game.colours import PlayerColours
from core.ui.game.plots import PlotView
from core.ui.game.stats import QuickStatsTW

logger = logging.getLogger(__name__)


class GameRoundsDetail(QTabWidget):
    """Tabbed detail panel: rounds table, score plot and quick statistics."""

    edited = QtCore.Signal()

    def __init__(self, engine: RoundGameEngine, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.engine = engine
        self.initUI()

    def initUI(self) -> None:
        """Build the table, plot and statistics tabs."""
        self.setStyleSheet("QGroupBox { font-size: 18px; font-weight: bold; }")
        self.widgetLayout = QVBoxLayout(self)

        self.tableContainer = QFrame(self)
        self.tableContainerLayout = QVBoxLayout(self.tableContainer)
        self.addTab(self.tableContainer, "")

        self.table = self.createRoundTable(self.engine, self)
        self.tableContainerLayout.addWidget(self.table, stretch=1)
        self.table.edited.connect(self.updateRound)
        self.table.edited.connect(self.edited.emit)

        self.plot = self.createRoundPlot(self.engine, self)
        self.addTab(self.plot, "")

        self.gamestats = self.createQSBox()
        self.addTab(self.gamestats, "")

    def retranslateUI(self) -> None:
        """Refresh tab labels and child widgets for the current language."""
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

    def updatePlot(self) -> None:
        self.plot.updatePlot()

    def updateColours(self, colours: list[QColor]) -> None:
        """Propagate a new ordered colour list to the plot widget."""
        if hasattr(self.plot, "updateColours"):
            self.plot.updateColours(colours)

    def updateRound(self) -> None:
        """Rebuild the rounds table from the engine and refresh the plot."""
        self.table.resetClear()
        for r in self.engine.getRounds():
            self.table.insertRound(r)
        self.updatePlot()

    def updateStats(self) -> None:
        """Refresh the quick-stats tab, never letting a failure crash the board."""
        try:
            self.gamestats.updateContent(
                self.engine.getGame(), self.engine.getListPlayers()
            )
        except Exception:
            # Defensive: a stats refresh must never take down the board.
            logger.warning("Stats update failed", exc_info=True)
            self.gamestats.update()

    def deleteRound(self, _nround: int) -> None:
        self.plot.updatePlot()

    def createRoundTable(
        self, _engine: RoundGameEngine, parent: QWidget | None
    ) -> GameRoundTable:
        """Build the rounds table widget; games override for their columns."""
        return GameRoundTable(self, parent)

    def createRoundPlot(
        self, _engine: RoundGameEngine, parent: QWidget | None
    ) -> GameRoundPlot:
        """Build the score-plot widget; games override for their plots."""
        return GameRoundPlot(self, parent)

    def createQSBox(self) -> QuickStatsTW:
        """Build the quick-statistics tab for this game and its players."""
        return QuickStatsTW(
            self.engine.getGame(),  # pyright: ignore[reportArgumentType]
            self.engine.getListPlayers(),
            self,
        )

    def updatePlayerOrder(self) -> None:
        self.updateRound()


class GameRoundTable(QTableWidget):
    """Base rounds table: one column per player; games fill in the rows."""

    edited = QtCore.Signal()

    def __init__(self, engine, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.engine = engine
        self.setColumnCount(len(self.engine.getListPlayers()))
        self.initUI()

    def initUI(self) -> None:
        """Set up the header labels and custom context menu."""
        self.setHorizontalHeaderLabels(self.engine.getListPlayers())
        self.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.setContextMenuPolicy(QtCore.Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self.openTableMenu)

    def resetClear(self) -> None:
        """Clear all rows and reset the header to the current player order."""
        self.setHorizontalHeaderLabels(self.engine.getListPlayers())
        self.clearContents()
        self.setRowCount(0)

    def openTableMenu(self, position: QtCore.QPoint) -> None:
        """Show the right-click menu to delete the entry at ``position``."""
        item = self.indexAt(position)
        nentry = item.row() + 1
        if nentry <= 0 or self.engine.getWinner():
            return

        menu = QMenu()
        ic = QIcon(":/icons/delete.png")
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

    def insertRound(self, _rnd: GenericRound) -> None:
        """Append a table row for ``_rnd``; implemented by subclasses."""


class GameRoundPlot(QWidget):
    """Base score-plot widget wrapping a line-plot canvas."""

    player_colours: list[QColor] = PlayerColours
    plot_min_ymax: float = 10

    def __init__(self, engine, parent: QWidget | None) -> None:
        super().__init__(parent)
        self.plotinited = False
        self.engine = engine
        # Deliberately shadows QObject.parent with the passed-in widget.
        self.parent = parent  # pyright: ignore[reportAttributeAccessIssue]
        self.axiswidth = 0
        self.initUI()

    def initUI(self) -> None:
        """Create the plot canvas and add its line plot."""
        self.widgetLayout = QHBoxLayout(self)
        self.canvas = PlotView(self.player_colours, self)
        self.canvas.setBackground(self.palette().color(self.backgroundRole()))
        self.canvas.addLinePlot()
        self.canvas.setMinYMax(self.plot_min_ymax)
        self.widgetLayout.addWidget(self.canvas)
        self.plotinited = True

    def playerColour(self, player: str) -> QColor:
        """Return the colour for ``player`` using the ordered colour list when set."""
        colours = getattr(self, "_ordered_colours", None) or self.player_colours
        players = self.engine.getListPlayers()
        try:
            idx = players.index(player)
        except ValueError:
            idx = 0
        return colours[idx % len(colours)]

    def updateColours(self, colours: list[QColor]) -> None:
        """Update the plot's colour series to reflect a new player colour mapping."""
        self._ordered_colours = colours
        self.canvas.setColours(colours)
        self.canvas.viewport().update()

    def paintEvent(self, event: QPaintEvent) -> None:
        self.canvas.setBackground(self.palette().color(self.backgroundRole()))
        super().paintEvent(event)
        self.canvas.viewport().repaint()

    def retranslateUI(self) -> None:
        self.retranslatePlot()

    def isPlotInited(self) -> bool:
        return self.plotinited

    def updatePlot(self) -> None:
        """Redraw the plot from current data; implemented by subclasses."""

    def retranslatePlot(self) -> None:
        """Refresh plot labels for the current language; overridden."""


class ToggleGroupBox(QGroupBox):
    """A group box holding stacked screens that cycle on any child click."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        self.current = 0
        self.screens: list[QWidget] = []
        self.widgetLayout = QStackedLayout(self)

    def addScreen(self, widget: QWidget) -> None:
        """Add a screen and route clicks on it (and its children) to toggle."""
        self._install_event_filters(widget)
        self.screens.append(widget)
        self.widgetLayout.addWidget(widget)

    def _install_event_filters(self, widget: QWidget) -> None:
        """Install this filter on ``widget`` and all of its descendants."""
        widget.installEventFilter(self)
        for child in widget.findChildren(QObject):
            child.installEventFilter(self)

    def eventFilter(self, watched: QObject, event) -> bool:
        if (
            event.type() == QEvent.Type.MouseButtonPress
            and event.button() == QtCore.Qt.MouseButton.LeftButton
        ):
            self.toggle()
            return True
        return super().eventFilter(watched, event)

    def toggle(self) -> None:
        """Advance to the next stacked screen, wrapping around."""
        if len(self.screens) < 2:
            return
        self.current = (self.current + 1) % len(self.screens)
        self.widgetLayout.setCurrentIndex(self.current)


__all__ = [
    "GameRoundsDetail",
    "GameRoundTable",
    "GameRoundPlot",
    "ToggleGroupBox",
]
