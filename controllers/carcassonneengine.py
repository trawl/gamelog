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
    SELECT value as "record" ,MAX(Round.score) as "points",RoundStatistics.nick 
    FROM Match,RoundStatistics,Round 
    WHERE Match.idMatch = Round.idMatch 
        and Round.idMatch = RoundStatistics.idMatch 
        and Round.idRound = RoundStatistics.idRound 
        and Round.nick = RoundStatistics.nick  
        and Game_name="Carcassonne" 
        and key="kind" 
        and  value in ("City","Road","Field") 
        and Round.score>0 
    group by value 
    order by value
    """
    
    def __init__(self):
        super(CarcassonneStatsEngine, self).__init__()
        self.singleKindRecord=None
        
    def update(self):
        super(CarcassonneStatsEngine, self).update()
        self.singleKindRecord = db.queryDict(self._singleKindRecordQuery)
    
    def getSingleKindRecords(self):
        return self.singleKindRecord
    