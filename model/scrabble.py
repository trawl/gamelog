from controllers.db import db
from model.base import GenericEntry, GenericRoundMatch


class ScrabbleMatch(GenericRoundMatch):
    bonuses = ("dl", "tl", "dw", "tw", "bingo")

    def __init__(self, players=()):
        super().__init__(players)
        self.game = "Scrabble"
        self.dealingp = 1
        self.updatewinnereveryround = False

    def createRound(self, numround):
        return ScrabbleEntry(numround)

    def getBonuses(self):
        return self.bonuses

    def flushToDB(self):
        super().flushToDB()
        for entry in self.rounds:
            for bonus, tally in entry.getBonuses().items():
                if tally:
                    db.execute(
                        "INSERT OR REPLACE INTO RoundStatistics "
                        "(idMatch,nick,idRound,key,value) "
                        f"VALUES ({self.idMatch},'{entry.getPlayer()}',{entry.getNumEntry()},'{bonus}','{tally}');"
                    )

    def computeWinner(self):
        maxscore = max(self.totalScores.values())
        candidates = [
            player for player, score in self.totalScores.items() if score == maxscore
        ]
        if len(candidates) == 1:
            self.winner = candidates.pop()
            return
        # Draw: check who's got more bonuses
        bonuses_tally = {player: 0 for player in candidates}
        for entry in self.getRounds():
            try:
                bonuses_tally[entry.getPlayer()] += sum(entry.getBonuses().values())
            except KeyError:
                pass

        max_bonuses = max(bonuses_tally.values())

        for player, bonus_tally in bonuses_tally.items():
            if bonus_tally != max_bonuses:
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


class ScrabbleEntry(GenericEntry):
    def __init__(self, numround):
        super().__init__(numround)
        self.bonuses = {"dl": 0, "tl": 0, "dw": 0, "tw": 0, "bingo": 0}

    def addExtraInfo(self, player, extras):
        try:
            self.bonuses = extras
        except KeyError:
            pass

    def getBonuses(self):
        return self.bonuses

    def __repr__(self):
        return f"{self.getNumEntry()}: {self.getPlayer()} - {self.getPlayerScore()} | {self.getBonuses()}"
