#!/usr/bin/env python
# -*- coding: utf-8 -*-
from typing import cast

from PySide6 import QtCore, QtGui
from PySide6.QtGui import QAction
from PySide6.QtWidgets import (
    QAbstractItemView,
    QDialog,
    QListView,
    QMenu,
    QPushButton,
    QVBoxLayout,
)

from controllers.db import db

standardIcon = "icons/player.png"
favouriteIcon = "icons/fav.png"
dealerIcon = "icons/cards.png"


class PlayerOrderDialog(QDialog):
    playerOrderChanged = QtCore.Signal()
    dealerChanged = QtCore.Signal()

    def __init__(self, engine, parent=None):
        super(PlayerOrderDialog, self).__init__(parent)
        self.engine = engine
        self.originalOrder = self.engine.getListPlayers()
        self.originalDealer = self.engine.getDealer()
        self.setWindowTitle(self.tr("Player Order"))
        self.widgetlayout = QVBoxLayout(self)
        self.pow = PlayerList(self.engine, self)
        self.okbutton = QPushButton("OK", self)
        self.okbutton.clicked.connect(self.changeOrder)
        self.widgetlayout.addWidget(self.pow)
        self.widgetlayout.addWidget(self.okbutton)

    def getNewDealer(self):
        return self.pow.getDealer()

    def getNewOrder(self):
        return cast("PlayerListModel", self.pow.model()).retrievePlayers()

    def changeOrder(self):
        players = cast("PlayerListModel", self.pow.model()).retrievePlayers()
        dealer = self.pow.getDealer()
        if players != self.originalOrder or dealer != self.originalDealer:
            self.accept()
        else:
            self.reject()


class PlayerList(QListView):
    doubleclickeditem = QtCore.Signal(str)
    changed = QtCore.Signal()

    def __init__(self, engine=None, parent=None):
        super(PlayerList, self).__init__(parent)
        self.engine = engine
        self.setStyleSheet("""
        QListView {
            background: transparent;
        }
        QListView::viewport {
            background: transparent;
        }
        QListView::item {
            padding: 5px 5px;
        }
        QListView::item:selected {
            background: transparent;
            border-radius: 6px;
        }
        """)
        self.setDragEnabled(True)
        self.setAcceptDrops(True)
        # self.setDropIndicatorShown(True)

        self.setDragDropMode(QAbstractItemView.DragDropMode.DragDrop)
        self.setDefaultDropAction(QtCore.Qt.DropAction.MoveAction)

        self.setSpacing(3)
        self.setModel(PlayerListModel(engine))
        self._model = cast("PlayerListModel", self.model())

        if self.engine:
            self._model.dealer = self.engine.getDealer()
            for player in self.engine.getListPlayers():
                self._model.addPlayer(player)

        self.setContextMenuPolicy(QtCore.Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self.openMenu)

    def addItem(self, text):
        self._model.addPlayer(text)
        self.changed.emit()

    def mouseDoubleClickEvent(self, event):
        item = self.indexAt(event.pos())
        try:
            player = str(item.data().toString())
        except AttributeError:
            player = str(item.data())
        if player != str(None):
            self.doubleclickeditem.emit(player)

            if self.engine:
                if self._model.dealer:
                    self.setDealer(item, player)
            else:
                self._model.removeRows(item.row(), 1)
                self.changed.emit()
        return QListView.mouseDoubleClickEvent(self, event)

    def openMenu(self, position):
        item = self.indexAt(position)
        if item.row() < 0:
            return
        try:
            player = str(item.data().toString())
        except AttributeError:
            player = str(item.data())
        if player:
            menu = QMenu()
            isfav = db.isPlayerFavourite(player)
            if isfav:
                favouriteAction = QAction(
                    QtGui.QIcon(standardIcon),
                    self.tr("Unset Favourite"),
                    self,
                )
            else:
                favouriteAction = QAction(
                    QtGui.QIcon(favouriteIcon),
                    self.tr("Set Favourite"),
                    self,
                )
            menu.addAction(favouriteAction)
            dealerAction = None
            if (
                self.engine
                and self.engine.getDealer() is not None
                and player != self._model.dealer
            ):
                dealerAction = QAction(
                    QtGui.QIcon(dealerIcon), self.tr("Set dealer"), self
                )
                menu.addAction(dealerAction)
            if dealerAction is not None:
                action = menu.exec_(self.mapToGlobal(position))
            else:
                action = favouriteAction
            if action is None:
                return
            elif action == favouriteAction:
                isfav = not isfav
                db.setPlayerFavourite(player, isfav)
                icon = standardIcon
                if isfav:
                    icon = favouriteIcon
                self._model.addIcon(self._model.itemFromIndex(item), icon)
            elif self.engine and action == dealerAction:
                self.setDealer(item, player)

    def setDealer(self, item, player):
        icon = standardIcon
        if db.isPlayerFavourite(self._model.dealer):
            icon = favouriteIcon
        self._model.addIcon(self._model.itemFromPlayer(self._model.dealer), icon)
        self._model.addIcon(self._model.itemFromIndex(item), dealerIcon)
        self._model.dealer = player

    def getDealer(self):
        return self._model.dealer


class PlayerListModel(QtGui.QStandardItemModel):
    def __init__(self, engine=None, parent=None):
        super(PlayerListModel, self).__init__(parent)
        self.engine = engine
        self.dealer = None

    def addPlayer(self, player, row=None):
        item = QtGui.QStandardItem(player)
        item.setEditable(False)
        item.setDropEnabled(False)
        font = item.font()
        font.setPixelSize(18)
        font.setBold(True)
        item.setFont(font)
        icon = standardIcon
        if self.engine and self.dealer == player:
            icon = dealerIcon
        elif db.isPlayerFavourite(player):
            icon = favouriteIcon
        self.addIcon(item, icon)
        if row is not None and row >= 0:
            self.insertRow(row, item)
        else:
            self.appendRow(item)

    def addIcon(self, item, icon):
        item.setIcon(QtGui.QIcon(icon))

    def retrievePlayers(self):
        players = list()
        for i in range(self.rowCount()):
            nick = str(self.item(i).text())
            players.append(nick)
        return players

    def itemFromPlayer(self, player):
        for i in range(self.rowCount()):
            item = self.item(i)
            nick = str(item.text())
            if nick == player:
                return item
        return None
