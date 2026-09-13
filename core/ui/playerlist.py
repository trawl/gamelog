"""Player list widgets and model with drag-drop, favourites and dealer."""

from __future__ import annotations

from typing import Any, cast

from PySide6 import QtCore, QtGui
from PySide6.QtWidgets import (
    QAbstractItemView,
    QDialog,
    QHBoxLayout,
    QListView,
    QPushButton,
    QStyledItemDelegate,
    QStyleOptionViewItem,
    QVBoxLayout,
    QWidget,
)

from core.engine.db import db

standardIcon = ":/icons/player.png"
favouriteIcon = ":/icons/fav.png"
dealerIcon = ":/icons/cards.png"

_COLOUR_INDEX_ROLE = QtCore.Qt.ItemDataRole.UserRole + 1
_SWATCH_SIZE = 22
_SWATCH_MARGIN = 8


class _PlayerColourDelegate(QStyledItemDelegate):
    """Draws a colour swatch on the right of each player row and handles clicks on it."""

    swatchClicked = QtCore.Signal(str)  # emits player nick

    def __init__(
        self, colours: list[QtGui.QColor], parent: QWidget | None = None
    ) -> None:
        super().__init__(parent)
        self._colours = colours

    def _swatchRect(self, option: QStyleOptionViewItem) -> QtCore.QRect:
        r = option.rect
        return QtCore.QRect(
            r.right() - _SWATCH_SIZE - _SWATCH_MARGIN,
            r.top() + (r.height() - _SWATCH_SIZE) // 2,
            _SWATCH_SIZE,
            _SWATCH_SIZE,
        )

    def paint(
        self,
        painter: QtGui.QPainter,
        option: QStyleOptionViewItem,
        index: QtCore.QModelIndex | QtCore.QPersistentModelIndex,
    ) -> None:
        # Shrink the item rect so the standard background/text don't overlap the swatch.
        adjusted = QStyleOptionViewItem(option)
        adjusted.rect = option.rect.adjusted(
            0, 0, -(_SWATCH_SIZE + _SWATCH_MARGIN * 2), 0
        )
        super().paint(painter, adjusted, index)

        ci = index.data(_COLOUR_INDEX_ROLE)
        if ci is not None and self._colours:
            colour = self._colours[int(ci) % len(self._colours)]
            rect = self._swatchRect(option)
            painter.save()
            painter.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing)
            painter.setBrush(QtGui.QBrush(colour))
            painter.setPen(QtGui.QPen(QtGui.QColor(90, 90, 90), 1))
            painter.drawRoundedRect(rect, 4, 4)
            painter.restore()

    def editorEvent(
        self,
        event: QtCore.QEvent,
        model: QtCore.QAbstractItemModel,
        option: QStyleOptionViewItem,
        index: QtCore.QModelIndex | QtCore.QPersistentModelIndex,
    ) -> bool:
        if event.type() == QtCore.QEvent.Type.MouseButtonRelease:
            mouse = cast(QtGui.QMouseEvent, event)
            if self._swatchRect(option).contains(mouse.pos()):
                nick = str(index.data(QtCore.Qt.ItemDataRole.DisplayRole))
                self.swatchClicked.emit(nick)
                return True
        return super().editorEvent(event, model, option, index)

    def sizeHint(
        self,
        option: QStyleOptionViewItem,
        index: QtCore.QModelIndex | QtCore.QPersistentModelIndex,
    ) -> QtCore.QSize:
        hint = super().sizeHint(option, index)
        return QtCore.QSize(
            hint.width() + _SWATCH_SIZE + _SWATCH_MARGIN * 2, hint.height()
        )


