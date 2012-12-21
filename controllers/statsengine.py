#!/usr/bin/env python
# -*- coding: utf-8 -*-

from controllers.db import db,GameLogDB
#import datetime

class StatsEngine:
    
    _lastwinnerquery="""
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
        TIME(MAX(duration),'unixepoch') AS maxduration, 
        TIME(MIN(duration),'unixepoch') AS minduration,
        TIME(AVG(duration),'unixepoch') AS avgduration, 
        MAX(CAST(totalScore as integer)) AS maxscore, 
        MIN(CAST(totalScore as integer)) AS minscore,
        CAST(ROUND(AVG(CAST(totalScore as integer))) as integer) AS avgscore 
    FROM (
        SELECT Game_name as game, 
            idMatch, strftime('%s', finished) - strftime('%s', started) AS duration,
            totalScore, 
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
    ORDER BY game, victoryp DESC;
    """      
    
    def __init__(self):
        self.generalgamestats = None
        self.generalmatchstats = None
        self.generalplayerstats = None
    
    def update(self):
        #Number of matches played
        self.generalgamestats = db.queryDict(self._lastwinnerquery)
        self.generalmatchstats = db.queryDict(self._generalmatchstatsquery)
        self.generalplayerstats = db.queryDict(self._generalplayerstatsquery)
        
    def getGameStats(self,game):
        for row in self.generalgamestats:
            if row['game'] == game:
                return row
        
    def getMatchGameStats(self,game):
        return [ row for row in self.generalmatchstats if row['game'] == game ]
    
    def getPlayerGameStats(self,game):
        return [ row for row in self.generalplayerstats if row['game'] == game ]
    
            
        
if __name__ == "__main__":
    db = GameLogDB()
    db.connectDB("../db/gamelog.db")      
    se = StatsEngine()
    se.update()
    print(se.getMatchGameStats('Phase10Master'))
    print(se.getPlayerGameStats('Phase10Master'))
    
    