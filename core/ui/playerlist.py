"""Player list widgets and model with drag-drop, favourites and dealer."""

from __future__ import annotations

from typing import Any, cast

from PySide6 import QtCore, QtGui
from PySide6.QtWidgets import (
    QAbstractItemView,
    QDialog,
    QListView,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from core.engine.db import db

standardIcon = ":/icons/player.png"
favouriteIcon = ":/icons/fav.png"
dealerIcon = ":/icons/cards.png"


class PlayerOrderDialog(QDialog):
    """Dialog to reorder players and pick the dealer for a running match."""

    playerOrderChanged = QtCore.Signal()
    dealerChanged = QtCore.Signal()

    def __init__(self, engine: Any, parent: QWidget | None = None) -> None:
        super().__init__(parent)
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

    def getNewDealer(self) -> str | None:
        return self.pow.getDealer()

    def getNewOrder(self) -> list[str]:
        return cast("PlayerListModel", self.pow.model()).retrievePlayers()

    def changeOrder(self) -> None:
        """Accept if the order or dealer changed, otherwise reject."""
        players = cast("PlayerListModel", self.pow.model()).retrievePlayers()
        dealer = self.pow.getDealer()
        if players != self.originalOrder or dealer != self.originalDealer:
            self.accept()
        else:
            self.reject()


class PlayerList(QListView):
    """List view of players supporting drag-drop, favourites and dealer."""

    doubleclickeditem = QtCore.Signal(str)
    changed = QtCore.Signal()

    def __init__(self, engine: Any = None, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.engine = engine
        self.max_players: int | None = None
        self.twin_list: PlayerList | None = None
        self.setStyleSheet("""
        QListView::item:selected {
            background: transparent;
        }
        QListView::item:selected:hover {
            background: rgba(102,102,102,100);
        }
        """)
        self.setDragEnabled(True)
        self.setAcceptDrops(True)
        self.setDropIndicatorShown(True)

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

    def addItem(self, text: str) -> bool:
        """Add ``text`` as a player unless full or already present."""
        if self._canAcceptItem() and not any(
            self._model.item(i).text() == text for i in range(self._model.rowCount())
        ):
            self._model.addPlayer(str(text))
            self.changed.emit()
            return True
        return False

    def _canAcceptItem(self) -> bool:
        model = self.model()
        return self.max_players is None or model.rowCount() < self.max_players

    def dragEnterEvent(self, event: QtGui.QDragEnterEvent) -> None:
        """Accept a drag only while there is room for another player."""
        super().dragEnterEvent(event)
        if self._canAcceptItem():
            event.acceptProposedAction()
        else:
            event.ignore()

    def dragMoveEvent(self, event: QtGui.QDragMoveEvent) -> None:
        """Accept a move drag only while there is room for another player."""
        super().dragMoveEvent(event)
        if self._canAcceptItem():
            event.acceptProposedAction()
        else:
            event.ignore()

    def setMaxPlayers(self, maxp: int | None) -> None:
        self.max_players = maxp

    def setTwinList(self, tl: PlayerList) -> None:
        self.twin_list = tl

    def mouseDoubleClickEvent(self, event: QtGui.QMouseEvent) -> None:
        """Toggle the dealer, or move the item to the twin list, on click."""
        item = self.indexAt(event.pos())
        try:
            player = str(item.data().toString())
        except AttributeError:
            player = str(item.data())
        if player != str(None):
            if self.engine:
                if self._model.dealer:
                    self.setDealer(item, player)
                    self.changed.emit()
            elif self.twin_list:
                if self.twin_list.addItem(player):
                    self._model.removeRows(item.row(), 1)
                    self.twin_list.clearSelection()
                    self.clearSelection()
                self.changed.emit()
        return QListView.mouseDoubleClickEvent(self, event)

    def openMenu(self, position: QtCore.QPoint) -> None:
        """Context menu action: set the dealer or toggle a favourite."""
        item = self.indexAt(position)
        if item.row() < 0:
            return
        try:
            player = str(item.data().toString())
        except AttributeError:
            player = str(item.data())
        if player:
            if self.engine and self.engine.getDealer() is not None:
                self.setDealer(item, player)
            elif not self.engine:
                isfav = not db.isPlayerFavourite(player)
                db.setPlayerFavourite(player, isfav)
                icon = standardIcon
                if isfav:
                    icon = favouriteIcon
                self._model.addIcon(self._model.itemFromIndex(item), icon)

    def setDealer(self, item: QtCore.QModelIndex, player: str) -> None:
        """Move the dealer marker from the current dealer to ``item``."""
        dealer = self._model.dealer
        icon = standardIcon
        if dealer is not None and db.isPlayerFavourite(dealer):
            icon = favouriteIcon
        self._model.addIcon(self._model.itemFromPlayer(dealer), icon)
        self._model.addIcon(self._model.itemFromIndex(item), dealerIcon)
        self._model.dealer = player

    def getDealer(self) -> str | None:
        return self._model.dealer


class PlayerListModel(QtGui.QStandardItemModel):
    """Item model backing a :class:`PlayerList`, tracking the dealer."""

    def __init__(
        self, engine: Any = None, parent: QtCore.QObject | None = None
    ) -> None:
        super().__init__(parent)
        self.engine = engine
        self.dealer: str | None = None

    def addPlayer(self, player: str, row: int | None = None) -> None:
        """Add ``player`` with the right icon at ``row`` (or at the end)."""
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

    def addIcon(self, item: Any, icon: str) -> None:
        item.setIcon(QtGui.QIcon(icon))

    def retrievePlayers(self) -> list[str]:
        """Return the player nicks in their current order."""
        players = []
        for i in range(self.rowCount()):
            nick = str(self.item(i).text())
            players.append(nick)
        return players

    def itemFromPlayer(self, player: str | None) -> QtGui.QStandardItem | None:
        """Return the item whose text matches ``player``, or ``None``."""
        for i in range(self.rowCount()):
            item = self.item(i)
            nick = str(item.text())
            if nick == player:
                return item
        return None
