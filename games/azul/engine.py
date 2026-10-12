"""Azul play-time engine."""

from __future__ import annotations

from typing import cast

from core.engine.db import db
from core.engine.engine import RoundGameEngine, readInput
from core.engine.stats import ParticularStatsEngine, StatsEngine
from games.azul.model import AzulMatch


class AzulEngine(RoundGameEngine):
    """Engine driving an Azul match and its end-of-game bonuses."""

    def __init__(self) -> None:
        if not hasattr(self, "game"):
            self.game = "Azul"
        super().__init__()

    def getBonuses(self) -> dict[str, int]:
        return cast("AzulMatch", self.match).bonuses

    def getMaxBonuses(self) -> int:
        return cast("AzulMatch", self.match).maxBonuses

    def getPlayerBonuses(self, player: str) -> dict[str, int]:
        return cast("AzulMatch", self.match).getPlayerBonuses(player)

    def bonusPoints(self, bonuses: dict[str, int]) -> int:
        return cast("AzulMatch", self.match).bonusPoints(bonuses)

    def bonusesAllowed(self) -> bool:
        """Whether a row can be complete by the round being played."""
        return self.getNumRound() >= cast("AzulMatch", self.match).firstBonusRound

    def runRoundPlayer(self, player: str, winner: str | None = None) -> None:
        """CLI harness: read ``player``'s round score and bonuses, record them."""
        score = readInput(
            f"{player} round score: ", int, lambda x: True, "Sorry, invalid score."
        )
        bonuses = {}
        if self.bonusesAllowed():
            for key in self.getBonuses():
                bonuses[key] = readInput(
                    f"{player} complete {key}: ",
                    int,
                    lambda x: 0 <= x <= self.getMaxBonuses(),
                    "Sorry, invalid number.",
                )
        self.addRoundInfo(player, score + self.bonusPoints(bonuses), bonuses)


class AzulStatsEngine(StatsEngine):
    """App-wide Azul statistics, adding the best end-of-game bonus per match
    size and per player."""

    def __init__(self) -> None:
        super().__init__()
        self.game = "Azul"
        self.queries: dict[str, str] = {}
        self.define_queries()

    def define_queries(self) -> None:
        """Build the per-match bonus queries for this engine."""
        points = " ".join(
            f"WHEN '{key}' THEN {value}" for key, value in AzulMatch.bonuses.items()
        )
        # Bonus points each player scored in each finished match.
        bonusPerPlayer = f"""
            SELECT Match.idMatch AS match, RoundStatistics.nick AS player,
                SUM(CASE key {points} ELSE 0 END
                    * CAST(value AS integer)) AS bonus
            FROM Match JOIN RoundStatistics USING (idMatch)
            WHERE Match.state = 1 AND Match.Game_name = '{self.game}'
            GROUP BY match, player
        """
        self.queries["player"] = f"""
        SELECT player, MAX(bonus) AS maxbonus
        FROM ({bonusPerPlayer}) AS tmp
        GROUP BY player
        """
        self.queries["match"] = f"""
        SELECT nplayers, MAX(bonus) AS maxbonus
        FROM ({bonusPerPlayer}) AS tmp
        JOIN (SELECT idMatch, COUNT(*) AS nplayers
              FROM MatchPlayer GROUP BY idMatch) AS np ON np.idMatch = tmp.match
        GROUP BY nplayers
        """

    def update(self, players: list[str] | None = None) -> None:
        """Refresh base statistics, then fold in the best bonuses."""
        super().update(players)
        if self.generalplayerstats:
            query = self.queries["player"]
            for row in db.queryDict(query, self._bound_params(query)):
                for stats in self.generalplayerstats:
                    if stats["game"] == self.game and stats["nick"] == row["player"]:
                        stats["maxbonus"] = row["maxbonus"]
        if self.generalmatchstats:
            query = self.queries["match"]
            for row in db.queryDict(query, self._bound_params(query)):
                for stats in self.generalmatchstats:
                    if (
                        stats["game"] == self.game
                        and stats["nplayers"] == row["nplayers"]
                    ):
                        stats["maxbonus"] = row["maxbonus"]


class AzulParticularStatsEngine(AzulStatsEngine, ParticularStatsEngine):
    """Azul statistics restricted to matches with an exact set of players."""

    def updatePlayers(self, players: list[str] | None) -> None:
        """Splice the player filter into each Azul-specific query."""
        super().updatePlayers(players)
        if players:
            self.define_queries()
            for q in self.queries:
                self.queries[q] = self.queries[q].replace(
                    "WHERE", "WHERE {} AND".format("Match." + self._newclause)
                )


if __name__ == "__main__":
    re = AzulEngine()
    re.gameStub()
