"""Scrabble play-time and statistics engines."""

from __future__ import annotations

from typing import cast

from core.engine.base import EntryGameEngine, readInput
from core.engine.db import db
from core.engine.stats import ParticularStatsEngine, StatsEngine
from games.scrabble.model import ScrabbleMatch


class ScrabbleEngine(EntryGameEngine):
    """Entry-scored engine driving a Scrabble match."""

    def __init__(self) -> None:
        if not hasattr(self, "game"):
            self.game = "Scrabble"
        EntryGameEngine.__init__(self)

    def getBonuses(self) -> dict:
        return cast(ScrabbleMatch, self.match).getBonuses()

    def requiresExplicitFinish(self) -> bool:
        return True

    def runStubRoundPlayer(self, player: str, winner: str | None = None) -> None:
        """CLI harness: read one player's score and bonus, then record the entry."""
        score = readInput(
            f"{player} score: ",
            int,
            lambda x: x > 0,
            "Sorry, invalid score number.",
        )
        errmsg = "Sorry, invalid kind [0-6]"
        kind = readInput("Scrabble bonus?: ", int, lambda x: 0 <= x <= 6, errmsg)
        self.addEntry(player, score, {"kind": kind})


class ScrabbleStatsEngine(StatsEngine):
    """Adds Scrabble extreme-round and max-bonus player statistics."""

    def __init__(self) -> None:
        super().__init__()
        self.game = "Scrabble"
        self.singleKindRecord = None
        self.queries: dict[str, str] = {}
        self.define_queries()

    def define_queries(self) -> None:
        """Build the extreme-round and max-bonus query templates."""
        self.query_params: dict[str, tuple[str, ...]] = {
            "extreme_rounds": ("max_round_score", "min_round_score"),
            "max_bonuses": ("max_bonuses",),
        }
        self.queries["extreme_rounds"] = f"""
        SELECT Round.nick as "player", max(score) as "max_round_score",
            min(score) as "min_round_score"
        FROM Round,Match
        WHERE Match.idMatch = Round.idMatch
            and Match.state = 1
            and Game_name="{self.game}"
        group by player
        """
        self.queries["max_bonuses"] = """
        SELECT player, MAX(bonuses) as "max_bonuses"
        FROM (
            SELECT Match.idMatch as "match",
                RoundStatistics.nick as "player",key,
             SUM(value) as "bonuses"
            FROM Match,Round,RoundStatistics
            WHERE Match.idMatch = Round.idMatch
                AND Round.idMatch = RoundStatistics.idMatch
                AND Round.idRound = RoundStatistics.idRound
                AND Round.nick = RoundStatistics.nick
                AND Match.state = 1
                AND Game_name='Scrabble'
            GROUP BY "match", "player") AS TMP
        GROUP BY "player"
        """

    def update(self, players: list[str] | None = None) -> None:
        """Merge the extreme-round and max-bonus figures into player stats."""
        super().update()
        if not self.generalplayerstats:
            return

        for q, params in self.query_params.items():
            query = self.queries[q]
            for row in db.queryDict(query, self._bound_params(query)):
                player = row["player"]
                for r2 in self.generalplayerstats:
                    if r2["nick"] == player and r2["game"] == self.game:
                        for p in params:
                            r2[p] = row[p]
                        break


class ScrabbleParticularStatsEngine(ScrabbleStatsEngine, ParticularStatsEngine):
    """Scrabble statistics restricted to an exact set of players."""

    def updatePlayers(self, players: list[str] | None) -> None:
        """Splice the player filter into the Scrabble statistics queries."""
        super().updatePlayers(players)
        if players:
            self.define_queries()
            for q in self.queries:
                self.queries[q] = self.queries[q].replace(
                    "WHERE", "WHERE {} AND".format("Match." + self._newclause)
                )


if __name__ == "__main__":
    re = ScrabbleEngine()
    re.gameStub()
