#!/usr/bin/env python
# -*- coding: utf-8 -*-
from controllers.db import GameLogDB, db


class StatsEngine(object):
    _lastwinnerquery = """
    SELECT Game_name AS game,
        nick AS lastwinner,
        DATETIME(finished) AS lastwinnerdate
    FROM Match JOIN MatchPlayer USING(idMatch)
    WHERE winner=1
    GROUP BY game
    HAVING MAX(strftime('%s', finished))
    ORDER BY game,finished;
    """

    _generalmatchstatsquery = """
     SELECT game,
        nplayers,
        TIME(MAX(elapsed),'unixepoch') AS maxduration,
        TIME(MIN(elapsed),'unixepoch') AS minduration,
        TIME(AVG(elapsed),'unixepoch') AS avgduration,
        MAX(CAST(maxscore as integer)) AS maxscore,
        MIN(CAST(minscore as integer)) AS minscore,
        CAST(ROUND(AVG(CAST(avgscore as integer))) as integer) AS avgscore
    FROM (
        SELECT Game_name as game,
            idMatch, elapsed,
            MAX( totalScore) AS maxscore,
            MIN( totalScore) AS minscore,
            AVG( totalScore) AS avgscore,
            count(nick) AS 'nplayers'
        FROM Match JOIN MatchPlayer USING (idMatch)
        WHERE state=1
        GROUP BY game, idMatch
        ) AS tmp
    GROUP BY game, nplayers ORDER BY game, nplayers;
    """

    _generalplayerstatsquery = """
    SELECT Game_name as game, nick,
        MAX(CAST(totalScore AS integer)) AS maxscore,
        MIN(CAST(totalScore AS integer)) AS minscore,
        CAST(ROUND(AVG(CAST(totalScore AS integer))) AS integer) AS avgscore,
        SUM(CAST(totalScore AS integer)) AS sumscore,
        SUM(winner) AS victories,
        COUNT(*) AS played,
        ROUND(CAST(SUM(winner) AS REAL)*100/COUNT(nick),2) as victoryp
    FROM Match JOIN MatchPlayer USING (idMatch)
    WHERE state=1
    GROUP BY game, nick
    ORDER BY game, victoryp DESC, played DESC;
    """

    def __init__(self):
        self.generalgamestats = None
        self.generalmatchstats = None
        self.generalplayerstats = None

    def update(self, _players=None):
        # Number of matches played
        self.generalgamestats = db.queryDict(self._lastwinnerquery)
        self.generalmatchstats = db.queryDict(self._generalmatchstatsquery)
        self.generalplayerstats = db.queryDict(self._generalplayerstatsquery)

    def getGameStats(self, game):
        if self.generalgamestats:
            for row in self.generalgamestats:
                if row["game"] == game:
                    return row
        return None

    def getMatchGameStats(self, game):
        if self.generalmatchstats:
            return [row for row in self.generalmatchstats if row["game"] == game]
        return None

    def getPlayerGameStats(self, game):
        if self.generalplayerstats:
            return [row for row in self.generalplayerstats if row["game"] == game]
        return None


class ParticularStatsEngine(StatsEngine):
    def __init__(self):
        super(ParticularStatsEngine, self).__init__()
        self._lastwinnerquerybase = self._lastwinnerquery
        self._generalmatchstatsquerybase = self._generalmatchstatsquery
        self._generalplayerstatsquerybase = self._generalplayerstatsquery
        self.players = None
        self._newclause = ""

    def update(self, players=None):
        self.updatePlayers(players)
        super(ParticularStatsEngine, self).update()

    def updatePlayers(self, players):
        if players:
            splayers = set(players)
            if self.players != splayers:
                self.players = splayers
                players_str = ",".join(["'" + p + "'" for p in self.players])
                self._newclause = (
                    "idMatch IN ("
                    "SELECT idMatch FROM MatchPlayer "
                    "WHERE nick IN ({0}) "
                    "GROUP BY idMatch "
                    "HAVING COUNT(*)={1} and idMatch NOT IN ("
                    "SELECT idMatch FROM MatchPlayer "
                    "WHERE nick NOT IN ({0})))"
                )
                self._newclause = self._newclause.format(players_str, len(self.players))
                self._lastwinnerquery = self._lastwinnerquerybase.replace(
                    "WHERE", "WHERE {} AND".format(self._newclause)
                )
                self._generalmatchstatsquery = self._generalmatchstatsquerybase.replace(
                    "WHERE", "WHERE {} AND".format(self._newclause)
                )
                self._generalplayerstatsquery = (
                    self._generalplayerstatsquerybase.replace(
                        "WHERE", "WHERE {} AND".format(self._newclause)
                    )
                )


if __name__ == "__main__":
    db = GameLogDB()
    db.connectDB("../db/gamelog.db")
    #     se = StatsEngine()
    #     se.update()
    #     print(se.getMatchGameStats('Phase10Master'))
    #     print(se.getPlayerGameStats('Phase10Master'))

    pse = ParticularStatsEngine()
    pse.update(["Xavi", "Rosa", "Dani", "Joan"])
    print(pse.getMatchGameStats("Phase10Master"))
    print(pse.getPlayerGameStats("Phase10Master"))
