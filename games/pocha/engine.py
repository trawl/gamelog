"""Pocha game engine and its statistics engines."""

from __future__ import annotations

from typing import cast

from core.engine.base import RoundGameEngine, readInput
from core.engine.db import db
from core.engine.stats import ParticularStatsEngine, StatsEngine
from games.pocha.model import PochaMatch


class PochaEngine(RoundGameEngine):
    """Round engine for Pocha: tracks hands, suit type and dealing direction."""

    def __init__(self) -> None:
        if not hasattr(self, "game"):
            self.game = "Pocha"
        super().__init__()
        self.setSuitType()

    def runRoundPlayer(self, player: str, winner: str | None = None) -> None:
        """CLI harness: read ``player``'s round score and record it."""
        score = readInput(
            f"{player} round score: ",
            int,
            lambda x: True,
            "Sorry, invalid score number.",
        )
        self.addRoundInfo(player, score)

    def getHands(self, rnd: int | None = None) -> int:
        """Return the number of cards dealt in round ``rnd`` (default: current)."""
        index = self.getNumRound() - 1
        if rnd is not None:
            index = rnd - 1
        try:
            return cast("PochaMatch", self.match).getHands()[index]
        except IndexError:
            return 1

    def getDirection(self, rnd: int | None = None) -> str:
        """Return the dealing direction/suit for round ``rnd`` (default: current)."""
        index = self.getNumRound() - 1
        if rnd is not None:
            index = rnd - 1
        try:
            return self.directions[index]
        except IndexError:
            return self.directions[-1]

    def setSuitType(self, st: str = "spanish") -> None:
        """Choose the card deck and build the per-round direction sequence."""
        self.suitType = st
        slope = (len(cast("PochaMatch", self.match).getHands()) - 4) // 2
        if st == "french":
            suits = ["diamonds", "hearts", "spades", "clovers"]
        else:
            suits = ["coins", "cups", "swords", "clubs"]
        self.directions: list[str] = (
            ["going up"] * slope + suits + ["going down"] * slope
        )

    def getSuitType(self) -> str:
        return self.suitType

    def getRoundSequence(self) -> list[int]:
        return cast("PochaMatch", self.match).getHands()


class PochaStatsQueries:
    """SQL query templates for Pocha statistics (``#GAMENAME#`` substituted in)."""

    hitsQuery = """
    SELECT player, max(hits) as "max_hits", min(hits) as "min_hits" from (
        SELECT Round.idMatch as idm, Round.nick as "player",
            COUNT(Round.idRound) as "hits"
        FROM Round,Match
        WHERE Match.idMatch = Round.idMatch
            and Match.state = 1
            and Game_name="#GAMENAME#"
            and Round.score>=10
        group by idm, player
    ) as tmp
    group by player
    order by player
    """

    extremeRounds = """
    SELECT Round.nick as "player", max(score) as "max_round_score",
        min(score) as "min_round_score"
    FROM Round,Match
    WHERE Match.idMatch = Round.idMatch
        and Match.state = 1
        and Game_name="#GAMENAME#"
    group by player
   """


class PochaStatsEngine(StatsEngine):
    """App-wide Pocha statistics: hit counts and extreme round scores."""

    def __init__(self) -> None:
        super().__init__()
        self.singleKindRecord = None
        self.game = "Pocha"
        self.define_queries()

    def define_queries(self) -> None:
        """Bind the game name into this engine's query templates."""
        q = PochaStatsQueries()
        self._hitsQuery = q.hitsQuery.replace("#GAMENAME#", self.game)
        self._extremeRounds = q.extremeRounds.replace("#GAMENAME#", self.game)

    def update(self, players: list[str] | None = None) -> None:
        """Refresh base statistics, then fold in Pocha hit/extreme-round figures."""
        super().update()
        # print(f"Updating {self.game} stats...")
        self.hitsRecord = db.queryDict(
            self._hitsQuery, self._bound_params(self._hitsQuery)
        )
        self.extremeRoundsRecord = db.queryDict(
            self._extremeRounds, self._bound_params(self._extremeRounds)
        )

        if not self.generalplayerstats:
            return

        for row in self.hitsRecord:
            player = row["player"]
            for r2 in self.generalplayerstats:
                if r2["nick"] == player and r2["game"] == self.game:
                    for k in ("avg_hits", "max_hits", "min_hits"):
                        if k in row:
                            r2[k] = row[k]
                    break
        for row in self.extremeRoundsRecord:
            player = row["player"]
            for r2 in self.generalplayerstats:
                if r2["nick"] == player and r2["game"] == self.game:
                    r2["max_round_score"] = row["max_round_score"]
                    r2["min_round_score"] = row["min_round_score"]
                    break


class PochaParticularStatsEngine(PochaStatsEngine, ParticularStatsEngine):
    """Pocha statistics restricted to matches with an exact set of players."""

    def updatePlayers(self, players: list[str] | None) -> None:
        """Splice the player filter into the Pocha-specific queries too."""
        super().updatePlayers(players)
        if players:
            self.define_queries()
            self._hitsQuery = self._hitsQuery.replace(
                "WHERE", "WHERE {} AND".format("Match." + self._newclause)
            ).replace("#GAMENAME#", self.game)
            self._extremeRounds = self._extremeRounds.replace(
                "WHERE", "WHERE {} AND".format("Match." + self._newclause)
            ).replace("#GAMENAME#", self.game)
            # print(self._hitsQuery)


if __name__ == "__main__":
    re = PochaEngine()
    re.gameStub()
