#!/usr/bin/env python
# -*- coding: utf-8 -*-

from controllers.db import db
from model.base import GenericEntryMatch,GenericEntry

class CarcassonneMatch(GenericEntryMatch):
    def __init__(self,players=[]):
        super(CarcassonneMatch,self).__init__(players)
        self.game = 'Carcassonne'
        cur = db.execute("SELECT value FROM GameExtras WHERE Game_name = '{}' and key='Kinds';".format(self.game))
        row = cur.fetchone()
        self.entry_kinds = [ str(kind) for kind in row['value'].split(',') ]
        self.dealingp = 3
    
    def getEntryKinds(self): return self.entry_kinds    
    
    def resumeExtraInfo(self,player,key,value): 
        extra = {}
        if key == 'kind': extra[key] = value
        return extra
    
    def createEntry(self,numround): return CarcassonneEntry(numround)
        
    def flushToDB(self):
        super(CarcassonneMatch,self).flushToDB()
        for entry in self.entries:
            db.execute("INSERT OR REPLACE INTO RoundStatistics (idMatch,nick,idRound,key,value) VALUES ({},'{}',{},'kind','{}');".format(self.idMatch,entry.getPlayer(),entry.getNumEntry(),entry.getKind()))
    
    def computeWinner(self):
        maxscore = max(self.totalScores.values())
        candidates = [ player for player,score in self.totalScores.items() if score == maxscore ]
        if len(candidates)==1:
            self.winner = candidates.pop()
            return
        # Compute details for candidates
        details = {}
        for kind in self.getEntryKinds():
            details[kind] = {}
            for player in candidates:
                details[kind][player] = 0
        for entry in self.getEntries():
            details[entry.getKind()][entry.getPlayer()] += entry.getScore()
                
        # Check who has more points in cities
        maxscore = max(details['City'].values())
        removed = []
        for player,score in details['City'].items():
            if score != maxscore: 
                candidates.remove(player)
                removed.append(player)
            
        if len(candidates)==1:
            self.winner = candidates.pop()
            return    
        
        for kind in details.keys():
            for player in removed:
                del details[kind][player]
        
        # Check who has more points in Roads
        maxscore = max(details['Road'].values())
        removed = []
        for player,score in details['Road'].items():
            if score != maxscore: 
                candidates.remove(player)
                removed.append(player)
            
        if len(candidates)==1:
            self.winner = candidates.pop()
            return    
        
        for kind in details.keys():
            for player in removed:
                del details[kind][player]
                
        # Check who has more points in Cloisters
        maxscore = max(details['Cloister'].values())
        removed = []
        for player,score in details['Cloister'].items():
            if score != maxscore: 
                candidates.remove(player)
                removed.append(player)
            
        if len(candidates)==1:
            self.winner = candidates.pop()
            return    
        
        for kind in details.keys():
            for player in removed:
                del details[kind][player]
                
        # Check who has more points in Fields
        maxscore = max(details['Field'].values())
        removed = []
        for player,score in details['Field'].items():
            if score != maxscore: 
                candidates.remove(player)
                removed.append(player)
            
        #Choose the first one (bad luck for the second...)
        self.winner = candidates.pop()
        return    

            
            
class CarcassonneEntry(GenericEntry):
    def __init__( self,numround):
        super(CarcassonneEntry,self).__init__(numround)
        self.kind = None
 
    def addExtraInfo(self,player,extras):
        try: self.kind = extras['kind']
        except KeyError: pass
    
    def getKind(self): return self.kind