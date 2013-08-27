#!/usr/bin/env python
# -*- coding: utf-8 -*-

from controllers.baseengine import EntryGameEngine,readInput
from controllers.statsengine import StatsEngine
from controllers.db import db

class CarcassonneEngine(EntryGameEngine):
    def __init__(self):
        EntryGameEngine.__init__(self)
        self.game = 'Carcassonne'
            
    def runStubEntryPlayer(self,player):
        score = readInput("{} score: ".format(player),int,lambda x: x>0,"Sorry, invalid score number.")
        kind = readInput("Kind: ",str,lambda x: x in self.match.getEntryKinds(),"Sorry, invalid kind [{}]".format(",".join(self.match.getEntryKinds())))
        self.addEntry(player,score,{'kind':kind})   
        
    def getEntryKinds(self): return self.match.getEntryKinds()


if __name__ == "__main__":
    re = CarcassonneEngine()
    re.gameStub()

    
class CarcassonneStatsEngine(StatsEngine):
    
    _singleKindRecordQuery="""
    SELECT value as "record" ,Round.score as "points",RoundStatistics.nick, DATE(Match.finished) as date
    FROM Match,Round,RoundStatistics
    WHERE Match.idMatch = Round.idMatch 
        and Round.idMatch = RoundStatistics.idMatch 
        and Round.idRound = RoundStatistics.idRound 
        and Round.nick = RoundStatistics.nick  
        and Game_name="Carcassonne" 
        and key="kind" 
        and value = '{}' 
        and Round.score>0 
    order by points desc
    limit 1
    """
    
    def __init__(self):
        super(CarcassonneStatsEngine, self).__init__()
        self.singleKindRecord=None
        
    def update(self):
        super(CarcassonneStatsEngine, self).update()
        self.singleKindRecord = []
        for kind in ("City","Road","Field"):
            self.singleKindRecord += db.queryDict(self._singleKindRecordQuery.format(kind))
    
    def getSingleKindRecords(self):
        return self.singleKindRecord
    