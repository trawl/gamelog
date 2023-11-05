#!/usr/bin/env python
# -*- coding: utf-8 -*-

try:
    from PyQt4 import QtCore,QtGui
    QtCore.Signal = QtCore.pyqtSignal
    QtCore.Slot = QtCore.pyqtSlot
except ImportError as error:
    from PySide import QtCore,QtGui
    QtGui.QFileDialog.getOpenFileNameAndFilter = QtGui.QFileDialog.getOpenFileName

    
class PlayerOrderDialog(QtGui.QDialog):
    
    def __init__(self,engine,parent=None):
        super(PlayerOrderDialog,self).__init__(parent)
        self.engine = engine
        self.setWindowTitle(QtGui.QApplication.translate("PlayerOrderDialog",'Player Order'))
        self.widgetlayout = QtGui.QVBoxLayout(self)
        self.pow = PlayerOrderWidget(self.engine,self)
        self.widgetlayout.addWidget(self.pow)

        
class PlayerOrderWidget(QtGui.QWidget):
    
    def __init__(self,engine,parent=None):
        super(PlayerOrderWidget,self).__init__(parent)
        self.engine = engine
        self.players = self.engine.getListPlayers()
        self.widgetLayout = QtGui.QVBoxLayout(self)
        self.setAcceptDrops(True)
        for player in self.players:
            self.widgetLayout.addWidget(PlayerTile(player,self.engine.getDealer()==player,self))
            
    def dragEnterEvent(self, event):
        event.accept()
        
    def dropEvent(self, event):
        print("'%s' was dropped onto me." % event) 
        

class PlayerTile(QtGui.QGroupBox): 
    def __init__(self,player,isDealer=False,parent=None):
        print("Creaing tile for {}".format(player))
        super(PlayerTile,self).__init__(parent)
        self.player = player
        self.isDealer = isDealer
        self.widgetLayout = QtGui.QHBoxLayout(self)
        self.playerLabel = QtGui.QLabel(self)
        self.widgetLayout.addWidget(self.playerLabel)
        self.playerLabel.setText(self.player)
        
    def dragEnterEvent(self,event):
        print("{} drag enter".format(self.player))
            

if __name__ == "__main__":
    import sys
    from controllers.db import db
    from controllers.enginefactory import GameEngineFactory 
    db.connectDB()
    app = QtGui.QApplication(sys.argv)
    engine = GameEngineFactory.createMatch('Pocha')
    players = ['Xavi','Rosa','Dani']
    for p in players: engine.addPlayer(p)
    engine.begin()
    mw = PlayerOrderDialog(engine)
    mw.show()
    sys.exit(app.exec_())
        