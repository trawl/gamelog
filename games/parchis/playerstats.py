"""Cards the player statistics show for a player in Parchís."""

from __future__ import annotations

from PySide6.QtCore import QCoreApplication

from core.engine.db import db
from core.engine.playerstats import PlayerStat, engine_row
from games.parchis.engine import ParchisStatsQueries


def player_stats(game: str, nick: str) -> list[PlayerStat]:
    row = engine_row(game, nick)
    cards = []
    if row.get("max_kills") is not None:
        cards.append(
            PlayerStat(
                QCoreApplication.translate("ParchisStats", "Max kills"),
                str(row["max_kills"]),
                QCoreApplication.translate("ParchisStats", "Kills in one match"),
            )
        )
    if row.get("max_combo") is not None:
        cards.append(
            PlayerStat(
                QCoreApplication.translate("ParchisStats", "Best combo"),
                str(row["max_combo"]),
                QCoreApplication.translate("ParchisStats", "Combo points in one match"),
            )
        )
    template = QCoreApplication.translate("ParchisStats", "{} kills")
    for caption, query in (
        (
            QCoreApplication.translate("ParchisStats", "Killed most by"),
            ParchisStatsQueries.killedMostByQuery,
        ),
        (
            QCoreApplication.translate("ParchisStats", "Killed most"),
            ParchisStatsQueries.killedMostQuery,
        ),
    ):
        for found in db.queryDict(query, (nick,)):
            cards.append(
                PlayerStat(caption, found["opponent"], template.format(found["kills"]))
            )
    return cards
