from controllers.db import db
from model.base import GenericRoundMatch


class RatukiMatch(GenericRoundMatch):
    def __init__(self, players=()):
        super().__init__(players)
        self.game = "Ratuki"
        self.top = 100

    def resumeMatch(self, idMatch):
        if not super().resumeMatch(idMatch):
            return False

        for player in self.getPlayers():
            self.playerStart(player)

        cur = db.execute(
            f"SELECT value FROM MatchExtras WHERE idMatch ={idMatch} and key='Top';"
        )
        row = cur.fetchone()
        if row:
            self.top = int(row["value"])

        return True

    def computeWinner(self):
        winner = None
        maxscore = self.top
        for player, score in self.totalScores.items():
            if score >= maxscore:
                winner = player
                maxscore = score

        if winner is not None:
            self.winner = winner

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
