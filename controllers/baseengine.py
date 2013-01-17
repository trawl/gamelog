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
        self.match = GameFactory.createMatch(self.game, self.porder)    
        self.match.startMatch()
        if self.dealingp != self.NoDealer :
            self.dealer = random.choice(self.porder)
            
    def resume(self,idMatch):
        self.match = GameFactory.createMatch(self.game)    
        if self.match.resumeMatch(idMatch):
            for nick in self.match.getPlayers(): 
                self.addPlayer(nick)
            return True
        return False
        
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
    
    def pause(self): self.match.pause()
    
    def unpause(self): self.match.unpause()
    
    def isPaused(self): return self.match.isPaused()
    
    def cancelMatch(self): self.match.cancel()
        
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
            print("Players:")
            for n in self.porder:
                if n == self.dealer: print(" * {} (Dealer)".format(n))
                else: print(" * {}".format(n))
            print("")
            policies = ["None","Round Robin","Winner"]
            print("DealingPolicy: {}".format(policies[self.getDealingPolicy()]))
            self.printExtraStats()
            print("Game started at {}".format(self.match.getStartTime()))
            print("***************************")
        else:
            print("")
            print("===========================")
            print("|        Round {0:<3}        |".format(lastround))
            print("===========================")
            print("")
            print("Time played: {}".format(self.match.getGameTime()))
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
                print("")
                print("{} match finished at {}".format(self.game,datetime.datetime.now()))
                print("Time played {}".format(self.match.getGameTime()))                   
                print("")
#
# Helper functions for cli test
#
    def gameStub(self):
    
        print("Welcome to {} Engine Stub".format(self.getGame()))
        
        if not db.isConnected(): db.connectDB("../db/gamelog.db")
    
        playersOrder = []
        validPlayers = db.getPlayerNicks()
        maxPlayers =  self.getGameMaxPlayers()
        
        nplayers = readInput("Number of players: ",int,lambda x: x>=2 and x<=maxPlayers,"Sorry, number of players must be between 2 and {}.".format(self.getGameMaxPlayers()))
    
        for i in range (1,nplayers+1):
            print ("Player {} Info:".format(i))
            nick = readInput("Nick: ",str,lambda x: x in validPlayers,"Sorry, player not found in DB")
            self.addPlayer(nick)
            playersOrder.append(nick)
    
        option = readInput("Dealing policy[0:None/1:RoundRobin/2:Winner]: ",int,lambda x: x in [0,1,2])
        if option == 0: self.setDealingPolicy(RoundGameEngine.NoDealer)
        elif option == 1: self.setDealingPolicy(RoundGameEngine.RRDealer)
        elif option == 2: self.setDealingPolicy(RoundGameEngine.WinnerDealer)
        
        self.begin()
        self.runRoundLoop()

    def runRoundLoop(self):
        self.printStats()
        while not self.getWinner():
            self.openRound()
            while True:
                rnd_winner = readInput("Round {} Winner (or p to pause): ".format(self.getNumRound()),str,lambda x: x in self.getListPlayers() or x =='p',"Sorry, player not found in current match.")
                if rnd_winner == 'p':
                    self.pause()
                    readInput("Press Enter to unpause...")
                    self.unpause()
                else: break
                
            self.setRoundWinner(rnd_winner)
            for n in self.getListPlayers():
                self.runRoundPlayer(n,rnd_winner)
            self.commitRound()
            self.printStats()
            
    # To be implemented in subclasses
    def printExtraStats(self): pass        
    def printExtraPlayerStats(self,player): pass
    def runRoundPlayer(self,player,winner): pass



    
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



    