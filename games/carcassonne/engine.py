"""Carcassonne play-time and statistics engines."""

from __future__ import annotations

from typing import cast

from core.engine.base import EntryGameEngine, readInput
from core.engine.db import db
from core.engine.stats import ParticularStatsEngine, StatsEngine
from games.carcassonne.model import CarcassonneMatch


class CarcassonneEngine(EntryGameEngine):
    """Entry-scored engine driving a Carcassonne match."""

    def __init__(self) -> None:
        if not hasattr(self, "game"):
            self.game = "Carcassonne"
        EntryGameEngine.__init__(self)

    def runStubRoundPlayer(self, player: str, winner: str | None = None) -> None:
        """CLI harness: read one player's score and feature kind, then record it."""
        entry_kinds = self.getEntryKinds()
        score = readInput(
            f"{player} score: ",
            int,
            lambda x: x > 0,
            "Sorry, invalid score number.",
        )
        errmsg = "Sorry, invalid kind [{}]".format(",".join(entry_kinds))
        kind = readInput("Kind: ", str, lambda x: x in entry_kinds, errmsg)
        self.addEntry(player, score, {"kind": kind})

    def getEntryKinds(self) -> list[str]:
        self.match = cast("CarcassonneMatch", self.match)
        return self.match.getEntryKinds()

    def requiresExplicitFinish(self) -> bool:
        return True


if __name__ == "__main__":
    re = CarcassonneEngine()
    re.gameStub()


class CarcassonneStatsQueries:
    """SQL query templates for Carcassonne single-kind and match-kind records."""

    singleKindRecordQuery = """
    SELECT value as "record",
        Round.score as "points",
        RoundStatistics.nick as "player",
        DATE(Match.finished) as date
    FROM Match,Round,RoundStatistics
    WHERE Match.idMatch = Round.idMatch
        and Round.idMatch = RoundStatistics.idMatch
        and Round.idRound = RoundStatistics.idRound
        and Round.nick = RoundStatistics.nick
        and Match.state = 1
        and Game_name="Carcassonne"
        and key="kind"
        and value = '{}'
        and Round.score>0
    order by points desc
    limit 1
    """

    matchKindRecordQuery = """
        SELECT Match.idMatch as "match",
            value as "record",
            SUM(Round.score) as "points",
            RoundStatistics.nick as "player",
            DATE(Match.finished) as date
    FROM Match,Round,RoundStatistics
    WHERE Match.idMatch = Round.idMatch
        and Round.idMatch = RoundStatistics.idMatch
        and Round.idRound = RoundStatistics.idRound
        and Round.nick = RoundStatistics.nick
        and Match.state = 1
        and Game_name="Carcassonne"
        and key="kind"
        and value = '{}'
        and Round.score>0
   GROUP BY "match","record","player"
   ORDER BY points desc
   LIMIT 1
   """


class CarcassonneStatsEngine(StatsEngine):
    """Adds Carcassonne single-kind and match-kind record statistics."""

    def __init__(self) -> None:
        super().__init__()
        self.singleKindRecord: list[dict] = []
        q = CarcassonneStatsQueries()
        self._singleKindRecordQuery = q.singleKindRecordQuery
        self._matchKindRecordQuery = q.matchKindRecordQuery

    def update(self, players: list[str] | None = None) -> None:
        """Refresh base statistics plus the per-kind Carcassonne records."""
        super().update()
        self.singleKindRecord = []
        self.matchKindRecord: list[dict] = []

        for kind in ("City", "Road", "Field"):
            q = self._singleKindRecordQuery.format(kind)
            self.singleKindRecord += db.queryDict(q, self._bound_params(q))

        for kind in ("City", "Road", "Cloister", "Field", "Fair"):
            q = self._matchKindRecordQuery.format(kind)
            self.matchKindRecord += db.queryDict(q, self._bound_params(q))

    def getSingleKindRecords(self) -> list[dict]:
        return self.singleKindRecord

    def getMatchKindRecords(self) -> list[dict]:
        return self.matchKindRecord


class CarcassonneParticularStatsEngine(CarcassonneStatsEngine, ParticularStatsEngine):
    """Carcassonne record statistics restricted to an exact set of players."""

    def updatePlayers(self, players: list[str] | None) -> None:
        """Splice the player filter into the Carcassonne record queries."""
        super().updatePlayers(players)
        if players:
            q = CarcassonneStatsQueries()
            self._singleKindRecordQuery = q.singleKindRecordQuery.replace(
                "WHERE", "WHERE {} AND".format("Match." + self._newclause)
            )
            self._matchKindRecordQuery = q.matchKindRecordQuery.replace(
                "WHERE", "WHERE {} AND".format("Match." + self._newclause)
            )
