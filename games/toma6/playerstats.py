"""Cards the player statistics show for a player in Toma6."""

from __future__ import annotations

from PySide6.QtCore import QCoreApplication

from core.engine.playerstats import PlayerStat, player_form, rounds_per_match


def player_stats(game: str, nick: str) -> list[PlayerStat]:
    cards = []
    rounds = rounds_per_match(nick, game)
    if rounds is not None:
        cards.append(
            PlayerStat(
                QCoreApplication.translate("Toma6Stats", "Rounds per match"),
                f"{rounds:.1f}",
                QCoreApplication.translate(
                    "Toma6Stats", "Average over finished matches"
                ),
            )
        )
    streak = player_form(nick, (game,)).longest_win_streak
    cards.append(
        PlayerStat(
            QCoreApplication.translate("Toma6Stats", "Best winning streak"), str(streak)
        )
    )
    return cards
