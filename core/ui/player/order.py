"""Player-order dialog: reorder, pick dealer and change colours."""

from __future__ import annotations

from typing import Any, cast

from PySide6 import QtCore, QtGui
from PySide6.QtWidgets import QDialog, QPushButton, QVBoxLayout, QWidget

from core.ui.player.colour import _ColourPickerDialog
from core.ui.player.list import _COLOUR_INDEX_ROLE, PlayerList, PlayerListModel


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
        from core.ui.player.list import _PlayerColourDelegate

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
            for other, idx in list(self._colour_map.items()):
                if other != player and idx == chosen_idx:
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


__all__ = ["PlayerOrderDialog"]
