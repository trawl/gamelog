from controllers.db import db
from model.base import GenericEntry, GenericRoundMatch


class QwirkleMatch(GenericRoundMatch):
    def __init__(self, players=()):
        super().__init__(players)
        self.game = "Qwirkle"
        self.dealingp = 1
        self.updatewinnereveryround = False

    def createRound(self, numround):
        return QwirkleEntry(numround)

    def addRound(self, rnd):
        self.rounds.append(rnd)
        for player, score in rnd.getScore().items():
            self.totalScores[player] += score
            self.playerAddRound(player, rnd)

    def flushToDB(self):
        super().flushToDB()
        for entry in self.rounds:
            if entry.getQwirkles():
                db.execute(
                    "INSERT OR REPLACE INTO RoundStatistics "
                    "(idMatch,nick,idRound,key,value) "
                    f"VALUES ({self.idMatch},'{entry.getPlayer()}',{entry.getNumEntry()},'qwirkles','{entry.getQwirkles()}');"
                )

    def computeWinner(self):
        maxscore = max(self.totalScores.values())
        candidates = [
            player for player, score in self.totalScores.items() if score == maxscore
        ]
        if len(candidates) == 1:
            self.winner = candidates.pop()
            return
        # Draw: check who's got more qwirkles
        qwirkles_tally = {player: 0 for player in candidates}
        for entry in self.getRounds():
            qwirkles = entry.getQwirkles()
            if qwirkles:
                try:
                    qwirkles_tally[entry.getPlayer()] += qwirkles
                except KeyError:
                    pass

        max_qwirkles = max(qwirkles_tally.values())

        for player, qwirkles in qwirkles_tally.items():
            if qwirkles != max_qwirkles:
                candidates.remove(player)

        if len(candidates) == 1:
            self.winner = candidates.pop()
            return

        # Draw: Check who's got max single play score
        max_entry_scores = {player: 0 for player in candidates}
        for entry in self.getRounds():
            try:
                max_entry_scores[entry.getPlayer()] = max(
                    max_entry_scores[entry.getPlayer()], entry.getPlayerScore()
                )
            except KeyError:
                pass
        max_entry_score = max(max_entry_scores.values())

        for player, score in max_entry_scores.items():
            if score != max_entry_score:
                candidates.remove(player)

        if len(candidates) == 1:
            self.winner = candidates.pop()
            return

        # Ultimate draw, pick the first candidate then...
        self.winner = candidates.pop()
        return


class QwirkleEntry(GenericEntry):
    def __init__(self, numround):
        super().__init__(numround)
        self.qwirkles = 0

    def addExtraInfo(self, player, extras):
        try:
            self.qwirkles = extras["qwirkles"]
        except KeyError:
            pass

    def getQwirkles(self):
        return self.qwirkles
