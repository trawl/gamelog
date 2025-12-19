#!/usr/bin/env python
# -*- coding: utf-8 -*-

from controllers.db import db
from model.pocha import PochaMatch


class SkullKingMatch(PochaMatch):
    roundModes = {
        "standard_rounds": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
        "even": [2, 4, 6, 8, 10],
        "brawl": [6, 7, 8, 9, 10],
        "skirmish": 5 * [5],
        "barrage": 10 * [10],
        "whirlpool": [9, 7, 5, 3, 1],
    }
    scoringModes = {
        "classic_scoring": {
            "skullking": {"bonus": 50, "reps": 1},
            "pirate": {"bonus": 20, "reps": 6},
        },
        "standard_scoring": {
            "skullking": {"bonus": 40, "reps": 1},
            "pirate": {"bonus": 20, "reps": 6},
            "mermaid": {"bonus": 20, "reps": 2},
            "loot": {"bonus": 20, "reps": 2},
            "fourteen": {"bonus": 10, "reps": 3},
            "blackfourteen": {"bonus": 1, "reps": 1},
            "roatan": {"bonus": 20, "reps": 1},
        },
    }
    scoringModes["rascal_scoring"] = scoringModes["standard_scoring"] | {
        "cannonball": {"bonus": 0, "reps": 1}
    }

    def __init__(self, players=[]):
        super(SkullKingMatch, self).__init__(players)
        self.game = "Skull King"
        self.dealingp = 1
        self.scoringMode = "classic_scoring"
        if len(self.players) > 6:
            self.scoringMode = "standard_scoring"
        self.setRoundMode("standard_rounds")

    def getBonus(self, bonus_name):
        try:
            return self.scoringModes[self.scoringMode][bonus_name]["bonus"]
        except KeyError:
            return 0

    def getBonusReps(self, bonus_name):
        try:
            return self.scoringModes[self.scoringMode][bonus_name]["reps"]
        except KeyError:
            return 0

    def listBonusTypes(self):
        return self.scoringModes[self.scoringMode].keys()

    def listScoringModes(self):
        return [
            sm
            for sm in self.scoringModes.keys()
            if len(self.players) <= 6
            or len(self.players) > 7
            and sm != "classic_scoring"
        ]

    @classmethod
    def listRoundModes(cls):
        return cls.roundModes.keys()

    def getScoringMode(self):
        return self.scoringMode

    def setScoringMode(self, smode):
        if smode not in self.scoringModes:
            raise ValueError(
                f"Invalid Scoring Mode type {smode}. Possible values are: {', '.join(self.scoringModes)}"
            )
        self.scoringMode = smode

    def getRoundMode(self):
        return self.roundMode

    def getRoundSequence(self, mode=None):
        if mode is None:
            mode = self.roundMode
        return self.roundModes[mode]

    def setRoundMode(self, rmode):
        if rmode not in self.roundModes:
            raise ValueError(
                f"Invalid Round Mode type {rmode}. Possible values are: {', '.join(self.roundModes.keys())}"
            )
        self.roundMode = rmode
        self.hands = self.roundModes[self.roundMode]
        self.maxRounds = len(self.hands)

    def getHands(self):
        return self.roundModes[self.roundMode]

    def resumeMatch(self, idMatch):
        if not super(SkullKingMatch, self).resumeMatch(idMatch):
            return False

        cur = db.execute(
            "SELECT value FROM MatchExtras WHERE idMatch ={} and key='scoringMode';".format(
                idMatch
            )
        )
        if cur:
            row = cur.fetchone()
            if row:
                self.scoringMode = row["value"]

        cur = db.execute(
            "SELECT value FROM MatchExtras WHERE idMatch ={} and key='roundMode';".format(
                idMatch
            )
        )
        if cur:
            row = cur.fetchone()
            if row:
                self.roundMode = row["value"]

        for player in self.getPlayers():
            self.playerStart(player)

        return True

    def flushToDB(self):
        super(SkullKingMatch, self).flushToDB()
        db.execute(
            "INSERT OR REPLACE INTO MatchExtras (idMatch,key,value) "
            "VALUES ({},'scoringMode','{}');".format(self.idMatch, self.scoringMode)
        )
        db.execute(
            "INSERT OR REPLACE INTO MatchExtras (idMatch,key,value) "
            "VALUES ({},'roundMode','{}');".format(self.idMatch, self.roundMode)
        )
