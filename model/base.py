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
    
    RUNNING = 0
    FINISHED = 1
    CANCELLED = 2
    PAUSED = 3
    
    def __init__(self,players=[]):
        self.game = None
        self.players = players
        self.winner = None
        self.start = None
        self.resumed = None
        self.finish = None
        self.elapsed = 0
        self.totalScores = dict()
        self.idMatch = -1
        self.state = self.CANCELLED
        
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
        
        self.state = self.RUNNING
        self.idMatch = idMatch
        return True

        
    def startMatch(self):
        self.start = datetime.datetime.now()
        self.resumed = self.start
#        cur = db.execute("INSERT INTO Match (Game_name,started) VALUES ('{}','{}');".format(self.game,str(self.start)))
#        self.idMatch = cur.lastrowid
        self.state = self.RUNNING
        for p in self.players:
            self.totalScores[p] = 0
#            db.execute("INSERT INTO MatchPlayer (idMatch,nick) VALUES ({},'{}');".format(str(self.idMatch),str(p)))
            self.playerStart(p)
            
    def updateWinner(self):
        self.computeWinner()
        if self.winner:
            self.finish = datetime.datetime.now()
            timediff = self.finish - self.start
            self.elapsed += timediff.seconds
            self.flushToDB()
#            db.execute("UPDATE Match SET finished='{}',state=1,elapsed={} WHERE idMatch={};".format(str(self.finish),self.elapsed,str(self.idMatch)))
#            db.execute("UPDATE MatchPlayer SET winner=1 WHERE idMatch={}  and nick='{}';".format(str(self.idMatch),self.winner))
    
    def cancel(self):
        if not self.isCancelled() and not self.winner:
            self.finish = datetime.datetime.now()
            timediff = self.finish - self.start
            self.elapsed += timediff.seconds
#            db.execute("UPDATE Match SET finished='{}',state=2, elapsed={} WHERE idMatch={};".format(str(self.finish),self.elapsed,str(self.idMatch)))
            self.state = self.CANCELLED
            self.flushToDB()
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
#            db.execute("UPDATE Match SET finished='{}', elapsed={}, state=3 WHERE idMatch={};".format(str(self.finish),self.elapsed,str(self.idMatch)))
            print("{} Paused at {}".format(self.game, self.finish))
            self.state = self.PAUSED
            
    def unpause(self):
        if self.isPaused():
            self.start = datetime.datetime.now()
#            db.execute("UPDATE Match SET state=0 WHERE idMatch={};".format(str(self.idMatch)))
            print("{} Resumed at {}".format(self.game, self.start))
            self.state = self.RUNNING
            
    def save(self):
        self.pause()
        self.flushToDB()
        
    def flushToDB(self):
        if self.idMatch < 0:
            cur = db.execute("INSERT INTO Match (Game_name,state,started,finished,elapsed) VALUES ('{}',{},'{}','{}',{});".format(self.game,self.state,str(self.start),str(self.finish),self.elapsed))
            self.idMatch = cur.lastrowid
        else:
            cur = db.execute("INSERT OR REPLACE INTO Match (idMatch,Game_name,state,started,finished,elapsed) VALUES ({},'{}',{},'{}','{}',{});".format(self.idMatch,self.game,self.state,str(self.start),str(self.finish),self.elapsed))
        for p in self.players:
            db.execute("INSERT OR REPLACE INTO MatchPlayer (idMatch,nick,winner) VALUES ({},'{}',{});".format(str(self.idMatch),str(p)),str(p)==self.winner)
            
    def getStartTime(self): return self.start
    
    def getPlayers(self): return self.players
    
    def setPlayers(self, players): self.players = players
    
    def getWinner(self): return self.winner
            
    def isPaused(self):  return self.state == self.PAUSED
    
    def isRunning(self): return self.state == self.RUNNING
    
    def isCancelled(self): return self.state == self.CANCELLED
    
    # To be implemented in subclasses
    def playerStart(self,player): pass
    
    def computeWinner(self): pass
        
        
