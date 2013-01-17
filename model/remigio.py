#!/usr/bin/env python
# -*- coding: utf-8 -*-

from controllers.db import db
from model.base import GenericRoundMatch,GenericRound

class RemigioMatch(GenericRoundMatch):
    def __init__(self,players=[]):
        GenericRoundMatch.__init__(self,players)
        self.game = 'Remigio'
        self.activeplayers = []
        self.playersoff = []
        self.top = 100
        
    def playerStart(self,player):
        self.activeplayers.append(player)
        
    def addRound(self,rnd):
        closeType = rnd.getCloseType()
        if closeType > 1:
            for player in rnd.getScore().keys():
                rnd.setPlayerScore(player,closeType*rnd.getPlayerScore(player))
        GenericRoundMatch.addRound(self,rnd)
        
    def playerAddRound(self,player,rnd):
        if rnd.winner==player:
            db.execute("INSERT INTO RoundStatistics (idMatch,nick,idRound,key,value) VALUES ({},'{}',{},'closeType','{}');".format(self.idMatch,player,len(self.rounds),rnd.closeType))
            
    def computeWinner(self):
        
        for p in self.activeplayers[:]:
            if self.totalScores[p] >= self.top:
                self.activeplayers.remove(p)
                self.playersoff.append(p)
        
        if len(self.activeplayers) == 1:
            self.winner = self.activeplayers[0]
            
    def resumeMatch(self,idMatch):
        if not super(RemigioMatch,self).resumeMatch(idMatch): 
            return False
     
        for player,score in self.totalScores.items():
            if score < self.top: self.activeplayers.append(player)
            else: self.playersoff.append(player)

        currentr = 0
        currentp = ""
        extras = {}
        cur = db.execute("SELECT idRound,nick,key,value FROM RoundStatistics WHERE idMatch ={} ORDER BY idRound,nick;".format(idMatch))
        for row in cur:
            if row['idRound'] != currentr:
                if len(extras):
                    for player,extra in extras.items(): 
                        self.rounds[currentr-1].addExtraInfo(player,extra)
                extras = {}
                currentp = ""
                currentr += 1
                
            if str(row['nick']) != currentp:
                currentp = str(row['nick'])
                extras['nick'] = {}
            
            if (str(row['key']) == 'closeType'):
                extras['nick'][str(row['key'])] = int(row['value'])
                
        if len(extras):
            for player,extra in extras.items(): 
                self.rounds[currentr-1].addExtraInfo(player,extra)
        return True
    
    def createRound(self): return RemigioRound()
    
    def getActivePlayers(self): return self.activeplayers
    
    def getPlayersOff(self): return self.playersoff
    
    def isPlayerOff(self,player): return player in self.playersoff
    
    def getTop(self): return self.top
    
    def setTop(self,top): self.top = top
            
class RemigioRound(GenericRound):
    def __init__( self):
        GenericRound.__init__(self)
        self.closeType = 1
 
    def addExtraInfo(self,player,extras):
        player = str(player)
        if player == self.getWinner():
            try: 
                self.closeType = extras['closeType']
            except KeyError: pass
    
    def getCloseType(self): return self.closeType