#!/usr/bin/env python
# -*- coding: utf-8 -*-

from controllers.db import db
from model.base import GenericRoundMatch,GenericRound

class RemigioMatch(GenericRoundMatch):
    def __init__(self,players=[]):
        super(RemigioMatch,self).__init__(players)
        self.game = 'Remigio'
        self.activeplayers = []
        self.playersoff = []
        self.top = 100
        
    def playerStart(self,player):
        if self.getScoreFromPlayer(player) < self.top: self.activeplayers.append(player)
        else: self.playersoff.append(player)
        
    def addRound(self,rnd):
        closeType = rnd.getCloseType()
        if closeType > 1:
            for player in rnd.getScore().keys():
                rnd.setPlayerScore(player,closeType*rnd.getPlayerScore(player))
        GenericRoundMatch.addRound(self,rnd)
        
    def computeWinner(self):
        
        for p in self.activeplayers[:]:
            if self.totalScores[p] >= self.top:
                self.activeplayers.remove(p)
                self.playersoff.append(p)
        
        if len(self.activeplayers) == 1:
            self.winner = self.activeplayers[0]
            
    def resumeMatch(self,idMatch):
        if not super(RemigioMatch,self).resumeMatch(idMatch): return False
        
        for player in self.getPlayers(): self.playerStart(player)
                       
        cur = db.execute("SELECT value FROM MatchExtras WHERE idMatch ={} and key='Top';".format(idMatch))
        row = cur.fetchone()
        if row: self.top = int(row['value'])
                
        return True
    
    def resumeExtraInfo(self,player,key,value): 
        extra = {}
        if key == 'closeType': extra[key] = int(value)
        return extra
    
    def createRound(self,numround): return RemigioRound(numround)
    
    def getActivePlayers(self): return self.activeplayers
    
    def getPlayersOff(self): return self.playersoff
    
    def isPlayerOff(self,player): return player in self.playersoff
    
    def getTop(self): return self.top
    
    def setTop(self,top): 
        if top <=0: return
        self.top = top
#        db.execute("INSERT OR REPLACE INTO MatchExtras (idMatch,key,value) VALUES ({},'Top','{}');".format(self.idMatch,top))
        
    def flushToDB(self):
        super(RemigioMatch,self).flushToDB()
        db.execute("INSERT OR REPLACE INTO MatchExtras (idMatch,key,value) VALUES ({},'Top','{}');".format(self.idMatch,self.top))
        for rnd in self.rounds:
            db.execute("INSERT OR REPLACE INTO RoundStatistics (idMatch,nick,idRound,key,value) VALUES ({},'{}',{},'closeType','{}');".format(self.idMatch,rnd.getWinner(),rnd.getNumRound(),rnd.closeType))
            
            
class RemigioRound(GenericRound):
    def __init__( self,numround):
        super(RemigioRound,self).__init__(numround)
        self.closeType = 1
 
    def addExtraInfo(self,player,extras):
        player = str(player)
        if player == self.getWinner():
            try: 
                self.closeType = extras['closeType']
            except KeyError: pass
    
    def getCloseType(self): return self.closeType