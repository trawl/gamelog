#!/usr/bin/env python
# -*- coding: utf-8 -*-

from controllers.db import db
from model.base import GenericRoundMatch,GenericRound

class RemigioMatch(GenericRoundMatch):
    def __init__(self,players=dict()):
        GenericRoundMatch.__init__(self,players)
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
            
class RemigioRound(GenericRound):
    def __init__( self):
        GenericRound.__init__(self)
        self.closeType = 1
 
    def addExtraInfo(self,player,extras):
        if (self.score[player] == 0): self.winner = player
        try: self.closeType = extras['closeType']
        except KeyError: pass

