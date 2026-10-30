"""Cards the player statistics show for a player in Azul and Azul: Summer Pavilion."""

from __future__ import annotations

from PySide6.QtCore import QCoreApplication

from core.engine.playerstats import PlayerStat, engine_row


def player_stats(game: str, nick: str) -> list[PlayerStat]:
    row = engine_row(game, nick)
    if row.get("maxbonus") is None:
        return []
    return [
        PlayerStat(
            QCoreApplication.translate("AzulStats", "Max bonus"),
            str(row["maxbonus"]),
            QCoreApplication.translate(
                "AzulStats", "End-of-game bonus points in one match"
            ),
        )
    ]
