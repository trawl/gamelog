#!/usr/bin/env python
# -*- coding: utf-8 -*-

import datetime

# Model
from controllers.db import db

class Player:
    def __init__(self):
        self.nick = ""
        self.fullName = ""
        self.dateCreation = None

class GenericMatch:
    def __init__(self,players=dict()):
        self.game = None
        self.players = players
        self.winner = None
        self.start = datetime.datetime.now()
        self.finish = None
        self.totalScores = dict()
        
    def startMatch(self):
        cur = db.execute("INSERT INTO Match (Game_name,started) VALUES ('{}','{}');".format(self.game,str(self.start)))
        self.idMatch = cur.lastrowid
        for p in self.players:
            self.totalScores[p] = 0
            db.execute("INSERT INTO MatchPlayer (idMatch,nick) VALUES ({},'{}');".format(str(self.idMatch),str(p)))
            self.playerStart(p)
            
    def updateWinner(self):
        self.computeWinner()
        if self.winner:
            self.finish = datetime.datetime.now()
            db.execute("UPDATE Match SET finished='{}',state=1 WHERE idMatch={};".format(str(self.finish),str(self.idMatch)))
            db.execute("UPDATE MatchPlayer SET winner=1 WHERE idMatch={}  and nick='{}';".format(str(self.idMatch),self.winner))

    def getWinner(self):
        return self.winner
    
    def cancel(self):
        if not self.winner:
            self.finish = datetime.datetime.now()
            db.execute("UPDATE Match SET finished='{}',state=2 WHERE idMatch={};".format(str(self.finish),str(self.idMatch)))

    # To be implemented in subclasses
    def playerStart(self,player): pass
    def computeWinner(self): pass
        
class GenericRoundMatch(GenericMatch):
    def __init__(self,players=dict()):
        GenericMatch.__init__(self,players)
        self.rounds = list()
    
    def addRound(self,rnd):

        self.rounds.append(rnd)
        for player,score in rnd.getScore().items():
            if (rnd.getWinner()==player): winner = 1
            else: winner=0
            self.totalScores[player]+=score
            db.execute("INSERT INTO Round (idMatch,nick,idRound,winner,score) VALUES ({},'{}',{},{},{});".format(self.idMatch,str(player),len(self.rounds),winner,score))
            db.execute("UPDATE MatchPlayer SET totalScore={} WHERE idMatch={} AND nick='{}';".format(self.totalScores[player],self.idMatch,str(player)))
            self.playerAddRound(player,rnd)
        self.updateWinner()
        
    def getRounds(self): return self.rounds

    # To be implemented in subclasses
    def playerAddRound(self,player,rnd): pass


class GenericRound:
    def __init__(self):
        self.score = dict() # nick -> points
        self.winner = None
        
    def setWinner(self,player):
        self.winner = player
        
    def getWinner(self):
        return self.winner
    
    def getPlayerScore(self,player):
        try: return self.score[player]
        except KeyError: return -1
        
    def setPlayerScore(self,player,score):
        try:  self.score[player] = score
        except KeyError: pass
        
    def getScore(self):
        return self.score
    
    def addInfo(self,player,score,extras=None):
        self.score[player] = score
        if extras: self.addExtraInfo(player,extras)
     
    # To be implemented in subclasses    
    def addExtraInfo(self,player,extras): pass