#!/usr/bin/env python
# -*- coding: utf-8 -*-

import datetime
from model.base import Player,GenericRound
from model.gamefactory import GameFactory
from controllers.db import db

class RoundGameEngine:
    def __init__(self):
        self.match = None
        self.players = dict()
        self.porder = list()
        self.game = None
        self.round = None
        
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
        
    def openRound(self):
        self.round = GenericRound()
        
    def addRoundInfo(self,player,score, extras=None):
        self.round.addInfo(player,score,extras)

    def commitRound(self):
        self.match.addRound(self.round)
        
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

    def printStats(self):
        lastround = self.getNumRound()-1
        if lastround == 0:
            print("===========================")
            print("|{0:^25}|".format(self.game))
            print("===========================")
            print("")
            print("Players: {}".format(self.porder))
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
                print(n)
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

    engine.begin()
    engine.printStats()
    nround=1;
    while not engine.getWinner():
        engine.openRound()
        rnd_winner = readInput("Round {} Winner: ".format(nround),str,lambda x: x in playersOrder,"Sorry, player not found in current match.")
        for n in playersOrder:
            roundPlayerFunction(engine,n,rnd_winner)
        engine.commitRound()
        engine.printStats()
        nround+=1

    