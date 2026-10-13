"""Pocha match model: a round-based trick-taking scoring game."""

from __future__ import annotations

from collections.abc import Sequence

from core.model.match import GenericRoundMatch


class PochaMatch(GenericRoundMatch):
    """Round-based match for Pocha, with its fixed ascending/descending hands."""

    def __init__(self, players: Sequence[str] = ()) -> None:
        super().__init__(players)
        self.game = "Pocha"
        self.dealingp = 1
        self.hands: list[int] = [1, 2, 3, 4, 5, 6, 7, 8, 8, 8, 8, 7, 6, 5, 4, 3, 2, 1]
        self.maxRounds = len(self.hands)

    def resumeMatch(self, idMatch: int) -> bool:
        """Reload the base match, then re-initialise per-player state."""
        if not super().resumeMatch(idMatch):
            return False

        for player in self.getPlayers():
            self.playerStart(player)

        return True

    def computeWinner(self) -> None:
        """Set the winner (highest total) once every round has been played;
        players tied on it share the victory."""
        if len(self.rounds) < self.maxRounds:
            return
        maxscore = max(self.totalScores.values())
        self.setWinners([p for p, s in self.totalScores.items() if s == maxscore])

    def getHands(self) -> list[int]:
        return self.hands