class GenericRoundMatch(GenericMatch):
    def __init__(self,players=[]):
        GenericMatch.__init__(self,players)
        self.rounds = list()
        self.dealer = None
        self.dealingp = 0
        
    def resumeMatch(self,idMatch):
        if not super(GenericRoundMatch,self).resumeMatch(idMatch): return False
        cur = db.execute("SELECT idRound,nick,winner,score FROM Round WHERE idMatch ={} ORDER BY idRound;".format(idMatch))
        current = 0
        rnd = None
        for row in cur:
            if row['idRound'] != current:
                current += 1
                if rnd is not None: self.rounds.append(rnd)
                rnd = self.createRound(current)
            if row['winner'] == 1: rnd.setWinner(str(row['nick']))
            rnd.addInfo(str(row['nick']), int(row['score']))
        if rnd is not None: self.rounds.append(rnd) 
        
        cur = db.execute("SELECT value FROM MatchExtras WHERE idMatch ={} and key='Dealer';".format(idMatch))
        row = cur.fetchone()
        if row: self.dealer = str(row['value'])

        cur = db.execute("SELECT value FROM MatchExtras WHERE idMatch ={} and key='DealingPolicy';".format(idMatch))
        row = cur.fetchone()
        if row: self.dealingp = int(row['value'])
        
        return True
    
    
    def addRound(self,rnd):
        self.rounds.append(rnd)
        for player,score in rnd.getScore().items():
#            if (rnd.getWinner()==player): winner = 1
#            else: winner=0
            self.totalScores[player]+=score
#            db.execute("INSERT INTO Round (idMatch,nick,idRound,winner,score) VALUES ({},'{}',{},{},{});".format(self.idMatch,str(player),rnd.getNumRound(),winner,score))
#            db.execute("UPDATE MatchPlayer SET totalScore={} WHERE idMatch={} AND nick='{}';".format(self.totalScores[player],self.idMatch,str(player)))
            self.playerAddRound(player,rnd)
        self.updateWinner()
        
    def getRounds(self): return self.rounds

    # To be implemented in subclasses
    def playerAddRound(self,player,rnd): pass
    
    def createRound(self,numround): return GenericRound(numround)
    
    def getDealer(self):
        return self.dealer

    def setDealer(self,player):
        if player not in self.players: return
        self.dealer = player
#        db.execute("INSERT OR REPLACE INTO MatchExtras (idMatch,key,value) VALUES ({},'Dealer','{}');".format(self.idMatch,player))

    def getDealingPolicy(self):
        return self.dealingp
        
    def setDealingPolicy(self,policy):
        if not policy in [0,1,2]: return
        self.dealingp = policy
#        db.execute("INSERT OR REPLACE INTO MatchExtras (idMatch,key,value) VALUES ({},'DealingPolicy','{}');".format(self.idMatch,policy))
        
    def flushToDB(self):
        super(GenericRoundMatch,self).flushToDB()
        
        db.execute("INSERT OR REPLACE INTO MatchExtras (idMatch,key,value) VALUES ({},'Dealer','{}');".format(self.idMatch,self.getDealer()))
        db.execute("INSERT OR REPLACE INTO MatchExtras (idMatch,key,value) VALUES ({},'DealingPolicy','{}');".format(self.idMatch,self.getDealingPolicy()))
        
        for rnd in self.rounds:
            for player,score in rnd.getScore().items():
                winner = rnd.getWinner()==player
                db.execute("INSERT OR REPLACE INTO Round (idMatch,nick,idRound,winner,score) VALUES ({},'{}',{},{},{});".format(self.idMatch,str(player),rnd.getNumRound(),winner,score))
                
    

class GenericRound(object):
    def __init__(self,numround):
        self.numround = numround
        self.score = dict() # nick -> points
        self.winner = None
        
    def getNumRound(self): return self.numround
        
    def setWinner(self,player): self.winner = player
        
    def getWinner(self): return self.winner
    
    def getPlayerScore(self,player):
        try: return self.score[player]
        except KeyError: return -1
        
    def setPlayerScore(self,player,score):
        try:  self.score[player] = score
        except KeyError: pass
        
    def getScore(self): return self.score
    
    def addInfo(self,player,score,extras=None):
        self.score[player] = score
        if extras: self.addExtraInfo(player,extras)
     
    # To be implemented in subclasses    
    def addExtraInfo(self,player,extras): pass