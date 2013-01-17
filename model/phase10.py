#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys

from controllers.db import db
from model.base import GenericRoundMatch,GenericRound

class Phase10Match(GenericRoundMatch):
    def __init__(self,players=[]):
        GenericRoundMatch.__init__(self,players)
        self.game = "Phase10"
        self.phasesCleared = dict() # player -> list of phases cleared
        
    def playerStart(self,player):
        self.phasesCleared[player] = list()
        
    def playerAddRound(self,player,rnd):
        if (rnd.completedPhase[player]):
            self.phasesCleared[player].append(rnd.completedPhase[player])
        db.execute("INSERT INTO RoundStatistics (idMatch,nick,idRound,key,value) VALUES ({},'{}',{},'PhaseAimed','{}');".format(self.idMatch,player,len(self.rounds),rnd.aimedPhase[player]))
        db.execute("INSERT INTO RoundStatistics (idMatch,nick,idRound,key,value) VALUES ({},'{}',{},'PhaseCompleted','{}');".format(self.idMatch,player,len(self.rounds),rnd.completedPhase[player]))            

    def computeWinner(self):
        
        playersIn10 = list();
        for p,pc in self.phasesCleared.iteritems():
            if (len(pc)==10):
                playersIn10.append(p)
        if (playersIn10):
            # Ok, there are some players with all phases completed
            self.winner = None
            wcscores = dict()
            # Let's see their scores, and select the ones with the lowest one
            for p in playersIn10:
                if self.totalScores[p] not in wcscores:
                    wcscores[self.totalScores[p]]=list()
                wcscores[self.totalScores[p]].append(p)

            minScore=sys.maxint
            # Here we have the players with all phases completed and with the lowest score
            # in case of draw, the player with less points in the last round is the winner
            candidates = wcscores[sorted(wcscores)[0]];
            for n in candidates:
                if self.rounds[-1].score[n]<minScore:
                    self.winner = n
                    minScore = self.rounds[-1].score[n]
                    
    def createRound(self): return Phase10Round()
    
    def resumeMatch(self,idMatch):
        if not super(Phase10Match,self).resumeMatch(idMatch): return False
        
        for player in self.players: self.phasesCleared[player]=[]
        
        cur = db.execute("SELECT idRound,nick,key,value FROM RoundStatistics WHERE idMatch ={} ORDER BY idRound,nick,key,value;".format(idMatch))
        
        currentr = 0
        currentp = ""
        extras = {}
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
                extras[currentp] = {}
            
            if (str(row['key']) == 'PhaseAimed'):
                extras[currentp]['aimedPhase'] = int(row['value'])
            if (str(row['key']) == 'PhaseCompleted'):
                value = int(row['value'])
                if value>0: 
                    extras[currentp]['isCompleted'] = True
                    self.phasesCleared[currentp].append(value)
                else: extras[currentp]['isCompleted'] = False
                
        if len(extras):
            for player,extra in extras.items(): 
                self.rounds[currentr-1].addExtraInfo(player,extra)
        return True
        
            
class Phase10Round(GenericRound):
    
    def __init__( self):
        GenericRound.__init__(self)
        self.completedPhase = dict() # nick -> Phase idx or 0
        self.aimedPhase = dict()

    def addExtraInfo(self,player,extras):
        try:
            self.aimedPhase[player] = extras['aimedPhase']
            if extras['isCompleted']:
                self.completedPhase[player] = extras['aimedPhase']
            else:
                self.completedPhase[player] = 0
        except KeyError: pass
 
        
        
class Phase10MasterMatch(Phase10Match):

    def __init__(self,players=[]):
        Phase10Match.__init__(self,players)
        self.game = 'Phase10Master'

