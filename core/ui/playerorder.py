"""Dialog and widgets for viewing/arranging the player order."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from PySide6.QtWidgets import (
    QDialog,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QVBoxLayout,
    QWidget,
)

if TYPE_CHECKING:
    from PySide6.QtGui import QDragEnterEvent

    from core.engine.base import GameEngine


class PlayerOrderDialog(QDialog):
    """Modal dialog wrapping the player-order widget for a match."""

    def __init__(self, engine: GameEngine, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.engine = engine
        self.setWindowTitle(self.tr("Player Order"))
        self.widgetlayout = QVBoxLayout(self)
        self.pow = PlayerOrderWidget(self.engine, self)
        self.widgetlayout.addWidget(self.pow)


class PlayerOrderWidget(QWidget):
    """Vertical stack of draggable player tiles for reordering."""

    def __init__(self, engine: GameEngine, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.engine = engine
        self.players = self.engine.getListPlayers()
        self.widgetLayout = QVBoxLayout(self)
        self.setAcceptDrops(True)
        for player in self.players:
            self.widgetLayout.addWidget(
                PlayerTile(player, self.engine.getDealer() == player, self)
            )

    def dragEnterEvent(self, event: QDragEnterEvent) -> None:
        event.accept()

    # def dropEvent(self, event):
    #     print("'%s' was dropped onto me." % event)


logger = logging.getLogger(__name__)


class PlayerTile(QGroupBox):
    """A single player's tile, flagged when that player is the dealer."""

    def __init__(
        self, player: str, isDealer: bool = False, parent: QWidget | None = None
    ) -> None:
        logger.debug("Creating tile for %s", player)
        super().__init__(parent)
        self.player = player
        self.isDealer = isDealer
        self.widgetLayout = QHBoxLayout(self)
        self.playerLabel = QLabel(self)
        self.widgetLayout.addWidget(self.playerLabel)
        self.playerLabel.setText(self.player)

    # def dragEnterEvent(self, event):
    #     print("{} drag enter".format(self.player))
