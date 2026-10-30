"""What the player statistics show beside each Phase 10 player's score."""

from __future__ import annotations

from collections.abc import Sequence

from PySide6.QtCore import QCoreApplication

from core.engine.db import db
from core.engine.playerstats import PlayerStat, engine_row
from games.phase10.engine import Phase10StatsQueries


def phases_completed(match_ids: Sequence[int]) -> dict[int, dict[str, str]]:
    """Per match and player, how many phases they completed."""
    cur = db.execute(
        "SELECT mp.idMatch, mp.nick, "
        "COUNT(CASE WHEN rs.value <> 0 THEN 1 END) AS phases "
        "FROM MatchPlayer mp LEFT JOIN RoundStatistics rs "
        "ON rs.idMatch=mp.idMatch AND rs.nick=mp.nick AND rs.key='PhaseCompleted' "
        f"WHERE mp.idMatch IN ({','.join('?' * len(match_ids))}) "
        "GROUP BY mp.idMatch, mp.nick",
        tuple(match_ids),
    )
    template = QCoreApplication.translate("Phase10Details", "phases: {}")
    details: dict[int, dict[str, str]] = {}
    for row in cur:
        details.setdefault(row["idMatch"], {})[str(row["nick"])] = template.format(
            row["phases"]
        )
    return details


# Average per match, from the very query behind the lowest count.
_AVERAGE_PHASES = Phase10StatsQueries.worst_phases.replace(
    "min(pc) AS min_phases", "AVG(pc) AS avg_phases"
)


def player_stats(game: str, nick: str) -> list[PlayerStat]:
    """Fewest phases, most attempted phase and phases per match."""
    row = engine_row(game, nick)
    cards = []
    if row.get("min_phases") is not None:
        cards.append(
            PlayerStat(
                QCoreApplication.translate("Phase10Details", "Fewest phases"),
                str(row["min_phases"]),
                QCoreApplication.translate(
                    "Phase10Details", "Phases completed in a match"
                ),
            )
        )
    if row.get("damned_phase") is not None:
        cards.append(
            PlayerStat(
                QCoreApplication.translate("Phase10Details", "Damned phase"),
                str(row["damned_phase"]),
                QCoreApplication.translate(
                    "Phase10Details", "The phase aimed at most often"
                ),
            )
        )
    for found in db.queryDict(_AVERAGE_PHASES):
        if found["game"] == game and found["nick"] == nick:
            cards.append(
                PlayerStat(
                    QCoreApplication.translate("Phase10Details", "Phases per match"),
                    f"{found['avg_phases']:.1f}",
                )
            )
    return cards
