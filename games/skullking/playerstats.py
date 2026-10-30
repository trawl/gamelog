"""Cards the player statistics show for a player in Skull King."""

from __future__ import annotations

from PySide6.QtCore import QCoreApplication

from core.engine.playerstats import PlayerStat, engine_row


def player_stats(game: str, nick: str) -> list[PlayerStat]:
    row = engine_row(game, nick)
    share = QCoreApplication.translate(
        "SkullKingStats", "Share of rounds with the bid met, per match"
    )
    cards = []
    if row.get("max_hits") is not None:
        caption = QCoreApplication.translate("SkullKingStats", "Max hit %")
        cards.append(PlayerStat(caption, f"{row['max_hits']:g}%", share))
    if row.get("avg_hits") is not None:
        caption = QCoreApplication.translate("SkullKingStats", "Avg hit %")
        cards.append(PlayerStat(caption, f"{row['avg_hits']:g}%", share))
    if row.get("max_round_score") is not None:
        caption = QCoreApplication.translate("SkullKingStats", "Best round")
        cards.append(PlayerStat(caption, str(row["max_round_score"])))
    return cards
