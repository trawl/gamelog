from typing import cast

from core.engine.base import readInput
from controllers.remigioengine import RemigioEngine
from model.toma6 import Toma6Match


class Toma6Engine(RemigioEngine):
    def __init__(self):
        if not hasattr(self, "game"):
            self.game = "Toma6"
        super().__init__()

    def getTop(self):
        return cast("Toma6Match", self.match).getTop()

    def printExtraStats(self):
        print(f"Match top: {self.getTop()}")

    def runRoundPlayer(self, player, winner=None):
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
