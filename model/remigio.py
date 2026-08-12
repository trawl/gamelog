from controllers.db import db
from model.base import GenericRound, GenericRoundMatch


class RemigioMatch(GenericRoundMatch):
    def __init__(self, players=()):
        super().__init__(players)
        self.game = "Remigio"
        self.activeplayers = []
        self.playersoff = []
        self.top = 100

    def playerStart(self, player):
        if self.getScoreFromPlayer(player) < self.top:
            self.activeplayers.append(player)
        else:
            self.playersoff.append(player)

    def addRound(self, rnd):
        closeType = rnd.getCloseType()
        if closeType > 1:
            for player in rnd.getScore().keys():  # noqa: SIM118
                rnd.setPlayerScore(player, closeType * rnd.getPlayerScore(player))
        GenericRoundMatch.addRound(self, rnd)

    def deleteRound(self, nrnd):
        super().deleteRound(nrnd)
        for player in self.playersoff[:]:
            if self.totalScores[player] < self.top:
                self.activeplayers.append(player)
                self.playersoff.remove(player)

    def computeWinner(self):
        for p in self.activeplayers[:]:
            if self.totalScores[p] >= self.top:
                self.activeplayers.remove(p)
                self.playersoff.append(p)

        if len(self.activeplayers) == 1:
            self.winner = self.activeplayers[0]

    def resumeMatch(self, idMatch):
        if not super().resumeMatch(idMatch):
            return False

        cur = db.execute(
            f"SELECT value FROM MatchExtras WHERE idMatch ={idMatch} and key='Top';"
        )
        if cur:
            row = cur.fetchone()
            if row:
                self.top = int(row["value"])

        for player in self.getPlayers():
            self.playerStart(player)

        return True

    def resumeExtraInfo(self, player, key, value):
        extra = {}
        if key == "closeType":
            extra[key] = int(value)
        return extra

    def createRound(self, numround):
        return RemigioRound(numround)

    def getActivePlayers(self):
        return self.activeplayers

    def getPlayersOff(self):
        return self.playersoff

    def isPlayerOff(self, player):
        return player in self.playersoff

    def getTop(self):
        return self.top

    def setTop(self, top):
        if top <= 0:
            return
        self.top = top

    def flushToDB(self):
        super().flushToDB()
        db.execute(
            "INSERT OR REPLACE INTO MatchExtras (idMatch,key,value) "
            f"VALUES ({self.idMatch},'Top','{self.top}');"
        )
        for rnd in self.rounds:
            db.execute(
                "INSERT OR REPLACE INTO RoundStatistics "
                "(idMatch,nick,idRound,key,value) "
                f"VALUES ({self.idMatch},'{rnd.getWinner()}',{rnd.getNumRound()},'closeType','{rnd.closeType}');"
            )


class RemigioRound(GenericRound):
    def __init__(self, numround):
        super().__init__(numround)
        self.closeType = 1

    def addExtraInfo(self, player, extras):
        player = str(player)
        if player == self.getWinner():
            try:
                self.closeType = extras["closeType"]
            except KeyError:
                pass

    def getCloseType(self):
        return self.closeType
