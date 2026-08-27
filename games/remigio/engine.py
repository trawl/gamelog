from typing import cast

from core.engine.base import RoundGameEngine, readInput
from games.remigio.model import RemigioMatch


class RemigioEngine(RoundGameEngine):
    def __init__(self):
        if not hasattr(self, "game"):
            self.game = "Remigio"
        RoundGameEngine.__init__(self)

    def getActivePlayers(self):
        return cast("RemigioMatch", self.match).getActivePlayers()

    def isPlayerOff(self, player):
        return cast("RemigioMatch", self.match).isPlayerOff(player)

    def wasPlayerOff(self, player, nround):
        totalscore = 0
        isoff = False
        for rnd in self.getRounds():
            totalscore += rnd.getPlayerScore(player)
            isoff = totalscore >= self.getTop()
            if nround == rnd.getNumRound():
                break

        return isoff

    def getTop(self):
        return cast("RemigioMatch", self.match).getTop()

    def setTop(self, top):
        cast("RemigioMatch", self.match).setTop(top)

    def printExtraPlayerStats(self, player):
        if player not in self.getActivePlayers():
            print("   Player Down!")

    def printExtraStats(self):
        print(f"Match top: {self.getTop()}")

    def updateRRDealer(self, back=False):
        candidate = self.porder.index(self.getDealer())
        increment = -1 if back else 1
        while True:
            candidate = (candidate + increment) % len(self.porder)
            player = self.porder[candidate]
            if not self.isPlayerOff(player):
                self.match.setDealer(player)
                break

    def runRoundPlayer(self, player, winner=None):
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

    def extraStubConfig(self):
        top = readInput("Top score: ", int, lambda x: x > 0)
        self.setTop(top)


if __name__ == "__main__":
    re = RemigioEngine()
    re.gameStub()