class PlayerOrderDialog(QDialog):
    """Dialog to reorder players, pick the dealer, and optionally change colours."""

    playerOrderChanged = QtCore.Signal()
    dealerChanged = QtCore.Signal()

    def __init__(
        self,
        engine: Any,
        parent: QWidget | None = None,
        player_colours: list[QtGui.QColor] | None = None,
        colour_map: dict[str, int] | None = None,
        colour_locked: bool = False,
    ) -> None:
        super().__init__(parent)
        self.engine = engine
        self.originalOrder = self.engine.getListPlayers()
        self.originalDealer = self.engine.getDealer()
        self._player_colours = player_colours or []
        self._colour_map: dict[str, int] = dict(colour_map) if colour_map else {}
        self._colour_locked = colour_locked
        self.setWindowTitle(self.tr("Player Order"))
        self.widgetlayout = QVBoxLayout(self)
        self.pow = PlayerList(self.engine, self)
        self.widgetlayout.addWidget(self.pow)
        if self._player_colours and not colour_locked:
            self._setupColourDelegate()
        self.okbutton = QPushButton("OK", self)
        self.okbutton.clicked.connect(self.changeOrder)
        self.widgetlayout.addWidget(self.okbutton)

    def _setupColourDelegate(self) -> None:
        """Install a colour-swatch delegate on the player list and seed item data."""
        delegate = _PlayerColourDelegate(self._player_colours, self.pow)
        self.pow.setItemDelegate(delegate)
        delegate.swatchClicked.connect(self._pickColour)
        self._delegate = delegate
        self._syncSwatchData()

    def _syncSwatchData(self) -> None:
        """Write current colour_map indices into model items so the delegate can paint them."""
        model = cast("PlayerListModel", self.pow.model())
        for player, ci in self._colour_map.items():
            item = model.itemFromPlayer(player)
            if item is not None:
                item.setData(ci, _COLOUR_INDEX_ROLE)

    def _pickColour(self, player: str) -> None:
        """Open a colour-picker popup for ``player`` and apply the selection."""
        dialog = _ColourPickerDialog(
            self._player_colours, self._colour_map, player, self
        )
        if dialog.exec_():
            chosen_idx = dialog.chosenIndex()
            # Displace any player that currently holds the chosen colour.
            for other, idx in list(self._colour_map.items()):
                if other != player and idx == chosen_idx:
                    # Colours still in use after this pick: exclude chosen_idx (taken by
                    # player) and free player's current colour for the displaced player.
                    taken = set(self._colour_map.values()) - {chosen_idx}
                    taken.discard(self._colour_map.get(player))
                    first_free = next(
                        i for i in range(len(self._player_colours)) if i not in taken
                    )
                    self._colour_map[other] = first_free
                    break
            self._colour_map[player] = chosen_idx
            self._syncSwatchData()

    def getNewDealer(self) -> str | None:
        return self.pow.getDealer()

    def getNewOrder(self) -> list[str]:
        return cast("PlayerListModel", self.pow.model()).retrievePlayers()

    def getNewColourMap(self) -> dict[str, int]:
        return dict(self._colour_map)

    def changeOrder(self) -> None:
        """Accept if the order, dealer, or colours changed, otherwise reject."""
        players = cast("PlayerListModel", self.pow.model()).retrievePlayers()
        dealer = self.pow.getDealer()
        if (
            players != self.originalOrder
            or dealer != self.originalDealer
            or self._colourMapChanged()
        ):
            self.accept()
        else:
            self.reject()

    def _colourMapChanged(self) -> bool:
        original = {p: i for i, p in enumerate(self.originalOrder)}
        return self._colour_map != original


class _ColourPickerDialog(QDialog):
    """Small popup showing all available colours as clickable swatches."""

    def __init__(
        self,
        colours: list[QtGui.QColor],
        colour_map: dict[str, int],
        player: str,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle(self.tr("Choose colour"))
        self._chosen: int | None = None
        layout = QHBoxLayout(self)
        current_idx = colour_map.get(player, 0)
        taken = {idx for p, idx in colour_map.items() if p != player}
        for i, colour in enumerate(colours):
            btn = QPushButton(self)
            btn.setFixedSize(36, 36)
            pixmap = QtGui.QPixmap(28, 28)
            pixmap.fill(colour)
            btn.setIcon(QtGui.QIcon(pixmap))
            btn.setIconSize(QtCore.QSize(28, 28))
            if i == current_idx:
                btn.setStyleSheet("border: 3px solid white;")
            elif i in taken:
                btn.setStyleSheet("border: 1px solid gray;")
            btn.clicked.connect(lambda checked=False, idx=i: self._select(idx))
            layout.addWidget(btn)

    def _select(self, idx: int) -> None:
        self._chosen = idx
        self.accept()

    def chosenIndex(self) -> int:
        return self._chosen if self._chosen is not None else 0


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
