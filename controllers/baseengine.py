#!/usr/bin/env python
# -*- coding: utf-8 -*-

import datetime
import random
from model.base import Player,GenericRound
from model.gamefactory import GameFactory
from controllers.db import db

class RoundGameEngine:
    
    NoDealer = 0
    RRDealer = 1
    WinnerDealer = 2
    
    def __init__(self):
        self.match = None
        self.players = dict()
        self.porder = list()
        self.game = None
        self.round = None
        self.dealer = None
        self.dealingp = self.NoDealer
        
    def addPlayer(self,nick,fullName=""):
        if (fullName == ""):
            fullName = nick
        self.porder.append(nick)
        self.players[nick] = Player()
        self.players[nick].nick = nick
        cur = db.execute("Select * from Player where nick='{}';".format(nick))
        ## Exists in db?
        user = cur.fetchone()
        if (user):
            self.players[nick].fullName = user['fullName']
        else:
            self.players[nick].fullName = fullName
            self.players[nick].dateCreation = datetime.datetime.now()
            db.execute("INSERT INTO Player (nick, fullName, dateCreation) values ('"+nick+"','"+fullName+"','"+str(self.players[nick].dateCreation)+"');")

    def begin(self):
        self.match = GameFactory.createMatch(self.game, self.players)    
        self.match.startMatch()
        if self.dealingp != self.NoDealer :
            self.dealer = random.choice(self.porder)
        
    def openRound(self):
        self.round = GenericRound()
        
    def setRoundWinner(self,winner):
        self.round.setWinner(winner)
        
    def addRoundInfo(self,player,score, extras=None):
        self.round.addInfo(player,score,extras)

    def commitRound(self):
        self.match.addRound(self.round)
        self.updateDealer()
        
    def getGame(self):
        return self.game

    def getRounds(self):
        return self.match.getRounds()

    def getWinner(self):
        return self.match.getWinner()

    def getPlayers(self):
        return self.players
    
    def getListPlayers(self):
        return self.porder

    def getScoreFromPlayer(self,player):
        if (player in self.match.totalScores):
            return self.match.totalScores[player]
        else:
            return 0

    def getNumRound(self):
        return len(self.match.rounds)+1

    def getGameMaxPlayers(self):
        cur = db.execute("Select maxPlayers from Game where name='{}'".format(self.game))
        r = cur.fetchone()
        return int(r['maxPlayers'])
    
    def cancelMatch(self):
        self.match.cancel()
        
    def setDealingPolicy(self, policy):
        if policy == self.RRDealer or policy == self.WinnerDealer:
            self.dealingp = policy
        
    def getDealingPolicy(self):
        return self.dealingp
    
    def getDealer(self):
        return self.dealer
    
    def updateDealer(self):
        if self.match.getWinner(): return
        if self.dealingp == self.RRDealer:
            self.updateRRDealer()
        elif self.dealingp == self.WinnerDealer:
            self.updateWinnerDealer()

    def updateRRDealer(self):
        candidate = (self.porder.index(self.dealer) + 1)%len(self.porder)
        self.dealer = self.porder[candidate]
        
    def updateWinnerDealer(self):
        self.dealer = self.round.getWinner()

    def printStats(self):
        lastround = self.getNumRound()-1
        if lastround == 0:
            print("===========================")
            print("|{0:^25}|".format(self.game))
            print("===========================")
            print("")
            print("Players:".format(self.porder))
            for n in self.porder:
                if n == self.dealer: print(" * {} (Dealer)".format(n))
                else: print(" * {}".format(n))
            print("")
            policies = ["None","Round Robin","Winner"]
            print("DealingPolicy: {}".format(policies[self.getDealingPolicy()]))
            self.printExtraStats()
            print("***************************")
        else:
            print("")
            print("===========================")
            print("|        Round {0:<3}        |".format(lastround))
            print("===========================")
            print("")
            self.printExtraStats()
            print("***************************")
            for n in self.porder:
                print("")
                if n == self.dealer: print("{} (Dealer)".format(n))
                else: print(n)
                    
                print("Current score: {}".format(self.getScoreFromPlayer(n)))
                self.printExtraPlayerStats(n)
                print("***************************")
                
            if self.getWinner():
                print("")
                print("!!!!!!!!! Winner: !!!!!!!!!")
                print("{0:^27}".format(self.getWinner()))
                print("!!!!!!!!!!!!!!!!!!!!!!!!!!!")
    
    def printExtraStats(self): pass        
    def printExtraPlayerStats(self,player): pass
    
    
#
# Helper functions for cli test
#
    

def readInput(prompt,cast=str,validator=lambda x : True,errormsg="Sorry, invalid answer."):
    validInput = False
    while not validInput:
        try:
            ret = cast(raw_input(prompt))
        except ValueError:
            print(errormsg)
            continue
        if validator(ret):
            validInput = True
        else:
            print(errormsg)
    return ret

def gameStub(engine,roundPlayerFunction):

    print("Welcome to {} Engine Stub".format(engine.getGame()))
    
    db.connectDB("../db/gamelog.db")

    playersOrder = []
    validPlayers = db.getPlayerNicks()
    maxPlayers =  engine.getGameMaxPlayers()
    
    nplayers = readInput("Number of players: ",int,lambda x: x>=2 and x<=maxPlayers,"Sorry, number of players must be between 2 and {}.".format(engine.getGameMaxPlayers()))

    for i in range (1,nplayers+1):
        print ("Player {} Info:".format(i))
        nick = readInput("Nick: ",str,lambda x: x in validPlayers,"Sorry, player not found in DB")
        engine.addPlayer(nick)
        playersOrder.append(nick)

    option = readInput("Dealing policy[0:None/1:RoundRobin/2:Winner]: ",int,lambda x: x in [0,1,2])
    if option == 0: engine.setDealingPolicy(RoundGameEngine.NoDealer)
    elif option == 1: engine.setDealingPolicy(RoundGameEngine.RRDealer)
    elif option == 2: engine.setDealingPolicy(RoundGameEngine.WinnerDealer)
    
    engine.begin()
    engine.printStats()
    nround=1;
    while not engine.getWinner():
        engine.openRound()
        rnd_winner = readInput("Round {} Winner: ".format(nround),str,lambda x: x in playersOrder,"Sorry, player not found in current match.")
        engine.setRoundWinner(rnd_winner)
        for n in playersOrder:
            roundPlayerFunction(engine,n,rnd_winner)
        engine.commitRound()
        engine.printStats()
        nround+=1

    