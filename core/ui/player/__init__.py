"""core.ui.player — player-list and order sub-package.

Re-exports all public names for backward-compatible imports.
"""

from core.ui.player.list import PlayerList, PlayerListModel
from core.ui.player.new import NewPlayerDialog
from core.ui.player.order import PlayerOrderDialog

__all__ = [
    "NewPlayerDialog",
    "PlayerList",
    "PlayerListModel",
    "PlayerOrderDialog",
]
