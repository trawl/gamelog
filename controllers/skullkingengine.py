#!/usr/bin/env python
# -*- coding: utf-8 -*-
from typing import cast

from controllers.pochaengine import (
    PochaEngine,
    PochaParticularStatsEngine,
    PochaStatsEngine,
)
from model.skullking import SkullKingMatch


class SkullKingEngine(PochaEngine):
    def __init__(self):
        if not hasattr(self, "game"):
            self.game = "Skull King"
        super(SkullKingEngine, self).__init__()
        self.hands = cast("SkullKingMatch", self.match).getHands()

    def getScoringMode(self):
        return cast("SkullKingMatch", self.match).getScoringMode()

    def getRoundMode(self):
        return cast("SkullKingMatch", self.match).getRoundMode()

    def getRoundSequence(self, mode=None):
        return cast("SkullKingMatch", self.match).getRoundSequence(mode)

    def setScoringMode(self, scoring_mode):
        cast("SkullKingMatch", self.match).setScoringMode(scoring_mode)

    def setRoundMode(self, round_mode):
        cast("SkullKingMatch", self.match).setRoundMode(round_mode)
        self.hands = cast("SkullKingMatch", self.match).getHands()

    def listBonusTypes(self):
        return cast("SkullKingMatch", self.match).listBonusTypes()

    def getBonusReps(self, bonus_name):
        return cast("SkullKingMatch", self.match).getBonusReps(bonus_name)

    def listScoringModes(self):
        return cast("SkullKingMatch", self.match).listScoringModes()

    def listRoundModes(self):
        return cast("SkullKingMatch", self.match).listRoundModes()

    def computePlayerBonuses(self, bonuses):
        points = 0
        for btype in cast("SkullKingMatch", self.match).listBonusTypes():
            try:
                points += bonuses[btype] * cast("SkullKingMatch", self.match).getBonus(
                    btype
                )
            except KeyError:
                pass
        return points

    def computePlayerScoreClassic(self, expected, won, bonuses):
        if expected == 0 and won == 0:
            return self.getNumRound() * 10
        if expected == 0 and won != 0:
            return self.getNumRound() * -10
        if expected == won:
            return won * 20 + self.computePlayerBonuses(bonuses)
        return -10 * abs(expected - won)

    def computePlayerScoreRascal(self, expected, won, bonuses):
        diff = abs(won - expected)
        cannonball = "cannonball" in bonuses and bonuses["cannonball"]
        if cannonball:
            score = self.getNumRound() * 15 + self.computePlayerBonuses(bonuses)
        else:
            score = self.getNumRound() * 10 + self.computePlayerBonuses(bonuses)
        if diff == 0:
            return score
        if diff == 1 and not cannonball:
            return score // 2
        return 0

    def computePlayerScore(self, expected, won, bonuses):
        if self.getScoringMode() in ("classic_scoring", "standard_scoring"):
            return self.computePlayerScoreClassic(expected, won, bonuses)
        elif self.getScoringMode() == "rascal_scoring":
            return self.computePlayerScoreRascal(expected, won, bonuses)
        raise ValueError(f"Unknown scoring mode {self.getScoringMode()}")


class SkullKingStatsQueries(object):
    hitsQuery = """
    SELECT player, max(hits) as "max_hits", min(hits) as "min_hits", round(avg(hits),2) as "avg_hits" from (
        SELECT Round.idMatch as idm, Round.nick as "player",
            COUNT(Round.idRound) as "hits"
        FROM Round,Match
        WHERE Match.idMatch = Round.idMatch
            and Match.state = 1
            and Game_name="#GAMENAME#"
            and Round.score > 0
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


class SkullKingStatsEngine(PochaStatsEngine):
    def __init__(self):
        super(SkullKingStatsEngine, self).__init__()
        self.game = "Skull King"
        self.define_queries()

    def define_queries(self):
        q = SkullKingStatsQueries()
        self._hitsQuery = q.hitsQuery.replace("#GAMENAME#", self.game)
        self._extremeRounds = q.extremeRounds.replace("#GAMENAME#", self.game)


class SkullKingParticularStatsEngine(PochaParticularStatsEngine):
    def __init__(self):
        super().__init__()
        self.game = "Skull King"
        self.define_queries()

    def define_queries(self):
        q = SkullKingStatsQueries()
        self._hitsQuery = q.hitsQuery.replace("#GAMENAME#", self.game)
        self._extremeRounds = q.extremeRounds.replace("#GAMENAME#", self.game)


if __name__ == "__main__":
    re = SkullKingEngine()
    re.gameStub()
