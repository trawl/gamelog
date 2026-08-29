"""Toma6 play-time engine."""

from __future__ import annotations

from typing import cast

from core.engine.base import readInput
from games.remigio.engine import RemigioEngine
from games.toma6.model import Toma6Match


class Toma6Engine(RemigioEngine):
    """Engine driving a Toma6 match, reusing Remigio's round handling."""

    def __init__(self) -> None:
        if not hasattr(self, "game"):
            self.game = "Toma6"
        super().__init__()

    def getTop(self) -> int:
        return cast("Toma6Match", self.match).getTop()

    def printExtraStats(self) -> None:
        print(f"Match top: {self.getTop()}")

    def runRoundPlayer(self, player: str, winner: str | None = None) -> None:
        """CLI harness: read ``player``'s round score and record it."""
        score = 0
        score = readInput(
            f"{player} round score: ",
            int,
            lambda x: x > 0,
            "Sorry, invalid score number.",
        )
        self.addRoundInfo(player, score)


if __name__ == "__main__":
    re = Toma6Engine()
    re.gameStub()
