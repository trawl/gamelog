"""Azul and Azul: Summer Pavilion match and round models.

Each round a player scores the tiles they placed (minus penalties). The final
round also carries the end-of-game bonuses, which are stored with the round.
In Azul the game ends after the round in which a player completes a wall row,
and the bonuses are for complete rows, columns and colours. In Summer Pavilion
the game lasts six rounds, players start on 5 points, and the bonuses are for
complete stars and for covering every space of a number (1 to 4).
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import ClassVar, cast

from core.engine.db import db
from core.model.match import GenericRound, GenericRoundMatch


class AzulMatch(GenericRoundMatch):
    """Round match for Azul, ending once someone completes a wall row."""

    gameName = "Azul"
    # End-of-game bonus points for each kind of bonus.
    bonuses: ClassVar[dict[str, int]] = {"rows": 2, "columns": 7, "colours": 10}
    # How the bonuses are grouped for display.
    bonusGroups: ClassVar[tuple[tuple[str, ...], ...]] = (
        ("rows", "columns", "colours"),
    )
    # A wall has five rows, five columns and five colours.
    maxBonuses = 5
    # A wall row has five tiles and gets at most one per round, so no row can
    # be complete before the fifth round.
    firstBonusRound = 5
    # The bonus that ends the game; the others only score alongside it.
    endingBonus: ClassVar[str | None] = "rows"
    initialScore = 0
    # The floor line costs at most 14 points.
    minRoundScore = -14
    maxRoundScore = 50

    def __init__(self, players: Sequence[str] = ()) -> None:
        super().__init__(players)
        self.game = self.gameName
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
        return AzulRound(numround, tuple(self.bonuses))

    def addRound(self, rnd: GenericRound) -> None:
        """Add a round, never letting a player's score drop below zero."""
        for player, score in rnd.getScore().items():
            total = self.totalScores.get(player, 0)
            if total + score < 0:
                rnd.setPlayerScore(player, -total)
        super().addRound(rnd)

    def playerStart(self, player: str) -> None:
        """Put the player's score on the starting space."""
        self.totalScores[player] = self.initialScore

    def playerAddRound(self, player: str, rnd: GenericRound) -> None:
        """Nothing to track beyond the running totals."""

    def isOver(self) -> bool:
        """Whether the last round ended the game: someone completed a row."""
        if not self.rounds or self.endingBonus is None:
            return False
        last = cast("AzulRound", self.rounds[-1])
        return any(last.getBonuses(p)[self.endingBonus] for p in last.getScore())

    def tieBreak(self, player: str) -> int:
        """Rank tied players: more complete rows is better."""
        if self.endingBonus is None:
            return 0
        return self.getPlayerBonuses(player)[self.endingBonus]

    def computeWinner(self) -> None:
        """Once the game is over, pick the highest score.

        Ties go to the best :meth:`tieBreak`, then to the first in playing
        order.
        """
        if not self.isOver():
            return
        maxscore = max(self.totalScores.values())
        candidates = [p for p, s in self.totalScores.items() if s == maxscore]
        candidates.sort(key=self.tieBreak, reverse=True)
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


class AzulSummerPavilionMatch(AzulMatch):
    """Round match for Azul: Summer Pavilion: six rounds, starting on 5."""

    gameName = "Azul Summer Pavilion"
    bonuses: ClassVar[dict[str, int]] = {
        "star_multi": 12,
        "star_red": 14,
        "star_blue": 15,
        "star_yellow": 16,
        "star_orange": 17,
        "star_green": 18,
        "star_purple": 20,
        "ones": 4,
        "twos": 8,
        "threes": 12,
        "fours": 16,
    }
    bonusGroups: ClassVar[tuple[tuple[str, ...], ...]] = (
        (
            "star_multi",
            "star_red",
            "star_blue",
            "star_yellow",
            "star_orange",
            "star_green",
            "star_purple",
        ),
        ("ones", "twos", "threes", "fours"),
    )
    # Each star and each number can only be completed once.
    maxBonuses = 1
    # Bonuses are scored after the last round.
    numRounds = 6
    firstBonusRound = numRounds
    endingBonus = None
    initialScore = 5
    minRoundScore = -20
    maxRoundScore = 100

    def isOver(self) -> bool:
        """The game ends after the sixth round."""
        return len(self.rounds) >= self.numRounds


class AzulRound(GenericRound):
    """An Azul round: each player's score and any end-of-game bonuses."""

    def __init__(self, numround: int, keys: tuple[str, ...]) -> None:
        super().__init__(numround)
        self.keys = keys
        self.bonuses: dict[str, dict[str, int]] = {}

    def addExtraInfo(self, player: str, extras: dict) -> None:
        """Record ``player``'s bonus counts from ``extras``."""
        self.bonuses[player] = {key: int(extras.get(key, 0)) for key in self.keys}

    def getBonuses(self, player: str) -> dict[str, int]:
        """Return ``player``'s bonus counts this round (all zero if none)."""
        try:
            return self.bonuses[player]
        except KeyError:
            return dict.fromkeys(self.keys, 0)
