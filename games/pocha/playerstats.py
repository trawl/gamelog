"""Cards the player statistics show for a player in Pocha."""

from __future__ import annotations

from PySide6.QtCore import QCoreApplication

from core.engine.playerstats import PlayerStat, engine_row


def player_stats(game: str, nick: str) -> list[PlayerStat]:
    row = engine_row(game, nick)
    hits = QCoreApplication.translate(
        "PochaStats", "Rounds with an exact bid in one match"
    )
    cards = []
    for key, caption, tip in (
        ("max_hits", QCoreApplication.translate("PochaStats", "Max hits"), hits),
        ("min_hits", QCoreApplication.translate("PochaStats", "Min hits"), hits),
        (
            "max_round_score",
            QCoreApplication.translate("PochaStats", "Best round"),
            None,
        ),
        (
            "min_round_score",
            QCoreApplication.translate("PochaStats", "Worst round"),
            None,
        ),
    ):
        if row.get(key) is not None:
            cards.append(PlayerStat(caption, str(row[key]), tip))
    return cards
