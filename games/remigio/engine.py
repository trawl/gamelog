"""Remigio play-time engine."""

from __future__ import annotations

from collections.abc import Sequence
from typing import cast

from core.engine.base import RoundGameEngine, readInput
from games.remigio.model import RemigioMatch


class RemigioEngine(RoundGameEngine):
    """Round engine driving a Remigio match, with elimination on the top score."""

    def __init__(self) -> None:
        if not hasattr(self, "game"):
            self.game = "Remigio"
        RoundGameEngine.__init__(self)

    def getActivePlayers(self) -> Sequence[str]:
        return cast("RemigioMatch", self.match).getActivePlayers()

    def isPlayerOff(self, player: str) -> bool:
        return cast("RemigioMatch", self.match).isPlayerOff(player)

    def wasPlayerOff(self, player: str, nround: int) -> bool:
        """Whether ``player``'s cumulative score was over the top by ``nround``."""
        totalscore = 0
        isoff = False
        for rnd in self.getRounds():
            totalscore += rnd.getPlayerScore(player)
            isoff = totalscore >= self.getTop()
            if nround == rnd.getNumRound():
                break

        return isoff

    def getTop(self) -> int:
        return cast("RemigioMatch", self.match).getTop()

    def setTop(self, top: int) -> None:
        cast("RemigioMatch", self.match).setTop(top)

    def printExtraPlayerStats(self, player: str) -> None:
        if player not in self.getActivePlayers():
            print("   Player Down!")

    def printExtraStats(self) -> None:
        print(f"Match top: {self.getTop()}")

    def updateRRDealer(self, back: bool = False) -> None:
        """Round-robin rotation that skips players already out of the match."""
        dealer = self.getDealer()
        if dealer is None:
            return
        candidate = self.porder.index(dealer)
        increment = -1 if back else 1
        while True:
            candidate = (candidate + increment) % len(self.porder)
            player = self.porder[candidate]
            if not self.isPlayerOff(player):
                self.match.setDealer(player)
                break

    def runRoundPlayer(self, player: str, winner: str | None = None) -> None:
        """CLI harness: read a player's round score, or close type if they won."""
        score = 0
        closeType = 1
        if winner == player:
            closeType = readInput(
                f"{player} close type: ",
                int,
                lambda x: x in [1, 2, 3, 4],
                "Sorry, invalid Close Type number [1,2,3,4].",
            )
        else:
            score = readInput(
                f"{player} round score: ",
                int,
                lambda x: x > 0,
                "Sorry, invalid score number.",
            )
        self.addRoundInfo(player, score, {"closeType": closeType})

    def extraStubConfig(self) -> None:
        """CLI harness: prompt for the match's top score."""
        top = readInput("Top score: ", int, lambda x: x > 0)
        self.setTop(top)


if __name__ == "__main__":
    re = RemigioEngine()
    re.gameStub()
