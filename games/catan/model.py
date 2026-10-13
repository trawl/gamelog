"""Catan match and round models.

A Catan round is one committed update of the board: for every player it stores
how their holdings changed (settlements, cities, longest road, largest army and
victory-point cards) and the victory points that change is worth. A player's
current holdings are the setup-phase holdings (two settlements) plus the sum
of their changes over all rounds.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import ClassVar, cast

from core.engine.db import db
from core.model.match import GenericRound, GenericRoundMatch


class CatanMatch(GenericRoundMatch):
    """Round match for Catan, won by the first player reaching ``top`` points."""

    # Victory points awarded by each kind of holding.
    components: ClassVar[dict[str, int]] = {
        "settlements": 1,
        "cities": 2,
        "longestroad": 2,
        "largestarmy": 2,
        "vpcards": 1,
    }
    # Most of each holding a player can have at once (pieces in the box).
    limits: ClassVar[dict[str, int]] = {
        "settlements": 5,
        "cities": 4,
        "longestroad": 1,
        "largestarmy": 1,
        "vpcards": 5,
    }
    # Holdings only one player can have at a time.
    awards: ClassVar[tuple[str, ...]] = ("longestroad", "largestarmy")
    # Settlements every player places during the setup phase.
    initial_settlements = 2
    # Victory points that win the game.
    top = 10

    def __init__(self, players: Sequence[str] = ()) -> None:
        super().__init__(players)
        self.game = "Catan"
        self.dealingp = 3

    def flushToDB(self) -> None:
        """Persist the base match plus every holding change."""
        super().flushToDB()
        # Every key is written for every player, so each round always has its
        # full set of RoundStatistics rows when resumed.
        for rnd in cast("list[CatanRound]", self.rounds):
            for player in rnd.getScore():
                for key, value in rnd.getChanges(player).items():
                    db.execute(
                        "INSERT OR REPLACE INTO RoundStatistics "
                        "(idMatch,nick,idRound,key,value) "
                        "VALUES (?,?,?,?,?);",
                        (self.idMatch, player, rnd.getNumRound(), key, value),
                    )

    def resumeExtraInfo(self, player: str, key: str, value: str) -> dict:
        """Decode a persisted holding-change row."""
        if key in self.components:
            return {key: int(value)}
        return {}

    def createRound(self, numround: int) -> CatanRound:
        return CatanRound(numround)

    def playerStart(self, player: str) -> None:
        """Credit the points of the settlements placed during the setup phase."""
        self.totalScores[player] = self.victoryPoints(self.getInitialState())

    def playerAddRound(self, player: str, rnd: GenericRound) -> None:
        """Nothing to track: holdings are derived from the rounds."""

    def computeWinner(self) -> None:
        """Pick the highest scorer at or above ``top``.

        A tie is broken in favour of the player who gained most points in the
        last round (in Catan you can only win during your own turn); players
        still tied share the victory.
        """
        candidates = [p for p, score in self.totalScores.items() if score >= self.top]
        if not candidates:
            return
        maxscore = max(self.totalScores[p] for p in candidates)
        candidates = [p for p in candidates if self.totalScores[p] == maxscore]
        if len(candidates) > 1 and self.rounds:
            last = self.rounds[-1]
            best = max(last.getPlayerScore(p) for p in candidates)
            candidates = [p for p in candidates if last.getPlayerScore(p) == best]
        self.setWinners(candidates)

    def getPlayerState(self, player: str) -> dict[str, int]:
        """Return ``player``'s current holdings: setup plus every round."""
        state = self.getInitialState()
        for rnd in cast("list[CatanRound]", self.rounds):
            for key, value in rnd.getChanges(player).items():
                state[key] += value
        return state

    def getInitialState(self) -> dict[str, int]:
        """Return the holdings every player has once the setup phase is over."""
        state = dict.fromkeys(self.components, 0)
        state["settlements"] = self.initial_settlements
        return state

    @classmethod
    def victoryPoints(cls, state: dict[str, int]) -> int:
        """Return the victory points worth of ``state`` (holdings or changes)."""
        return sum(cls.components[key] * state.get(key, 0) for key in cls.components)

    def getTop(self) -> int:
        return self.top


class CatanRound(GenericRound):
    """A Catan round: each player's holding changes and the points they earn."""

    def __init__(self, numround: int) -> None:
        super().__init__(numround)
        self.changes: dict[str, dict[str, int]] = {}

    def addExtraInfo(self, player: str, extras: dict) -> None:
        """Record ``player``'s holding changes from ``extras``."""
        self.changes[player] = {
            key: int(extras.get(key, 0)) for key in CatanMatch.components
        }

    def getChanges(self, player: str) -> dict[str, int]:
        """Return ``player``'s holding changes this round (all zero if none)."""
        try:
            return self.changes[player]
        except KeyError:
            return dict.fromkeys(CatanMatch.components, 0)
