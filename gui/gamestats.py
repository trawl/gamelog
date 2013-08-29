#!/usr/bin/env python
# -*- coding: utf-8 -*-
try:
    from PySide import QtCore,QtGui
    QtGui.QFileDialog.getOpenFileNameAndFilter = QtGui.QFileDialog.getOpenFileName
except ImportError as error:
    from PyQt4 import QtCore,QtGui
    QtCore.Signal = QtCore.pyqtSignal
    QtCore.Slot = QtCore.pyqtSlot

from controllers.enginefactory import StatsEngineFactory
from gui.tab import Tab

class QuickStatsBox(QtGui.QGroupBox):
    
    def __init__(self,game,parent):
        super(QuickStatsBox, self).__init__(parent)
        self.stats = StatsEngineFactory.getStatsEngine(game)
        self.game = game
        self.initUI()

        sp = QtGui.QSizePolicy(QtGui.QSizePolicy.Preferred,QtGui.QSizePolicy.Expanding)
        self.setSizePolicy(sp)
        
    def initUI(self):
        self.widgetLayout = QtGui.QVBoxLayout(self)
        self.gameStatsLabel = QtGui.QLabel(self)
        self.widgetLayout.addWidget(self.gameStatsLabel)
        
        self.matchStatsTitleLabel = QtGui.QLabel(self)
        self.widgetLayout.addWidget(self.matchStatsTitleLabel)
        self.matchStatsTable = StatsTable(self)
        self.widgetLayout.addWidget(self.matchStatsTable)
        
        self.playerStatsTitleLabel = QtGui.QLabel(self)
        self.widgetLayout.addWidget(self.playerStatsTitleLabel)
        self.playerStatsTable = StatsTable(self)
        self.widgetLayout.addWidget(self.playerStatsTable)
        
#         self.stretch = QtGui.QSpacerItem(0,0)
#         self.widgetLayout.addSpacerItem(self.stretch)
        self.widgetLayout.addStretch()
        self.retranslateUI()
        
    def retranslateUI(self):
        self.gameStatsText = QtGui.QApplication.translate("QuickStatsBox",'Last winner') + ": {} ({})"
#         self.setTitle(QtGui.QApplication.translate("QuickStatsBox",'Statistics'))
        self.matchStatsTitleLabel.setText(QtGui.QApplication.translate("QuickStatsBox","Matches"))
        self.playerStatsTitleLabel.setText(QtGui.QApplication.translate("QuickStatsBox","Players"))
        self.update()
        
    def update(self,game=None):
        if game is not None: self.game = game
#         self.setTitle(QtGui.QApplication.translate("QuickStatsBox",'Statistics'))
        self.stats.update()
        gamestats = self.stats.getGameStats(self.game)
        matchstats = self.stats.getMatchGameStats(self.game)
        playerstats = self.stats.getPlayerGameStats(self.game)
        
        if not gamestats:
            self.gameStatsLabel.setText(QtGui.QApplication.translate("QuickStatsBox","No statistics found"))
            self.playerStatsTitleLabel.hide()
            self.matchStatsTitleLabel.hide()
        else:
            self.gameStatsLabel.setText(self.gameStatsText.format(gamestats['lastwinner'],gamestats['lastwinnerdate']))
            self.playerStatsTitleLabel.show()
            self.matchStatsTitleLabel.show()
        keys = ['maxduration','minduration','avgduration','maxscore','minscore','avgscore']
        headers = [QtGui.QApplication.translate("QuickStatsBox",'Longest'),QtGui.QApplication.translate("QuickStatsBox",'Shortest'),QtGui.QApplication.translate("QuickStatsBox",'Average'),QtGui.QApplication.translate("QuickStatsBox",'Highest'),QtGui.QApplication.translate("QuickStatsBox",'Lowest'),QtGui.QApplication.translate("QuickStatsBox",'Average')]
        self.updateTable(self.matchStatsTable, matchstats, keys, 'nplayers', headers)
            
        keys = ['played','victories','victoryp','maxscore','minscore','avgscore','sumscore']
        headers = [QtGui.QApplication.translate("QuickStatsBox",'Played'),QtGui.QApplication.translate("QuickStatsBox",'Victories'),QtGui.QApplication.translate("QuickStatsBox",'Ratio (%)'),QtGui.QApplication.translate("QuickStatsBox",'Highest'),QtGui.QApplication.translate("QuickStatsBox",'Lowest'),QtGui.QApplication.translate("QuickStatsBox",'Average'),QtGui.QApplication.translate("QuickStatsBox",'Total')]
        self.updateTable(self.playerStatsTable, playerstats, keys, 'nick', headers)
                           

    def updateTable(self,table,contents,keyorder,rowheaderkey,cheaders):
        table.clear()
        if len(contents) and len(contents[0])>1:
            table.show()
            displayed = contents#[:10]
            table.setRowCount(len(displayed))
            table.setColumnCount(len(cheaders))
            table.setHorizontalHeaderLabels(cheaders)
            vheaders = [str(row[rowheaderkey]) for row in displayed]
            table.setVerticalHeaderLabels(vheaders)
            
            for i, row in enumerate(displayed):
                keys = keyorder
                for j, key in enumerate(keys):
                    item = QtGui.QTableWidgetItem(str(row[key]))
                    item.setTextAlignment(QtCore.Qt.AlignVCenter|QtCore.Qt.AlignHCenter)
                    item.setFlags(item.flags()^QtCore.Qt.ItemIsEditable)
                    table.setItem(i,j,item)
                    
            table.horizontalHeader().setResizeMode(QtGui.QHeaderView.Stretch)            
            table.setMaximumHeight(table.sizeHint().height())

        else:
            table.hide()

class StatsTable(QtGui.QTableWidget):
    def sizeHint(self):
        s = QtCore.QSize()
        s.setWidth(super(StatsTable,self).sizeHint().height())
        s.setHeight(self.rowHeight(0)*(self.rowCount()+1)+2)
        return s
        

class GameStatsWidget(Tab):
    def __init__(self, parent=None):
        super(GameStatsWidget, self).__init__(parent)
        self.parent = parent
        self.initUI()   

    def initUI(self):

        #Setup Layouts
        
        self.retranslateUI()
    
    def retranslateUI(self):
        pass
        
