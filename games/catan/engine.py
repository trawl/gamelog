"""Catan play-time engine."""

from __future__ import annotations

from typing import cast

from core.engine.engine import RoundGameEngine, readInput
from games.catan.model import CatanMatch


class CatanEngine(RoundGameEngine):
    """Engine driving a Catan match, its holdings and target victory points."""

    def __init__(self) -> None:
        if not hasattr(self, "game"):
            self.game = "Catan"
        super().__init__()

    def getTop(self) -> int:
        return cast("CatanMatch", self.match).getTop()

    def getComponents(self) -> dict[str, int]:
        return cast("CatanMatch", self.match).components

    def getLimits(self) -> dict[str, int]:
        return cast("CatanMatch", self.match).limits

    def getAwards(self) -> tuple[str, ...]:
        return cast("CatanMatch", self.match).awards

    def getPlayerState(self, player: str) -> dict[str, int]:
        return cast("CatanMatch", self.match).getPlayerState(player)

    def getInitialState(self) -> dict[str, int]:
        return cast("CatanMatch", self.match).getInitialState()

    def victoryPoints(self, state: dict[str, int]) -> int:
        return cast("CatanMatch", self.match).victoryPoints(state)

    def printExtraStats(self) -> None:
        print(f"Victory points to win: {self.getTop()}")

    def printExtraPlayerStats(self, player: str) -> None:
        state = self.getPlayerState(player)
        print(", ".join(f"{key}: {value}" for key, value in state.items()))

    def runRoundPlayer(self, player: str, winner: str | None = None) -> None:
        """CLI harness: read ``player``'s holding changes and record them."""
        changes = {}
        for key in self.getComponents():
            changes[key] = readInput(
                f"{player} {key} change: ",
                int,
                lambda x: True,
                "Sorry, invalid number.",
            )
        self.addRoundInfo(player, self.victoryPoints(changes), changes)


if __name__ == "__main__":
    re = CatanEngine()
    re.gameStub()
