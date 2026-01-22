#!/usr/bin/env python
# -*- coding: utf-8 -*-

from PySide6 import QtCore
from PySide6.QtCore import QCoreApplication
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

from controllers.enginefactory import StatsEngineFactory
from gui.tab import Tab


class QuickStatsTW(QTabWidget):
    def __init__(self, game, players, parent):
        super(QuickStatsTW, self).__init__(parent)
        self.game = game
        self.players = players
        self.initUI()

    def initStatsWidgets(self):
        self.gs = GeneralQuickStats(self.game, self)
        self.ps = ParticularQuickStats(self.game, self)

    def initUI(self):
        self.initStatsWidgets()
        try:
            self.ps.updatePlayers(self.players)
        except Exception:
            pass
        self.addTab(self.gs, "")
        self.addTab(self.ps, "")
        self.retranslateUI()

    def retranslateUI(self):
        self.setTabText(self.indexOf(self.gs), self.tr("General"))
        self.setTabText(self.indexOf(self.ps), self.tr("Particular"))
        self.gs.retranslateUI()
        self.ps.retranslateUI()

    def updateContent(self, game=None, players=None):
        if game is not None:
            self.game = game
        self.gs.updateContent(game)
        self.ps.updatePlayers(players)
        self.ps.updateContent(game)


class AbstractQuickStatsBox(QGroupBox):
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

    def __init__(self, game, parent):
        super(AbstractQuickStatsBox, self).__init__(parent)
        # self.stats = None
        self.game = game
        self.initEngine()

        self.matchStatsKeys = [
            "maxduration",
            "minduration",
            "avgduration",
            "maxscore",
            "minscore",
            "avgscore",
        ]
        self.matchStatsHeaders = [
            "Longest",
            "Shortest",
            "Average",
            "Highest",
            "Lowest",
            "Average",
        ]

        self.playerStatsKeys = [
            "played",
            "victories",
            "victoryp",
            "maxscore",
            "minscore",
            "avgscore",
            "sumscore",
        ]
        self.playerStatsHeaders = [
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

    def initEngine(self):
        self.stats = StatsEngineFactory.getStatsEngine(self.game)

    def initUI(self):
        self.superlayout = QVBoxLayout(self)
        self.scrollarea = QScrollArea()
        self.scrollarea.setWidgetResizable(True)
        self.scrollarea.setFrameShape(QFrame.Shape.NoFrame)
        self.superlayout.addWidget(self.scrollarea)
        self.container = QWidget(self)
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

        #         self.stretch = QSpacerItem(0,0)
        #         self.widgetLayout.addSpacerItem(self.stretch)
        self.widgetLayout.addStretch()
        self.retranslateUI()

    def retranslateUI(self):
        self.gameStatsText = self.tr("Last winner") + ": {} ({})"
        #         self.setTitle(self.tr('Statistics'))
        self.matchStatsTitleLabel.setText(self.tr("Matches"))
        self.playerStatsTitleLabel.setText(self.tr("Players"))
        self.updateContent()
        self.update()

    def updateContent(self, _game=None):
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
            self.gameStatsLabel.setText(
                self.gameStatsText.format(
                    gamestats["lastwinner"], gamestats["lastwinnerdate"]
                )
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

    def updateTable(self, table, contents, keyorder, rowheaderkey, cheaders):
        table.clear()
        if contents and len(contents[0]) > 1:
            table.show()
            displayed = contents  # [:10]
            table.setRowCount(len(displayed))
            table.setColumnCount(len(cheaders))
            table.setHorizontalHeaderLabels(cheaders)
            # table.verticalHeader().setVisible(False)
            vheaders = [str(row[rowheaderkey]) for row in displayed]
            table.setVerticalHeaderLabels(vheaders)

            for i, row in enumerate(displayed):
                keys = keyorder
                # keys = [
                #     rowheaderkey,
                # ] + keyorder
                for j, key in enumerate(keys):
                    item = QTableWidgetItem(str(row[key]))
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
    pass


class ParticularQuickStats(AbstractQuickStatsBox):
    def initEngine(self):
        self.stats = StatsEngineFactory.getParticularStatsEngine(self.game)

    def updatePlayers(self, players):
        if players:
            self.stats.updatePlayers(players)


class StatsTable(QTableWidget):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setStyleSheet("""
            QTableView {
                background: transparent;
                gridline-color: rgba(255, 255, 255, 120);
                color: white;
                selection-background-color: rgba(120, 180, 255, 80);
                selection-color: white;
            }

            QTableView::viewport {
                background: transparent;
            }

            /* Cells */
            QTableView::item {
                background: transparent;
                padding: 4px 6px;
            }

            /* Selected cell
            QTableView::item:selected {
                background: rgba(255, 255, 255, 40);
            } */

            /* Headers */
            QHeaderView::section {
                background: qlineargradient(
                    x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(255, 255, 255, 60),
                    stop:1 rgba(255, 255, 255, 20)
                );
                color: white;
                padding: 6px 8px;
                border-top: 1px solid rgba(255, 255, 255, 120);
                border-bottom: 1px solid rgba(255, 255, 255, 180);
                border-left: 1px solid rgba(255, 255, 255, 80);
                border-right: 1px solid rgba(255, 255, 255, 80);
                font-weight: 600;
            }

            /* Remove double border between adjacent headers */
            QHeaderView::section:horizontal {
                margin-left: -1px;
            }

            /* Corner button (top-left square) */
            QTableCornerButton::section {
                background: rgba(255, 255, 255, 30);
                border: 1px solid rgba(255, 255, 255, 120);
            }

            /* Optional: hover feedback */
            QTableView::item:hover {
                background: rgba(255, 255, 255, 20);
            }
            """)
        self.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.verticalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Fixed)
        # self.setSortingEnabled(True)

    def sizeHint(self):
        s = QtCore.QSize()
        s.setWidth(super(StatsTable, self).sizeHint().width())
        s.setWidth(75 * (self.columnCount() + 1) + 2 * self.columnCount())
        s.setHeight(self.rowHeight(0) * (self.rowCount() + 1) + 10)
        return s


class GameStatsWidget(Tab):
    def __init__(self, parent=None):
        super(GameStatsWidget, self).__init__(parent)
        self._parent = parent
        self.initUI()

    def initUI(self):
        # Setup Layouts

        self.retranslateUI()

    def retranslateUI(self):
        pass
