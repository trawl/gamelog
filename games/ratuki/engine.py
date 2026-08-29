"""Ratuki play-time engine."""

from __future__ import annotations

from typing import cast

from core.engine.base import RoundGameEngine, readInput
from games.ratuki.model import RatukiMatch


class RatukiEngine(RoundGameEngine):
    """Engine driving a Ratuki match and its target-score configuration."""

    def __init__(self) -> None:
        if not hasattr(self, "game"):
            self.game = "Ratuki"
        super().__init__()

    def getTop(self) -> int:
        return cast("RatukiMatch", self.match).getTop()

    def setTop(self, top: int) -> None:
        cast("RatukiMatch", self.match).setTop(top)

    def printExtraStats(self) -> None:
        print(f"Match top: {self.getTop()}")

    def extraStubConfig(self) -> None:
        top = readInput("Top score: ", int, lambda x: x > 0)
        self.setTop(top)

    def runRoundPlayer(self, player: str, winner: str | None = None) -> None:
        """CLI harness: read ``player``'s round score and record it."""
        score = readInput(
            f"{player} round score: ",
            int,
            lambda x: True,
            "Sorry, invalid score number.",
        )
        self.addRoundInfo(player, score)


if __name__ == "__main__":
    re = RatukiEngine()
    re.gameStub()
