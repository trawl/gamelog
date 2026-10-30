"""Cards the player statistics show for a player in Catan."""

from __future__ import annotations

from PySide6.QtCore import QCoreApplication

from core.engine.db import db
from core.engine.playerstats import PlayerStat
from core.model.match import GenericMatch

_AWARDS = """
    SELECT key, COUNT(*) AS matches FROM (
        SELECT rs.idMatch, rs.key, SUM(CAST(rs.value AS INTEGER)) AS held
        FROM RoundStatistics rs JOIN Match m ON m.idMatch=rs.idMatch
        WHERE m.state=? AND m.Game_name='Catan' AND rs.nick=?
            AND rs.key IN ('longestroad', 'largestarmy')
        GROUP BY rs.idMatch, rs.key
    ) WHERE held > 0 GROUP BY key
"""


def player_stats(game: str, nick: str) -> list[PlayerStat]:
    """In how many finished matches the player ended with each award."""
    held = {
        r["key"]: r["matches"]
        for r in db.queryDict(_AWARDS, (GenericMatch.FINISHED, nick))
    }
    tip = QCoreApplication.translate("CatanStats", "Matches ended holding it")
    return [
        PlayerStat(
            QCoreApplication.translate("CatanStats", "Longest road"),
            str(held.get("longestroad", 0)),
            tip,
        ),
        PlayerStat(
            QCoreApplication.translate("CatanStats", "Largest army"),
            str(held.get("largestarmy", 0)),
            tip,
        ),
    ]
