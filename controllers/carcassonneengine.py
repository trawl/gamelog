#!/usr/bin/env python
# -*- coding: utf-8 -*-
from typing import cast

from controllers.baseengine import EntryGameEngine, readInput
from controllers.db import db
from controllers.statsengine import ParticularStatsEngine, StatsEngine
from model.carcassonne import CarcassonneMatch


class CarcassonneEngine(EntryGameEngine):
    def __init__(self):
        EntryGameEngine.__init__(self)
        self.game = "Carcassonne"

    def runStubRoundPlayer(self, player, winner=None):
        entry_kinds = self.getEntryKinds()
        score = readInput(
            "{} score: ".format(player),
            int,
            lambda x: x > 0,
            "Sorry, invalid score number.",
        )
        errmsg = "Sorry, invalid kind [{}]".format(",".join(entry_kinds))
        kind = readInput("Kind: ", str, lambda x: x in entry_kinds, errmsg)
        self.addEntry(player, score, {"kind": kind})

    def getEntryKinds(self):
        self.match = cast("CarcassonneMatch", self.match)
        return self.match.getEntryKinds()


if __name__ == "__main__":
    re = CarcassonneEngine()
    re.gameStub()


class CarcassonneStatsQueries(object):
    singleKindRecordQuery = """
    SELECT value as "record",
        Round.score as "points",
        RoundStatistics.nick as "player",
        DATE(Match.finished) as date
    FROM Match,Round,RoundStatistics
    WHERE Match.idMatch = Round.idMatch
        and Round.idMatch = RoundStatistics.idMatch
        and Round.idRound = RoundStatistics.idRound
        and Round.nick = RoundStatistics.nick
        and Match.state = 1
        and Game_name="Carcassonne"
        and key="kind"
        and value = '{}'
        and Round.score>0
    order by points desc
    limit 1
    """

    matchKindRecordQuery = """
        SELECT Match.idMatch as "match",
            value as "record",
            SUM(Round.score) as "points",
            RoundStatistics.nick as "player",
            DATE(Match.finished) as date
    FROM Match,Round,RoundStatistics
    WHERE Match.idMatch = Round.idMatch
        and Round.idMatch = RoundStatistics.idMatch
        and Round.idRound = RoundStatistics.idRound
        and Round.nick = RoundStatistics.nick
        and Match.state = 1
        and Game_name="Carcassonne"
        and key="kind"
        and value = '{}'
        and Round.score>0
   GROUP BY "match","record","player"
   ORDER BY points desc
   LIMIT 1
   """


class CarcassonneStatsEngine(StatsEngine):
    def __init__(self):
        super(CarcassonneStatsEngine, self).__init__()
        self.singleKindRecord = []
        q = CarcassonneStatsQueries()
        self._singleKindRecordQuery = q.singleKindRecordQuery
        self._matchKindRecordQuery = q.matchKindRecordQuery

    def update(self, players=None):
        super(CarcassonneStatsEngine, self).update()
        self.singleKindRecord = []
        self.matchKindRecord = []

        for kind in ("City", "Road", "Field"):
            self.singleKindRecord += db.queryDict(
                self._singleKindRecordQuery.format(kind)
            )

        for kind in ("City", "Road", "Cloister", "Field", "Fair"):
            self.matchKindRecord += db.queryDict(
                self._matchKindRecordQuery.format(kind)
            )

    def getSingleKindRecords(self):
        return self.singleKindRecord

    def getMatchKindRecords(self):
        return self.matchKindRecord


class CarcassonneParticularStatsEngine(CarcassonneStatsEngine, ParticularStatsEngine):
    def updatePlayers(self, players):
        super(CarcassonneParticularStatsEngine, self).updatePlayers(players)
        if players:
            q = CarcassonneStatsQueries()
            self._singleKindRecordQuery = q.singleKindRecordQuery.replace(
                "WHERE", "WHERE {} AND".format("Match." + self._newclause)
            )
            self._matchKindRecordQuery = q.matchKindRecordQuery.replace(
                "WHERE", "WHERE {} AND".format("Match." + self._newclause)
            )
