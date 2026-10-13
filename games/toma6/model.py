"""6 Nimmt! (Toma6) match and round models."""

from __future__ import annotations

from collections.abc import Sequence

from core.model.match import GenericRound, GenericRoundMatch


class Toma6Match(GenericRoundMatch):
    """Round-based match for Toma6, won by the lowest score once ``top`` is hit."""

    def __init__(self, players: Sequence[str] = ()) -> None:
        super().__init__(players)
        self.game = "Toma6"
        self.top = 66

    def computeWinner(self) -> None:
        """Once any player reaches ``top``, the lowest total score wins;
        players tied on it share the victory."""
        if max(self.totalScores.values()) >= self.top:
            minscore = min(self.totalScores.values())
            self.setWinners([p for p, s in self.totalScores.items() if s == minscore])

    def createRound(self, numround: int) -> GenericRound:
        return Toma6Round(numround)

    def getTop(self) -> int:
        return self.top

    def setTop(self, top: int) -> None:
        self.top = top


class Toma6Round(GenericRound):
    """A Toma6 round; identical to the generic round."""
