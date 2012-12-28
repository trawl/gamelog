#!/usr/bin/env python
# -*- coding: utf-8 -*-

from controllers.db import db
from model.base import AbstractRoundMatch,AbstractRound

class RemigioMatch(AbstractRoundMatch):
    def __init__(self,players=dict()):
        AbstractRoundMatch.__init__(self,players)
        self.game = 'Remigio'
        self.activeplayers = []
        self.top = 100
        
    def playerStart(self,player):
        self.activeplayers.append(player)
        
    def playerAddRound(self,player,rnd):
        if rnd.winner==player:
            db.execute("INSERT INTO RoundStatistics (idMatch,nick,idRound,key,value) VALUES ({},'{}',{},'closeType','{}');".format(self.idMatch,player,len(self.rounds),rnd.closeType))
            
    def computeWinner(self):
        
        for p in self.activeplayers[:]:
            if self.totalScores[p] >= self.top:
                self.activeplayers.remove(p)
        
        if len(self.activeplayers) == 1:
            self.winner = self.activeplayers[0]
    
    def getActivePlayers(self):
        return self.activeplayers
    
    def getTop(self):
        return self.top
    
    def setTop(self,top):
        self.top = top
            
class RemigioRound(AbstractRound):
    def __init__( self):
        AbstractRound.__init__(self)
        self.closeType = 1

    def addRoundInfo(self,player,score,closeType=1):
        self.score[player]=score
        if (score == 0): self.winner = player
        self.closeType = closeType
 


