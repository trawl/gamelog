#!/usr/bin/env python
# -*- coding: utf-8 -*-
from typing import cast

from controllers.baseengine import RoundGameEngine, readInput
from controllers.db import db
from controllers.statsengine import ParticularStatsEngine, StatsEngine
from model.pocha import PochaMatch


class PochaEngine(RoundGameEngine):
    def __init__(self):
        if not hasattr(self, "game"):
            self.game = "Pocha"
        super(PochaEngine, self).__init__()
        self.setSuitType()

    def runRoundPlayer(self, player, winner=None):
        score = readInput(
            "{} round score: ".format(player),
            int,
            lambda x: True,
            "Sorry, invalid score number.",
        )
        self.addRoundInfo(player, score)

    def getHands(self, rnd=None):
        index = self.getNumRound() - 1
        if rnd is not None:
            index = rnd - 1
        try:
            return cast("PochaMatch", self.match).getHands()[index]
        except IndexError:
            return 1

    def getDirection(self, rnd=None):
        index = self.getNumRound() - 1
        if rnd is not None:
            index = rnd - 1
        try:
            return self.directions[index]
        except IndexError:
            return self.directions[-1]

    def setSuitType(self, st="spanish"):
        self.suitType = st
        slope = (len(cast("PochaMatch", self.match).getHands()) - 4) // 2
        if st == "french":
            suits = ["diamonds", "hearts", "spades", "clovers"]
        else:
            suits = ["coins", "cups", "swords", "clubs"]
        self.directions = ["going up"] * slope + suits + ["going down"] * slope

    def getSuitType(self):
        return self.suitType

    def getRoundSequence(self):
        return cast("PochaMatch", self.match).getHands()


class PochaStatsQueries(object):
    hitsQuery = """
    SELECT player, max(hits) as "max_hits", min(hits) as "min_hits" from (
        SELECT Round.idMatch as idm, Round.nick as "player",
            COUNT(Round.idRound) as "hits"
        FROM Round,Match
        WHERE Match.idMatch = Round.idMatch
            and Match.state = 1
            and Game_name="#GAMENAME#"
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
        and Game_name="#GAMENAME#"
    group by player
   """


class PochaStatsEngine(StatsEngine):
    def __init__(self):
        super(PochaStatsEngine, self).__init__()
        self.singleKindRecord = None
        self.game = "Pocha"
        self.define_queries()

    def define_queries(self):
        q = PochaStatsQueries()
        self._hitsQuery = q.hitsQuery.replace("#GAMENAME#", self.game)
        self._extremeRounds = q.extremeRounds.replace("#GAMENAME#", self.game)

    def update(self, players=None):
        super(PochaStatsEngine, self).update()
        # print(f"Updating {self.game} stats...")
        self.hitsRecord = db.queryDict(self._hitsQuery)
        self.extremeRoundsRecord = db.queryDict(self._extremeRounds)

        if not self.generalplayerstats:
            return

        for row in self.hitsRecord:
            player = row["player"]
            for r2 in self.generalplayerstats:
                if r2["nick"] == player and r2["game"] == self.game:
                    for k in ("avg_hits", "max_hits", "min_hits"):
                        if k in row:
                            r2[k] = row[k]
                    break
        for row in self.extremeRoundsRecord:
            player = row["player"]
            for r2 in self.generalplayerstats:
                if r2["nick"] == player and r2["game"] == self.game:
                    r2["max_round_score"] = row["max_round_score"]
                    r2["min_round_score"] = row["min_round_score"]
                    break


class PochaParticularStatsEngine(PochaStatsEngine, ParticularStatsEngine):
    def updatePlayers(self, players):
        super(PochaParticularStatsEngine, self).updatePlayers(players)
        if players:
            self.define_queries()
            self._hitsQuery = self._hitsQuery.replace(
                "WHERE", "WHERE {} AND".format("Match." + self._newclause)
            ).replace("#GAMENAME#", self.game)
            self._extremeRounds = self._extremeRounds.replace(
                "WHERE", "WHERE {} AND".format("Match." + self._newclause)
            ).replace("#GAMENAME#", self.game)
            # print(self._hitsQuery)


if __name__ == "__main__":
    re = PochaEngine()
    re.gameStub()
