#!/usr/bin/env python
# -*- coding: utf-8 -*-

from controllers.baseengine import RoundGameEngine, readInput
from controllers.statsengine import StatsEngine, ParticularStatsEngine
from controllers.db import db


class SkullKingEngine(RoundGameEngine):
    def __init__(self):
        super(SkullKingEngine, self).__init__()
        self.game = 'Skull King'
        self.hands = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]

    def runRoundPlayer(self, player, winner):
        score = readInput("{} round score: ".format(player),
                          int, lambda x: True, "Sorry, invalid score number.")
        self.addRoundInfo(player, score)

    def getHands(self, rnd=None):
        index = self.getNumRound()-1
        if rnd is not None:
            index = rnd - 1
        try:
            return self.hands[index]
        except IndexError:
            return self.hands[-1]

class SkullKingStatsQueries(object):
    hitsQuery = """
    SELECT player, max(hits) as "max_hits", min(hits) as "min_hits" from (
        SELECT Round.idMatch as idm, Round.nick as "player",
            COUNT(Round.idRound) as "hits"
        FROM Round,Match
        WHERE Match.idMatch = Round.idMatch
            and Match.state = 1
            and Game_name="Skull King"
            and Round.score>=10
        group by idm, player
    ) as tmp
    group by player
    order by player
    """

    extremeRounds = """
    SELECT Round.nick as "player", max(score) as "max_round_score",
        min(score) as "min_round_score"
    FROM Round,Match
    WHERE Match.idMatch = Round.idMatch
        and Match.state = 1
        and Game_name="Skull King"
    group by player
   """


class SkullKingStatsEngine(StatsEngine):

    def __init__(self):
        super(SkullKingStatsEngine, self).__init__()
        self.singleKindRecord = None
        q = SkullKingStatsQueries()
        self._hitsQuery = q.hitsQuery
        self._extremeRounds = q.extremeRounds

    def update(self):
        super(SkullKingStatsEngine, self).update()
        self.hitsRecord = db.queryDict(self._hitsQuery)
        self.extremeRoundsRecord = db.queryDict(self._extremeRounds)

        for row in self.hitsRecord:
            player = row['player']
            for r2 in self.generalplayerstats:
                if r2['nick'] == player and r2['game'] == "Skull King":
                    r2['max_hits'] = row['max_hits']
                    r2['min_hits'] = row['min_hits']
                    break
        for row in self.extremeRoundsRecord:
            player = row['player']
            for r2 in self.generalplayerstats:
                if r2['nick'] == player and r2['game'] == "Skull King":
                    r2['max_round_score'] = row['max_round_score']
                    r2['min_round_score'] = row['min_round_score']
                    break


class SkullKingParticularStatsEngine(SkullKingStatsEngine, ParticularStatsEngine):

    def updatePlayers(self, players):
        super(SkullKingParticularStatsEngine, self).updatePlayers(players)
        if players:
            q = SkullKingStatsQueries()
            self._hitsQuery = q.hitsQuery.replace(
                'WHERE', "WHERE {} AND".format("Match." + self._newclause))
            self._extremeRounds = q.extremeRounds.replace(
                'WHERE', "WHERE {} AND".format("Match." + self._newclause))


if __name__ == "__main__":
    re = SkullKingEngine()
    re.gameStub()
