#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import datetime

from controllers.db import db
from model.base import Match,Round

class Phase10Match(Match):
    def __init__(self,players=dict()):
        Match.__init__(self,players=dict())
        self.rounds = list()
        self.totalScores = dict()
        self.phasesCleared = dict() # player -> list of phases cleared
        cur = db.execute("INSERT INTO Match (Game_name,started) VALUES ('Phase10','"+str(self.start)+"')")
        self.idMatch = cur.lastrowid

        for p in players:
            self.totalScores[p] = 0
            self.phasesCleared[p] = list()
            db.execute("INSERT INTO MatchPlayer (idMatch,nick) VALUES ("+str(self.idMatch)+",'"+str(p)+"')")

    def addRound(self,r):

        self.rounds.append(r)
        for p in r.score:
            if (r.winner==p):
                winner = 1
            else:
                winner=0
            self.totalScores[p]+=r.score[p]
            if (r.completedPhase[p]):
                self.phasesCleared[p].append(r.completedPhase[p])
            db.execute("INSERT INTO Round (idMatch,nick,idRound,winner,score) VALUES ("+str(self.idMatch)+",'"+str(p)+"',"+str(len(self.rounds))+","+str(winner)+","+str(r.score[p])+")")
            db.execute("UPDATE MatchPlayer SET totalScore="+str(self.totalScores[p]) + " WHERE idMatch="+str(self.idMatch)+" AND nick='"+p+"'")
            db.execute("INSERT INTO RoundStatistics (idMatch,nick,idRound,key,value) VALUES ("+str(self.idMatch)+",'"+str(p)+"',"+str(len(self.rounds))+",'PhaseCompleted','"+str(r.completedPhase[p])+"')")

        self.updateWinner()


    def updateWinner(self):
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

        if self.winner:
            self.finish = datetime.datetime.now()
            db.execute("UPDATE Match SET finished='"+str(self.finish)+"',state=1 WHERE idMatch="+str(self.idMatch))
            db.execute("UPDATE MatchPlayer SET winner=1 WHERE idMatch="+str(self.idMatch) +" and nick='"+self.winner+"'")


    def getWinner(self):
        return self.winner

    def getRounds(self):
        return self.rounds
    
    def cancel(self):
        if not self.winner:
            self.finish = datetime.datetime.now()
            db.execute("UPDATE Match SET finished='"+str(self.finish)+"',state=2 WHERE idMatch="+str(self.idMatch))
        
            
class Phase10Round(Round):
    def __init__( self):
        self.score = dict() # nick -> points
        self.winner = None
        self.completedPhase = dict() # nick -> Phase idx or 0

    def addRoundInfo(self,player,score,completedPhase,winner):
        self.score[player]=score
        if (winner): self.winner = player
        self.completedPhase[player] = completedPhase
        
        
class Phase10MasterMatch(Phase10Match):

    def __init__(self,players=dict()):
        Match.__init__(self,players=dict())
        self.rounds = list()
        self.totalScores = dict()
        self.phasesCleared = dict() # player -> list of phases cleared
        cur = db.execute("INSERT INTO Match (Game_name,started) VALUES ('Phase10Master','"+str(self.start)+"')")
        self.idMatch = cur.lastrowid

        for p in players:
            self.totalScores[p] = 0
            self.phasesCleared[p] = list()
            db.execute("INSERT INTO MatchPlayer (idMatch,nick) VALUES ("+str(self.idMatch)+",'"+str(p)+"')")

