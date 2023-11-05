#!/usr/bin/env python
# -*- coding: utf-8 -*-

from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtWidgets import (QApplication, QFrame, QGroupBox, QHeaderView,
                             QLabel, QScrollArea, QSizePolicy, QSpacerItem,
                             QTabWidget, QTableWidget, QTableWidgetItem,
                             QVBoxLayout, QWidget)
from controllers.enginefactory import StatsEngineFactory
from gui.tab import Tab

i18n = QApplication.translate


class QuickStatsTW(QTabWidget):
    def __init__(self, game, players, parent):
        super(QuickStatsTW, self).__init__(parent)
        self.game = game
        self.players = players
        self.gs = None
        self.ps = None
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
        self.setTabText(self.indexOf(self.gs),
                        i18n("QuickStatsTW", 'General'))
        self.setTabText(self.indexOf(self.ps),
                        i18n("QuickStatsTW", 'Particular'))
        self.gs.retranslateUI()
        self.ps.retranslateUI()

    def update(self, game=None, players=None):
        if game is not None:
            self.game = game
        self.gs.update(game)
        self.ps.updatePlayers(players)
        self.ps.update(game)


class AbstractQuickStatsBox(QGroupBox):

    i18n("AbstractQuickStatsBox", 'Longest')
    i18n("AbstractQuickStatsBox", 'Shortest')
    i18n("AbstractQuickStatsBox", 'Average')
    i18n("AbstractQuickStatsBox", 'Highest')
    i18n("AbstractQuickStatsBox", 'Lowest')
    i18n("AbstractQuickStatsBox", 'Average')
    i18n("AbstractQuickStatsBox", 'Played')
    i18n("AbstractQuickStatsBox", 'Victories')
    i18n("AbstractQuickStatsBox", 'Ratio (%)')
    i18n("AbstractQuickStatsBox", 'Highest')
    i18n("AbstractQuickStatsBox", 'Lowest')
    i18n("AbstractQuickStatsBox", 'Average')
    i18n("AbstractQuickStatsBox", 'Total')

    def __init__(self, game, parent):
        super(AbstractQuickStatsBox, self).__init__(parent)
        self.stats = None
        self.game = game
        self.initEngine()

        self.matchStatsKeys = ['maxduration', 'minduration',
                               'avgduration', 'maxscore',
                               'minscore', 'avgscore']
        self.matchStatsHeaders = ['Longest', 'Shortest',
                                  'Average', 'Highest',
                                  'Lowest', 'Average']

        self.playerStatsKeys = ['played', 'victories', 'victoryp',
                                'maxscore', 'minscore', 'avgscore', 'sumscore']
        self.playerStatsHeaders = ['Played', 'Victories', 'Ratio (%)',
                                   'Highest', 'Lowest', 'Average', 'Total']

        self.initUI()

        sp = QSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.Expanding)
        self.setSizePolicy(sp)

    def initEngine(self):
        self.stats = StatsEngineFactory.getStatsEngine(self.game)

    def initUI(self):
        self.superlayout = QVBoxLayout(self)
        self.scrollarea = QScrollArea()
        self.scrollarea.setWidgetResizable(True)
        self.scrollarea.setFrameShape(QFrame.NoFrame)
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
        self.gameStatsText = i18n(
            "AbstractQuickStatsBox", 'Last winner') + ": {} ({})"
#         self.setTitle(i18n("QuickStatsBox", 'Statistics'))
        self.matchStatsTitleLabel.setText(
            i18n("AbstractQuickStatsBox", "Matches"))
        self.playerStatsTitleLabel.setText(
            i18n("AbstractQuickStatsBox", "Players"))
        self.update()

    def update(self, game=None):
        # if game is not None: self.game = game
        # self.setTitle(i18n("QuickStatsBox", 'Statistics'))
        self.stats.update()
        gamestats = self.stats.getGameStats(self.game)
        matchstats = self.stats.getMatchGameStats(self.game)
        playerstats = self.stats.getPlayerGameStats(self.game)

        if not gamestats:
            self.gameStatsLabel.setText(i18n(
                "AbstractQuickStatsBox", "No statistics found"))
            self.playerStatsTitleLabel.hide()
            self.matchStatsTitleLabel.hide()
        else:
            self.gameStatsLabel.setText(self.gameStatsText.format(
                gamestats['lastwinner'], gamestats['lastwinnerdate']))
            self.playerStatsTitleLabel.show()
            self.matchStatsTitleLabel.show()
        headers = [i18n(
            "AbstractQuickStatsBox", h) for h in self.matchStatsHeaders]
        self.updateTable(self.matchStatsTable, matchstats,
                         self.matchStatsKeys, 'nplayers', headers)

        headers = [i18n(
            "AbstractQuickStatsBox", h) for h in self.playerStatsHeaders]
        self.updateTable(self.playerStatsTable, playerstats,
                         self.playerStatsKeys, 'nick', headers)

    def updateTable(self, table, contents, keyorder, rowheaderkey, cheaders):
        table.clear()
        if len(contents) and len(contents[0]) > 1:
            table.show()
            displayed = contents  # [:10]
            table.setRowCount(len(displayed))
            table.setColumnCount(len(cheaders))
            table.setHorizontalHeaderLabels(cheaders)
            vheaders = [str(row[rowheaderkey]) for row in displayed]
            table.setVerticalHeaderLabels(vheaders)

            for i, row in enumerate(displayed):
                keys = keyorder
                for j, key in enumerate(keys):
                    item = QTableWidgetItem(str(row[key]))
                    item.setTextAlignment(
                        QtCore.Qt.AlignVCenter | QtCore.Qt.AlignHCenter)
                    item.setFlags(item.flags() ^ QtCore.Qt.ItemIsEditable)
                    table.setItem(i, j, item)

            table.horizontalHeader().setSectionResizeMode(
                QHeaderView.Stretch)
#            table.setMaximumHeight(table.sizeHint().height())
#            table.setMinimumHeight(table.rowHeight(0)*2)
            table.setFixedHeight(table.sizeHint().height())
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
    def sizeHint(self):
        s = QtCore.QSize()
        s.setWidth(super(StatsTable, self).sizeHint().width())
        s.setWidth(75*(self.columnCount()+1)+2*self.columnCount())
        s.setHeight(self.rowHeight(0)*(self.rowCount()+1)+10)
        return s


class GameStatsWidget(Tab):
    def __init__(self, parent=None):
        super(GameStatsWidget, self).__init__(parent)
        self.parent = parent
        self.initUI()

    def initUI(self):

        # Setup Layouts

        self.retranslateUI()

    def retranslateUI(self):
        pass
