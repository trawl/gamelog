#!/usr/bin/env python
# -*- coding: utf-8 -*-

import datetime

# Model
from controllers.db import db

class Player(object):
    def __init__(self):
        self.nick = ""
        self.fullName = ""
        self.dateCreation = None

class GenericMatch(object):
    
    def __init__(self,players=[]):
        self.game = None
        self.players = players
        self.winner = None
        self.start = None
        self.finish = None
        self.elapsed = 0
        self.totalScores = dict()
        self.idMatch = -1
        self.status = 'cancelled'
        
    def resumeMatch(self,idMatch):
        if self.start is not None: return False
        if not isinstance(idMatch,int): return False
        cur = db.execute("SELECT Game_name,state,elapsed FROM Match WHERE idMatch ={};".format(idMatch))
        row = cur.fetchone()
        if not row: return False
        if row['Game_name']!=self.game or row['state']!=3: return False
        self.elapsed = int(row['elapsed'])
        self.start = datetime.datetime.now()
        #Retrieve players
        self.players = []
        cur = db.execute("SELECT rowid,nick,totalScore FROM MatchPlayer WHERE idMatch ={} ORDER BY rowid;".format(idMatch))
        for row in cur:
            player = str(row['nick'])
            self.players.append(player)
            self.totalScores[player] = int(row['totalScore'])
        
        self.status = 'running'
        self.idMatch = idMatch
        return True

        
    def startMatch(self):
        self.start = datetime.datetime.now()
        cur = db.execute("INSERT INTO Match (Game_name,started) VALUES ('{}','{}');".format(self.game,str(self.start)))
        self.idMatch = cur.lastrowid
        self.status = 'running'
        for p in self.players:
            self.totalScores[p] = 0
            db.execute("INSERT INTO MatchPlayer (idMatch,nick) VALUES ({},'{}');".format(str(self.idMatch),str(p)))
            self.playerStart(p)
            
    def updateWinner(self):
        self.computeWinner()
        if self.winner:
            self.finish = datetime.datetime.now()
            timediff = self.finish - self.start
            self.elapsed += timediff.seconds
            db.execute("UPDATE Match SET finished='{}',state=1,elapsed={} WHERE idMatch={};".format(str(self.finish),self.elapsed,str(self.idMatch)))
            db.execute("UPDATE MatchPlayer SET winner=1 WHERE idMatch={}  and nick='{}';".format(str(self.idMatch),self.winner))
    
    def cancel(self):
        if not self.isCancelled() and not self.winner:
            self.finish = datetime.datetime.now()
            timediff = self.finish - self.start
            self.elapsed += timediff.seconds
            db.execute("UPDATE Match SET finished='{}',state=2, elapsed={} WHERE idMatch={};".format(str(self.finish),self.elapsed,str(self.idMatch)))
            self.status = 'cancelled'
            print("{} Match Cancelled at {}".format(self.game,self.finish))
    
    def getGameTime(self): 
        if self.isPaused() or self.winner:
            elapsed = self.elapsed
        else:
            timediff = datetime.datetime.now() - self.start
            elapsed = self.elapsed + timediff.seconds
            
        hours, remainder = divmod(elapsed, 3600)
        minutes, seconds = divmod(remainder,60)
        return "{0:02}:{1:02}:{2:02}".format(hours,minutes,seconds)
            
    def pause(self):
        if not self.isPaused():
            self.finish = datetime.datetime.now()
            timediff = self.finish - self.start
            self.elapsed += timediff.seconds
            db.execute("UPDATE Match SET finished='{}', elapsed={}, state=3 WHERE idMatch={};".format(str(self.finish),self.elapsed,str(self.idMatch)))
            print("{} Paused at {}".format(self.game, self.finish))
            self.status = 'paused'
            
    def unpause(self):
        if self.isPaused():
            self.start = datetime.datetime.now()
            db.execute("UPDATE Match SET state=0 WHERE idMatch={};".format(str(self.idMatch)))
            print("{} Resumed at {}".format(self.game, self.start))
            self.status = 'running'
            
    def getStartTime(self): return self.start
    
    def getPlayers(self): return self.players
    
    def getWinner(self): return self.winner
            
    def isPaused(self):  return self.status == 'paused'
    
    def isRunning(self): return self.status == 'running'
    
    def isCancelled(self): return self.status == 'cancelled'
    
    # To be implemented in subclasses
    def playerStart(self,player): pass
    
    def computeWinner(self): pass
        
        
class GenericRoundMatch(GenericMatch):
    def __init__(self,players=[]):
        GenericMatch.__init__(self,players)
        self.rounds = list()
        
    def resumeMatch(self,idMatch):
        if not super(GenericRoundMatch,self).resumeMatch(idMatch): return False
        cur = db.execute("SELECT idRound,nick,winner,score FROM Round WHERE idMatch ={} ORDER BY idRound;".format(idMatch))
        current = 0
        rnd = None
        for row in cur:
            if row['idRound'] != current:
                if rnd is not None: self.rounds.append(rnd)
                rnd = self.createRound()
                current += 1
            if row['winner'] == 1: rnd.setWinner(str(row['nick']))
            rnd.addInfo(str(row['nick']), int(row['score']))
        if rnd is not None: self.rounds.append(rnd) 
        return True
    
    
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
    
    def createRound(self): return GenericRound()


class GenericRound(object):
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