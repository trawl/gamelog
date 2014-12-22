#!/usr/bin/env python
# -*- coding: utf-8 -*-

from controllers.baseengine import RoundGameEngine,readInput
from controllers.statsengine import StatsEngine
from controllers.db import db

class PochaEngine(RoundGameEngine):
    def __init__(self):
        super(PochaEngine,self).__init__()
        self.game = 'Pocha'
        self.hands = [1,2,3,4,5,6,7,8,8,8,8,7,6,5,4,3,2,1]
        self.setSuitType()

    def runRoundPlayer(self,player,winner):
        score = readInput("{} round score: ".format(player),int,lambda x: True,"Sorry, invalid score number.")
        self.addRoundInfo(player,score)   

    def getHands(self,rnd=None):
        index = self.getNumRound()-1
        if rnd is not None: index = rnd - 1 
        return self.hands[index]
    
    def getDirection(self,rnd=None):
        index = self.getNumRound()-1
        if rnd is not None: index = rnd - 1 
        return self.directions[index]
    
    def setSuitType(self,st='spanish'):
        self.suitType = st
        if st == 'french':
            self.directions = ["going up"] * 7 + ['diamonds','hearts','pikes','clovers'] + ["going down"] * 7
        else:
            self.directions = ["going up"] * 7 + ['coins','cups','swords','clubs'] + ["going down"] * 7
                
    def getSuitType(self): return self.suitType
    
    
    
class PochaStatsEngine(StatsEngine):
    
    _hitsQuery="""
    SELECT player, max(hits) as "max_hits", min(hits) as "min_hits" from (   
     SELECT Round.idMatch as idm, Round.nick as "player", COUNT(Round.idRound) as "hits"
        FROM Round,Match
        WHERE Match.idMatch = Round.idMatch 
            and Match.state = 1
            and Game_name="Pocha" 
            and Round.score>=10 
        group by idm, player
    ) as tmp
    group by player
    order by player
    """
    
    _extremeRounds="""
     SELECT Round.nick as "player", max(score) as "max_round_score", min(score) as "min_round_score"
        FROM Round,Match
        WHERE Match.idMatch = Round.idMatch 
            and Match.state = 1
            and Game_name="Pocha" 
        group by player
   """
    
    def __init__(self):
        super(PochaStatsEngine, self).__init__()
        self.singleKindRecord=None
        
    def update(self):
        super(PochaStatsEngine, self).update()
        self.hitsRecord = db.queryDict(self._hitsQuery)
        self.extremeRoundsRecord = db.queryDict(self._extremeRounds)
        
        for row in self.hitsRecord:
            player = row['player']
            for r2 in self.generalplayerstats:
                if r2['nick'] == player and r2['game'] == "Pocha":
                    r2['max_hits'] = row['max_hits']
                    r2['min_hits'] = row['min_hits']
                    break
        for row in self.extremeRoundsRecord:
            player = row['player']
            for r2 in self.generalplayerstats:
                if r2['nick'] == player and r2['game'] == "Pocha":
                    r2['max_round_score'] = row['max_round_score']
                    r2['min_round_score'] = row['min_round_score']
                    break
        
if __name__ == "__main__":
    re = PochaEngine()
    re.gameStub()

    
