"""Cards the player statistics show for a player in Qwirkle."""

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
                QCoreApplication.translate("QwirkleStats", "Best play"),
                str(row["max_round_score"]),
            )
        )
    if row.get("max_qwirkles") is not None:
        cards.append(
            PlayerStat(
                QCoreApplication.translate("QwirkleStats", "Max Qwirkles"),
                str(row["max_qwirkles"]),
                QCoreApplication.translate("QwirkleStats", "Qwirkles in one match"),
            )
        )
    average = db.queryDict(_AVERAGE_PLAY, (GenericMatch.FINISHED, nick))
    if average and average[0]["average"] is not None:
        cards.append(
            PlayerStat(
                QCoreApplication.translate("QwirkleStats", "Average play"),
                f"{average[0]['average']:.1f}",
            )
        )
    total = db.queryDict(_TOTAL_QWIRKLES, (GenericMatch.FINISHED, nick))
    if total and total[0]["total"] is not None:
        cards.append(
            PlayerStat(
                QCoreApplication.translate("QwirkleStats", "Total Qwirkles"),
                str(int(total[0]["total"])),
            )
        )
    return cards


_AVERAGE_PLAY = """
    SELECT AVG(r.score) AS average FROM Round r JOIN Match m ON m.idMatch=r.idMatch
    WHERE m.state=? AND m.Game_name='Qwirkle' AND r.nick=?
"""

_TOTAL_QWIRKLES = """
    SELECT SUM(CAST(rs.value AS INTEGER)) AS total
    FROM RoundStatistics rs JOIN Match m ON m.idMatch=rs.idMatch
    WHERE m.state=? AND m.Game_name='Qwirkle' AND rs.key='qwirkles' AND rs.nick=?
"""
