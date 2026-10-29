"""Quick-statistics widgets: tabs, boxes, tables used inside game panels."""

from __future__ import annotations

import datetime
import logging
from collections.abc import Sequence

from PySide6 import QtCore
from PySide6.QtCore import QCoreApplication, QRect, QSize
from PySide6.QtGui import QFont, QFontInfo, QFontMetrics, QResizeEvent
from PySide6.QtWidgets import (
    QFrame,
    QGroupBox,
    QHeaderView,
    QLabel,
    QScrollArea,
    QSizePolicy,
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from core.engine.settings import appsettings
from core.registry import registry
from core.ui.performance import format_performance, performance_tooltip

logger = logging.getLogger(__name__)


class QuickStatsTW(QTabWidget):
    """Tab widget pairing general and per-player quick-statistics views."""

    def __init__(
        self, game: str, players: Sequence[str], parent: QWidget | None
    ) -> None:
        super().__init__(parent)
        self.game = game
        self.players = players
        self.initUI()

    def initStatsWidgets(self) -> None:
        """Create the general and particular statistics tab pages."""
        self.gs = GeneralQuickStats(self.game, self)
        self.ps = ParticularQuickStats(self.game, self)

    def initUI(self) -> None:
        """Build the tabs, populate players and apply translations."""
        self.initStatsWidgets()
        try:
            self.ps.updatePlayers(self.players)
        except Exception:
            logger.warning("Quick-stats init failed", exc_info=True)
        self.addTab(self.gs, "")
        self.addTab(self.ps, "")
        self.retranslateUI()

    def retranslateUI(self) -> None:
        """Refresh tab labels for the current language and button-text setting."""
        if appsettings["text_in_buttons"]:
            self.setTabText(self.indexOf(self.gs), self.tr("General"))
            self.setTabText(self.indexOf(self.ps), self.tr("Particular"))
        else:
            self.setTabText(self.indexOf(self.gs), "∑")
            self.setTabText(self.indexOf(self.ps), "#")
        self.gs.retranslateUI()
        self.ps.retranslateUI()

    def updateContent(
        self, game: str | None = None, players: Sequence[str] | None = None
    ) -> None:
        """Refresh both stats pages for the given game and player selection."""
        if game is not None:
            self.game = game
        self.gs.updateContent(game)
        self.ps.updatePlayers(players)
        self.ps.updateContent(game)


class AbstractQuickStatsBox(QGroupBox):
    """Scrollable box rendering match- and player-level statistics tables."""

    QCoreApplication.translate("AbstractQuickStatsBox", "Longest")
    QCoreApplication.translate("AbstractQuickStatsBox", "Shortest")
    QCoreApplication.translate("AbstractQuickStatsBox", "Average")
    QCoreApplication.translate("AbstractQuickStatsBox", "Highest")
    QCoreApplication.translate("AbstractQuickStatsBox", "Lowest")
    QCoreApplication.translate("AbstractQuickStatsBox", "Average")
    QCoreApplication.translate("AbstractQuickStatsBox", "Played")
    QCoreApplication.translate("AbstractQuickStatsBox", "Victories")
    QCoreApplication.translate("AbstractQuickStatsBox", "Ratio (%)")
    QCoreApplication.translate("AbstractQuickStatsBox", "Performance")
    QCoreApplication.translate("AbstractQuickStatsBox", "Highest")
    QCoreApplication.translate("AbstractQuickStatsBox", "Lowest")
    QCoreApplication.translate("AbstractQuickStatsBox", "Average")
    QCoreApplication.translate("AbstractQuickStatsBox", "Total")

    def __init__(self, game: str, parent: QWidget | None) -> None:
        super().__init__(parent)
        self.game = game
        self.initEngine()

        self.matchStatsKeys = [
            "nplayers",
            "maxduration",
            "minduration",
            "avgduration",
            "maxscore",
            "minscore",
            "avgscore",
        ]
        self.matchStatsHeaders = [
            "# Players",
            "Longest",
            "Shortest",
            "Average",
            "Highest",
            "Lowest",
            "Average",
        ]

        self.playerStatsKeys = [
            "nick",
            "played",
            "victories",
            "victoryp",
            "performance",
            "maxscore",
            "minscore",
            "avgscore",
            "sumscore",
        ]
        self.playerStatsHeaders = [
            "Player",
            "Played",
            "Victories",
            "Ratio (%)",
            "Performance",
            "Highest",
            "Lowest",
            "Average",
            "Total",
        ]

        self.initUI()

        sp = QSizePolicy(
            QSizePolicy.Policy.MinimumExpanding, QSizePolicy.Policy.Expanding
        )
        self.setSizePolicy(sp)

    def initEngine(self) -> None:
        """Instantiate the statistics engine for this game."""
        self.stats = registry.create_stats_engine(self.game)

    def initUI(self) -> None:
        """Build the scroll area, labels and statistics tables."""
        self.superlayout = QVBoxLayout(self)
        self.scrollarea = QScrollArea()
        self.scrollarea.setWidgetResizable(True)
        self.scrollarea.setFrameShape(QFrame.Shape.NoFrame)
        self.scrollarea.setObjectName("quickStatsScrollArea")
        self.superlayout.addWidget(self.scrollarea)
        self.container = QWidget(self)
        self.container.setObjectName("quickStatsContainer")
        self.setStyleSheet("""QWidget#quickStatsContainer {
            background: transparent;
        }
        QScrollArea#quickStatsScrollArea {
            background: transparent;
        }""")
        self.widgetLayout = QVBoxLayout(self.container)
        self.scrollarea.setWidget(self.container)

        self.gameStatsLabel = QLabel(self)
        self.widgetLayout.addWidget(self.gameStatsLabel)

        self.matchStatsTitleLabel = QLabel(self)
        self.widgetLayout.addWidget(self.matchStatsTitleLabel)
        self.matchStatsTable = StatsTable(self)
        self.widgetLayout.addWidget(self.matchStatsTable)

        self.playerStatsTitleLabel = QLabel(self)
        self.widgetLayout.addWidget(self.playerStatsTitleLabel)
        self.playerStatsTable = StatsTable(self)
        StatsTable.linkHeaderSizes(self.matchStatsTable, self.playerStatsTable)
        self.widgetLayout.addWidget(self.playerStatsTable)

        self.titlecss = """QLabel { font-weight: bold; font-size: 18px; margin-top: 10px; margin-bottom: 5px;}"""
        self.matchStatsTitleLabel.setStyleSheet(self.titlecss)
        self.playerStatsTitleLabel.setStyleSheet(self.titlecss)
        self.gameStatsLabel.setStyleSheet(self.titlecss)

        self.widgetLayout.addStretch()
        self.retranslateUI()

    def retranslateUI(self) -> None:
        """Apply translated title strings and refresh the displayed content."""
        self.gameStatsText = self.tr("Last winner") + ": {} ({})"
        self.matchStatsTitleLabel.setText(self.tr("Matches"))
        self.playerStatsTitleLabel.setText(self.tr("Players"))
        self.updateContent()
        self.update()

    def updateContent(self, _game: str | None = None) -> None:
        """Reload statistics from the engine and repopulate every table."""
        self.stats.update()
        gamestats = self.stats.getGameStats(self.game)
        matchstats = self.stats.getMatchGameStats(self.game)
        playerstats = self.stats.getPlayerGameStats(self.game)

        if not gamestats:
            self.gameStatsLabel.setText(self.tr("No statistics found"))
            self.playerStatsTitleLabel.hide()
            self.matchStatsTitleLabel.hide()
        else:
            lastwinnerdate = (
                datetime.datetime.strptime(
                    gamestats["lastwinnerdate"], "%Y-%m-%d %H:%M:%S"
                )
                .replace(tzinfo=datetime.UTC)
                .astimezone()
                .strftime("%Y-%m-%d %H:%M:%S")
            )
            self.gameStatsLabel.setText(
                self.gameStatsText.format(gamestats["lastwinner"], lastwinnerdate)
            )
            self.playerStatsTitleLabel.show()
            self.matchStatsTitleLabel.show()
        headers = [self.tr(h) for h in self.matchStatsHeaders]
        self.updateTable(
            self.matchStatsTable, matchstats, self.matchStatsKeys, "nplayers", headers
        )

        headers = [self.tr(h) for h in self.playerStatsHeaders]
        self.updateTable(
            self.playerStatsTable, playerstats, self.playerStatsKeys, "nick", headers
        )
        # The match table was fitted before the player titles it shares a
        # size with were known.
        self.matchStatsTable.fitColumns()

    def updateTable(
        self,
        table: StatsTable,
        contents: Sequence[dict] | None,
        keyorder: Sequence[str],
        rowheaderkey: str,
        cheaders: Sequence[str],
    ) -> None:
        """Fill ``table`` from ``contents`` in ``keyorder`` column order."""
        table.clear()
        if contents and len(contents[0]) > 1:
            table.show()
            displayed = contents
            if rowheaderkey in keyorder:
                vheaders = ["" for _ in displayed]
                table.verticalHeader().setFixedWidth(1)
                table.setSortingEnabled(True)
            else:
                vheaders = [str(row[rowheaderkey]) for row in displayed]
            table.setVerticalHeaderLabels(vheaders)
            table.setRowCount(len(displayed))
            table.setColumnCount(len(cheaders))
            table.setHorizontalHeaderLabels(cheaders)
            for i, row in enumerate(displayed):
                for j, key in enumerate(keyorder):
                    try:
                        value = row[key]
                    except KeyError:
                        value = "-"
                    item = QTableWidgetItem()
                    if key == "performance":
                        item = _PerformanceItem(value)
                    elif isinstance(value, (int, float)):
                        item.setData(QtCore.Qt.ItemDataRole.DisplayRole, value)
                    else:
                        item.setData(QtCore.Qt.ItemDataRole.DisplayRole, str(value))
                    item.setTextAlignment(
                        QtCore.Qt.AlignmentFlag.AlignVCenter
                        | QtCore.Qt.AlignmentFlag.AlignHCenter
                    )
                    item.setFlags(item.flags() ^ QtCore.Qt.ItemFlag.ItemIsEditable)
                    table.setItem(i, j, item)

            for j, key in enumerate(keyorder):
                if key == "performance" and (header := table.horizontalHeaderItem(j)):
                    header.setToolTip(performance_tooltip())

            table.setMinimumWidth(table.sizeHint().width())
            table.fitColumns()
        else:
            table.hide()


class _PerformanceItem(QTableWidgetItem):
    """Performance cell shown as ``1.35×`` that still sorts by its number."""

    def __init__(self, value: object) -> None:
        number = value if isinstance(value, (int, float)) else None
        super().__init__(format_performance(number))
        self._value = -1.0 if number is None else float(number)

    def __lt__(self, other: QTableWidgetItem) -> bool:
        if isinstance(other, _PerformanceItem):
            return self._value < other._value
        return super().__lt__(other)


class GeneralQuickStats(AbstractQuickStatsBox):
    """Quick-stats box aggregating results across all players."""


class ParticularQuickStats(AbstractQuickStatsBox):
    """Quick-stats box filtered to a specific set of players."""

    def initEngine(self) -> None:
        """Instantiate the per-player statistics engine for this game."""
        self.stats = registry.create_particular_stats_engine(self.game)

    def updatePlayers(self, players: Sequence[str] | None) -> None:
        if players:
            self.stats.updatePlayers(players)


class StatsTable(QTableWidget):
    """Read-only table whose columns share the width without scrolling sideways.

    Titles are drawn as large as the table text when there is room for all of
    them on one line, and smaller when there is not. Every column gets at least
    the room its widest title word and its values need, and the spare width is
    shared evenly. Titles wrap onto further lines and the header grows to fit
    them, so nothing is cut short until the table is too narrow for even that.
    """

    MIN_COLUMN_WIDTH = 40
    MIN_HEADER_FONT_SIZE = 15
    HEADER_PADDING = 4

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        header = self.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.Fixed)
        header.setDefaultAlignment(
            QtCore.Qt.AlignmentFlag.AlignCenter | QtCore.Qt.TextFlag.TextWordWrap
        )
        header.setMinimumSectionSize(1)
        self._headerFontSize = 0
        self._linked: list[StatsTable] = [self]
        self._setHeaderFontSize(self.MIN_HEADER_FONT_SIZE)
        self.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.verticalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Fixed)

    def setHorizontalHeaderLabels(self, labels: Sequence[str]) -> None:
        """Set the column titles, each also shown in full as a tooltip."""
        super().setHorizontalHeaderLabels(labels)
        for j, label in enumerate(labels):
            if item := self.horizontalHeaderItem(j):
                item.setToolTip(label)

    def _headerText(self, column: int) -> str:
        item = self.horizontalHeaderItem(column)
        return item.text() if item else ""

    def _headerMetrics(self, size: int) -> QFontMetrics:
        # Titles are measured bold: the theme draws them semi-bold at most.
        font = QFont(self.horizontalHeader().font())
        font.setPixelSize(size)
        font.setBold(True)
        return QFontMetrics(font)

    def _setHeaderFontSize(self, size: int) -> None:
        if size != self._headerFontSize:
            self._headerFontSize = size
            self.setStyleSheet(
                "QHeaderView::section:horizontal {"
                f" font-size: {size}px; padding: {self.HEADER_PADDING}px; }}"
            )

    def _fittingHeaderSize(self, available: int, chrome: int) -> int:
        """The largest title size, up to that of the table text, that keeps
        every title on one line; the smallest one otherwise."""
        text_size = QFontInfo(self.font()).pixelSize()
        for size in range(text_size, self.MIN_HEADER_FONT_SIZE, -1):
            widths = self._titleWidths(self._headerMetrics(size), chrome)[1]
            if sum(widths) <= available:
                return size
        return min(text_size, self.MIN_HEADER_FONT_SIZE)

    @staticmethod
    def linkHeaderSizes(*tables: StatsTable) -> None:
        """Make ``tables`` (laid out at the same width) share one title size."""
        for table in tables:
            table._linked = list(tables)

    def _titleWidths(
        self, metrics: QFontMetrics, chrome: int
    ) -> tuple[list[int], list[int]]:
        """Room each column needs with its title wrapped at every word, and
        with its title kept on a single line."""
        needs, single_line = [], []
        for j in range(self.columnCount()):
            text = self._headerText(j)
            word = max((metrics.horizontalAdvance(w) for w in text.split()), default=0)
            need = max(self.MIN_COLUMN_WIDTH, word + chrome, self.sizeHintForColumn(j))
            needs.append(need)
            single_line.append(max(need, metrics.horizontalAdvance(text) + chrome))
        return needs, single_line

    def fitColumns(self) -> None:
        """Share the width out between the columns and fit the header height."""
        count = self.columnCount()
        if not count:
            return
        header = self.horizontalHeader()
        # Section padding on both sides plus its border.
        chrome = 2 * self.HEADER_PADDING + 2
        vheader = self.verticalHeader()
        available = self.width() - 2 * self.frameWidth()
        if vheader.isVisible():
            available -= vheader.width()

        size = min(t._fittingHeaderSize(available, chrome) for t in self._linked)
        self._setHeaderFontSize(size)
        metrics = self._headerMetrics(size)
        needs, single_line = self._titleWidths(metrics, chrome)
        total = sum(needs)
        if total <= available:
            # Unwrap the cheapest titles first, then share out what is left.
            widths = list(needs)
            spare = available - total
            for j in sorted(range(count), key=lambda j: single_line[j] - needs[j]):
                if single_line[j] - needs[j] > spare:
                    break
                spare -= single_line[j] - needs[j]
                widths[j] = single_line[j]
            share, extra = divmod(spare, count)
            widths = [w + share + (j < extra) for j, w in enumerate(widths)]
        else:
            # Too narrow for every title. The values keep their room while it
            # lasts and the titles (in full in their tooltips) give way; the
            # width is still filled exactly so no column is pushed out of view.
            available = max(available, 0)
            values = [
                min(need, self.sizeHintForColumn(j)) for j, need in enumerate(needs)
            ]
            if sum(values) <= available:
                slack = [
                    need - value for need, value in zip(needs, values, strict=True)
                ]
                room = available - sum(values)
                widths = [
                    v + s * room // sum(slack)
                    for v, s in zip(values, slack, strict=True)
                ]
            else:
                widths = [v * available // sum(values) for v in values]
            for j in range(available - sum(widths)):
                widths[j % count] += 1
        for j, width in enumerate(widths):
            header.resizeSection(j, width)

        flags = QtCore.Qt.AlignmentFlag.AlignCenter | QtCore.Qt.TextFlag.TextWordWrap
        title_height = max(
            metrics.boundingRect(
                QRect(0, 0, max(1, width - chrome), 1000), flags, self._headerText(j)
            ).height()
            for j, width in enumerate(widths)
        )
        header.setFixedHeight(title_height + chrome)
        self.setFixedHeight(self.sizeHint().height())

    def resizeEvent(self, event: QResizeEvent) -> None:
        super().resizeEvent(event)
        self.fitColumns()

    def sizeHint(self) -> QSize:
        """Size the table to its column count, header and row heights."""
        rows = sum(self.rowHeight(i) for i in range(self.rowCount()))
        return QSize(
            self.MIN_COLUMN_WIDTH * self.columnCount() + 2 * self.frameWidth(),
            self.horizontalHeader().height() + rows + 2 * self.frameWidth(),
        )


__all__ = [
    "AbstractQuickStatsBox",
    "GeneralQuickStats",
    "ParticularQuickStats",
    "QuickStatsTW",
    "StatsTable",
]
