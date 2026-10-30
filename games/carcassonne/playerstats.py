"""Cards the player statistics show for a player in Carcassonne."""

from __future__ import annotations

from PySide6.QtCore import QCoreApplication

from core.engine.db import db
from core.engine.playerstats import PlayerStat
from games.carcassonne.engine import CarcassonneStatsQueries


def player_stats(game: str, nick: str) -> list[PlayerStat]:
    """The player's best total in a single match for each kind of feature."""
    names = {
        "City": QCoreApplication.translate("CarcassonneStats", "Best city"),
        "Road": QCoreApplication.translate("CarcassonneStats", "Best road"),
        "Cloister": QCoreApplication.translate("CarcassonneStats", "Best cloister"),
        "Field": QCoreApplication.translate("CarcassonneStats", "Best field"),
        "Fair": QCoreApplication.translate("CarcassonneStats", "Best fair"),
    }
    template = QCoreApplication.translate("CarcassonneStats", "Best in one match, {}")
    cards = []
    for kind, caption in names.items():
        query = CarcassonneStatsQueries.matchKindPlayerQuery.format(kind)
        for row in db.queryDict(query, (nick,)):
            cards.append(
                PlayerStat(caption, str(row["points"]), template.format(row["date"]))
            )
    return cards
