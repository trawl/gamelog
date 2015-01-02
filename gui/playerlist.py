#!/usr/bin/env python
# -*- coding: utf-8 -*-

try:
    from PyQt4 import QtCore,QtGui
    QtCore.Signal = QtCore.pyqtSignal
    QtCore.Slot = QtCore.pyqtSlot
except ImportError as error:
    from PySide import QtCore,QtGui
    QtGui.QFileDialog.getOpenFileNameAndFilter = QtGui.QFileDialog.getOpenFileName
    
from controllers.db import db

standardIcon = 'icons/player.png'
favouriteIcon =  'icons/fav.png'
dealerIcon =  'icons/cards.png'        

class PlayerOrderDialog(QtGui.QDialog):
     
    playerOrderChanged = QtCore.Signal()
    dealerChanged = QtCore.Signal()
     
    def __init__(self,engine,parent=None):
        super(PlayerOrderDialog,self).__init__(parent)
        self.engine = engine
        self.originalOrder = self.engine.getListPlayers()
        self.originalDealer = self.engine.getDealer()
        self.setWindowTitle(QtGui.QApplication.translate("PlayerOrderDialog",'Player Order'))
        self.widgetlayout = QtGui.QVBoxLayout(self)
        self.pow = PlayerList(self.engine,self)
        self.okbutton = QtGui.QPushButton("OK",self)
        self.okbutton.clicked.connect(self.changeOrder)
        self.widgetlayout.addWidget(self.pow)
        self.widgetlayout.addWidget(self.okbutton)
        
    def getNewDealer(self): return self.pow.getDealer()
    
    def getNewOrder(self): return self.pow.model().retrievePlayers()
    
    def changeOrder(self):
        players = self.pow.model().retrievePlayers()
        dealer = self.pow.getDealer()
        if players != self.originalOrder or dealer != self.originalDealer: 
            self.accept()
        else: 
            self.reject()
        
class PlayerList(QtGui.QListView):
    
    doubleclickeditem = QtCore.Signal(str)
    
    def __init__(self,engine=None, parent=None):
        super(PlayerList, self).__init__(parent)
        self.engine = engine
        self.dealer = None
        self.setDragEnabled(True)
        self.setAcceptDrops(True)
        self.setModel(PlayerListModel(engine))
        
        if self.engine: 
            self.dealer = self.engine.getDealer()
            for player in self.engine.getListPlayers():
                self.model().addPlayer(player)

        self.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.openMenu)

    def dropEvent(self, e):
        e.setDropAction(QtCore.Qt.MoveAction)
        QtGui.QListView.dropEvent(self,e)
            
    def addItem(self,text): self.model().addPlayer(text)

    def mouseDoubleClickEvent(self,event):
        item = self.indexAt(event.pos())
        try: player = str(item.data().toString())
        except AttributeError: player = str(item.data())
        if player != str(None):
            self.doubleclickeditem.emit(player)
            if self.dealer:
                self.setDealer(item,player)
            else:
                self.model().removeRows(item.row(),1)
        return QtGui.QListView.mouseDoubleClickEvent(self,event)
    
    def openMenu(self,position):
        
        item = self.indexAt(position)
        if item.row()<0: return
        try: player = str(item.data().toString())
        except AttributeError: player = str(item.data())
        if player:
            menu = QtGui.QMenu()
            isfav =  db.isPlayerFavourite(player)
            if isfav:
                favouriteAction = QtGui.QAction(QtGui.QIcon(standardIcon),QtGui.QApplication.translate("PlayerList","Unset Favourite"), self)
            else:
                favouriteAction = QtGui.QAction(QtGui.QIcon(favouriteIcon),QtGui.QApplication.translate("PlayerList","Set Favourite"), self)
            menu.addAction(favouriteAction)
            dealerAction = None
            if self.engine and player != self.engine.getDealer():
                dealerAction = QtGui.QAction( QtGui.QIcon(dealerIcon),QtGui.QApplication.translate("PlayerList","Set dealer"), self)
                menu.addAction(dealerAction)
            action = menu.exec_(self.mapToGlobal(position))
            if action == favouriteAction:
                isfav = not isfav
                db.setPlayerFavourite(player,isfav)
                icon = standardIcon
                if isfav: icon = favouriteIcon
                self.model().addIcon(self.model().itemFromIndex(item),icon)
            elif self.engine and action == dealerAction:
                self.setDealer(item, player)

                
    def setDealer(self,item,player):
        icon = standardIcon
        if db.isPlayerFavourite(self.dealer): icon = favouriteIcon
        self.model().addIcon(self.model().itemFromPlayer(self.dealer), icon)
        self.model().addIcon(self.model().itemFromIndex(item),dealerIcon)
        self.dealer = player
        
    def getDealer(self): return self.dealer
    

class PlayerListModel(QtGui.QStandardItemModel):
    
    def __init__(self, engine=None, parent = None):
        super(PlayerListModel, self).__init__( parent)
        self.engine = engine
        
    def dropMimeData(self, data, action, row, column, parent):

        if data.hasFormat('application/x-qabstractitemmodeldatalist'):
            barray = data.data('application/x-qabstractitemmodeldatalist')
            data_items = self.decode_data(barray)

            # Assuming that we get at least one item, and that it defines
            # text that we can display.
            try:
                text = data_items[0][QtCore.Qt.DisplayRole].toString()
            except AttributeError:
                text = str(data_items[0][QtCore.Qt.DisplayRole])

#            self.appendRow(QtGui.QStandardItem(text))
            self.addPlayer(text,row)
            return True
        else:
            return QtGui.QStandardItemModel.dropMimeData(self, data, action, row, column, parent)

    def decode_data(self, barray):
        data = []
        item = {}
        ds = QtCore.QDataStream(barray)
        while not ds.atEnd():
            ds.readInt32() #Row 
            ds.readInt32() #Column
            map_items = ds.readInt32()
            for _ in range(map_items):
                key = ds.readInt32()
                try:
                    value = QtCore.QVariant()
                    ds >> value
                except (AttributeError,TypeError):
                    value = ds.readQVariant()
                item[QtCore.Qt.ItemDataRole(key)] = value
            data.append(item)
        return data
    
    def addPlayer(self,player,row=None):
        item = QtGui.QStandardItem(player)
        item.setEditable(False)
        item.setDropEnabled(False)
        font = item.font()
        font.setPixelSize(24)
        font.setBold(True)
        item.setFont(font)
        icon = standardIcon
        if self.engine and self.engine.getDealer() == player:
            icon = dealerIcon
        elif db.isPlayerFavourite(player): 
            icon = favouriteIcon
        self.addIcon(item,icon)
        if row is not None and row>=0:
            self.insertRow(row,item)
        else:        
            self.appendRow(item)
        
    def addIcon(self,item,icon):
        item.setIcon(QtGui.QIcon(icon))

    def retrievePlayers(self):
        players = list()
        for i in range(self.rowCount()):
            nick =str(self.item(i).text())
            players.append(nick)
        return players
    
    def itemFromPlayer(self,player):
        for i in range(self.rowCount()):
            item = self.item(i)
            nick =str(item.text())
            if nick == player:
                return item
        return None
    
# class PlayerOrderList(PlayerList):
#     
#     def __init__(self,engine,parent=None):
#         super(PlayerOrderList,self).__init__(parent)
#         self.engine = engine
#         
#         
#         
# class PlayerOrderModel(PlayerListModel):
#     
#     pass
# 
#             
# 
#     
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
        