"""Cards the player statistics show for a player in Remigio."""

from __future__ import annotations

from PySide6.QtCore import QCoreApplication

from core.engine.db import db
from core.engine.playerstats import PlayerStat
from core.model.match import GenericMatch

_CLOSES = """
    SELECT CAST(rs.value AS INTEGER) AS multiplier, COUNT(*) AS rounds
    FROM RoundStatistics rs JOIN Match m ON m.idMatch=rs.idMatch
    WHERE m.state=? AND m.Game_name='Remigio' AND rs.key='closeType' AND rs.nick=?
    GROUP BY multiplier
"""


def player_stats(game: str, nick: str) -> list[PlayerStat]:
    """How the rounds the player won were closed: each multiplier's share."""
    cards = []
    rows = db.queryDict(_CLOSES, (GenericMatch.FINISHED, nick))
    total = sum(r["rounds"] for r in rows)
    if total:
        counts = {r["multiplier"]: r["rounds"] for r in rows}
        caption = QCoreApplication.translate("RemigioStats", "Closed with ×{}")
        tip = QCoreApplication.translate("RemigioStats", "{} of {} rounds won")
        cards += [
            PlayerStat(
                caption.format(multiplier),
                f"{counts.get(multiplier, 0) * 100 / total:.0f}%",
                tip.format(counts.get(multiplier, 0), total),
            )
            for multiplier in (1, 2, 3, 4)
        ]
    return cards
