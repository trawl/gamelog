"""Quick-statistics tab widgets summarising per-game and per-player results."""

from __future__ import annotations

import datetime
import logging
from collections.abc import Sequence

from PySide6 import QtCore
from PySide6.QtCore import QCoreApplication, QSize
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
from core.ui.tab import Tab

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
    QCoreApplication.translate("AbstractQuickStatsBox", "Highest")
    QCoreApplication.translate("AbstractQuickStatsBox", "Lowest")
    QCoreApplication.translate("AbstractQuickStatsBox", "Average")
    QCoreApplication.translate("AbstractQuickStatsBox", "Total")

    def __init__(self, game: str, parent: QWidget | None) -> None:
        super().__init__(parent)
        # self.stats = None
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
        self.widgetLayout.addWidget(self.playerStatsTable)

        self.titlecss = """QLabel { font-weight: bold; font-size: 18px; margin-top: 10px; margin-bottom: 5px;}"""
        self.matchStatsTitleLabel.setStyleSheet(self.titlecss)
        self.playerStatsTitleLabel.setStyleSheet(self.titlecss)
        self.gameStatsLabel.setStyleSheet(self.titlecss)

        #         self.stretch = QSpacerItem(0,0)
        #         self.widgetLayout.addSpacerItem(self.stretch)
        self.widgetLayout.addStretch()
        self.retranslateUI()

    def retranslateUI(self) -> None:
        """Apply translated title strings and refresh the displayed content."""
        self.gameStatsText = self.tr("Last winner") + ": {} ({})"
        #         self.setTitle(self.tr('Statistics'))
        self.matchStatsTitleLabel.setText(self.tr("Matches"))
        self.playerStatsTitleLabel.setText(self.tr("Players"))
        self.updateContent()
        self.update()

    def updateContent(self, _game: str | None = None) -> None:
        """Reload statistics from the engine and repopulate every table."""
        # if game is not None: self.game = game
        # self.setTitle(self.tr('Statistics'))
        self.stats.update()
        gamestats = self.stats.getGameStats(self.game)
        matchstats = self.stats.getMatchGameStats(self.game)
        playerstats = self.stats.getPlayerGameStats(self.game)

        if not gamestats:
            self.gameStatsLabel.setText(self.tr("No statistics found"))
            self.playerStatsTitleLabel.hide()
            self.matchStatsTitleLabel.hide()
        else:
            # Show date in local time instead of UTC
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
            displayed = contents  # [:10]
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
                keys = keyorder
                for j, key in enumerate(keys):
                    try:
                        value = row[key]
                    except KeyError:
                        value = "-"
                    item = QTableWidgetItem()
                    if isinstance(value, (int, float)):
                        item.setData(QtCore.Qt.ItemDataRole.DisplayRole, value)
                    else:
                        item.setData(QtCore.Qt.ItemDataRole.DisplayRole, str(value))
                    item.setTextAlignment(
                        QtCore.Qt.AlignmentFlag.AlignVCenter
                        | QtCore.Qt.AlignmentFlag.AlignHCenter
                    )
                    item.setFlags(item.flags() ^ QtCore.Qt.ItemFlag.ItemIsEditable)
                    table.setItem(i, j, item)

            # table.horizontalHeader().setSectionResizeMode(
            #     QHeaderView.ResizeMode.Stretch
            # )
            #            table.setMaximumHeight(table.sizeHint().height())
            #            table.setMinimumHeight(table.rowHeight(0)*2)
            table.setFixedHeight(table.sizeHint().height() + 10)
            table.setMinimumWidth(table.sizeHint().width())

        else:
            table.hide()


class GeneralQuickStats(AbstractQuickStatsBox):
    """Quick-stats box aggregating results across all players."""

    pass


class ParticularQuickStats(AbstractQuickStatsBox):
    """Quick-stats box filtered to a specific set of players."""

    def initEngine(self) -> None:
        """Instantiate the per-player statistics engine for this game."""
        self.stats = registry.create_particular_stats_engine(self.game)

    def updatePlayers(self, players: Sequence[str] | None) -> None:
        if players:
            self.stats.updatePlayers(players)


class StatsTable(QTableWidget):
    """Read-only table with stretched columns and a fitted size hint."""

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.verticalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Fixed)
        # self.setSortingEnabled(True)

    def sizeHint(self) -> QSize:
        """Size the table to its column count and row heights."""
        s = QtCore.QSize()
        s.setWidth(super().sizeHint().width())
        s.setWidth(75 * (self.columnCount() + 1) + 2 * self.columnCount())
        s.setHeight(self.rowHeight(0) * (self.rowCount() + 1) + 10)
        return s


class GameStatsWidget(Tab):
    """Placeholder tab reserved for the full game-statistics view."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._parent = parent
        self.initUI()

    def initUI(self) -> None:
        # Setup Layouts

        self.retranslateUI()

    def retranslateUI(self) -> None:
        pass
