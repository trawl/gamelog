"""Cards the player statistics show for a player in Scrabble."""

from __future__ import annotations

from PySide6.QtCore import QCoreApplication

from core.engine.db import db
from core.engine.playerstats import PlayerStat, engine_row
from core.model.match import GenericMatch


def player_stats(game: str, nick: str) -> list[PlayerStat]:
    row = engine_row(game, nick)
    cards = []
    if row.get("max_round_score") is not None:
        cards.append(
            PlayerStat(
                QCoreApplication.translate("ScrabbleStats", "Best play"),
                str(row["max_round_score"]),
            )
        )
    if row.get("max_bonuses") is not None:
        cards.append(
            PlayerStat(
                QCoreApplication.translate("ScrabbleStats", "Max bonus"),
                str(row["max_bonuses"]),
                QCoreApplication.translate("ScrabbleStats", "Bonuses in one match"),
            )
        )
    average = db.queryDict(_AVERAGE_PLAY, (GenericMatch.FINISHED, nick))
    if average and average[0]["average"] is not None:
        cards.append(
            PlayerStat(
                QCoreApplication.translate("ScrabbleStats", "Average play"),
                f"{average[0]['average']:.1f}",
            )
        )
    return cards


_AVERAGE_PLAY = """
    SELECT AVG(r.score) AS average FROM Round r JOIN Match m ON m.idMatch=r.idMatch
    WHERE m.state=? AND m.Game_name='Scrabble' AND r.nick=?
"""
