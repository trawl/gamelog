"""Azul match and round models.

Each round a player scores the tiles placed on their wall (minus floor-line
penalties). The game ends after the round in which a player completes a
horizontal row; that round also carries the end-of-game bonuses for complete
rows, columns and colours, which are stored with the round.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import ClassVar, cast

from core.engine.db import db
from core.model.match import GenericRound, GenericRoundMatch


class AzulMatch(GenericRoundMatch):
    """Round match for Azul, ending once someone completes a wall row."""

    # End-of-game bonus points for each complete row, column and colour.
    bonuses: ClassVar[dict[str, int]] = {"rows": 2, "columns": 7, "colours": 10}
    # A wall has five rows, five columns and five colours.
    maxBonuses = 5
    # A wall row has five tiles and gets at most one per round, so no row can
    # be complete before the fifth round.
    firstBonusRound = 5

    def __init__(self, players: Sequence[str] = ()) -> None:
        super().__init__(players)
        self.game = "Azul"
        self.dealingp = 3

    def flushToDB(self) -> None:
        """Persist the base match plus every player's bonuses in each round."""
        super().flushToDB()
        # Every key is written for every player, so each round always has its
        # full set of RoundStatistics rows when resumed.
        for rnd in cast("list[AzulRound]", self.rounds):
            for player in rnd.getScore():
                for key, value in rnd.getBonuses(player).items():
                    db.execute(
                        "INSERT OR REPLACE INTO RoundStatistics "
                        "(idMatch,nick,idRound,key,value) "
                        "VALUES (?,?,?,?,?);",
                        (self.idMatch, player, rnd.getNumRound(), key, value),
                    )

    def resumeExtraInfo(self, player: str, key: str, value: str) -> dict:
        """Decode a persisted bonus-count row."""
        if key in self.bonuses:
            return {key: int(value)}
        return {}

    def createRound(self, numround: int) -> AzulRound:
        return AzulRound(numround)

    def addRound(self, rnd: GenericRound) -> None:
        """Add a round, never letting a player's score drop below zero."""
        for player, score in rnd.getScore().items():
            total = self.totalScores.get(player, 0)
            if total + score < 0:
                rnd.setPlayerScore(player, -total)
        super().addRound(rnd)

    def playerStart(self, player: str) -> None:
        """Nothing to initialise: scores start at zero."""

    def playerAddRound(self, player: str, rnd: GenericRound) -> None:
        """Nothing to track beyond the running totals."""

    def computeWinner(self) -> None:
        """Once a row is complete, pick the highest score.

        Ties go to the player with more complete rows, then to the first in
        playing order.
        """
        if not self.rounds:
            return
        last = cast("AzulRound", self.rounds[-1])
        if not last.endsGame():
            return
        maxscore = max(self.totalScores.values())
        candidates = [p for p, s in self.totalScores.items() if s == maxscore]
        candidates.sort(key=lambda p: last.getBonuses(p)["rows"], reverse=True)
        self.winner = candidates[0]

    def getPlayerBonuses(self, player: str) -> dict[str, int]:
        """Return ``player``'s bonus counts summed over every round."""
        totals = dict.fromkeys(self.bonuses, 0)
        for rnd in cast("list[AzulRound]", self.rounds):
            for key, count in rnd.getBonuses(player).items():
                totals[key] += count
        return totals

    @classmethod
    def bonusPoints(cls, bonuses: dict[str, int]) -> int:
        """Return the points worth of ``bonuses`` (counts per bonus kind)."""
        return sum(cls.bonuses[key] * bonuses.get(key, 0) for key in cls.bonuses)


class AzulRound(GenericRound):
    """An Azul round: each player's score and any end-of-game bonuses."""

    def __init__(self, numround: int) -> None:
        super().__init__(numround)
        self.bonuses: dict[str, dict[str, int]] = {}

    def addExtraInfo(self, player: str, extras: dict) -> None:
        """Record ``player``'s bonus counts from ``extras``."""
        self.bonuses[player] = {
            key: int(extras.get(key, 0)) for key in AzulMatch.bonuses
        }

    def getBonuses(self, player: str) -> dict[str, int]:
        """Return ``player``'s bonus counts this round (all zero if none)."""
        try:
            return self.bonuses[player]
        except KeyError:
            return dict.fromkeys(AzulMatch.bonuses, 0)

    def endsGame(self) -> bool:
        """Whether some player completed a row, ending the game."""
        return any(self.getBonuses(p)["rows"] > 0 for p in self.getScore())
