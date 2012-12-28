#!/usr/bin/env python
# -*- coding: utf-8 -*-

import datetime
from model.base import Player
from model.gamefactory import GameFactory
from controllers.db import db


class RoundGameEngine:
    def __init__(self):
        self.match = None
        self.players = dict()
        self.porder = list()
        self.game = None
        
    def addPlayer(self,nick,fullName=""):
        if (fullName == ""):
            fullName = nick
        self.porder.append(nick)
        self.players[nick] = Player()
        self.players[nick].nick = nick
        cur = db.execute("Select * from Player where nick='{}';".format(nick))
        ## Exists in db?
        user = cur.fetchone()

        #user=1

        if (user):
#            print "USER:",user,
            self.players[nick].fullName = user['fullName']
        else:
            self.players[nick].fullName = fullName
            self.players[nick].dateCreation = datetime.datetime.now()
            db.execute("INSERT INTO Player (nick, fullName, dateCreation) values ('"+nick+"','"+fullName+"','"+str(self.players[nick].dateCreation)+"');")

    def begin(self):
        self.match = GameFactory.createMatch(self.game, self.players)    
        self.match.startMatch()

    def addRound(self,r):
        self.match.addRound(r)

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
        cur = db.execute("Select maxPlayers from Game where name='Phase10'")
        r = cur.fetchone()
        return int(r['maxPlayers'])
    
    def cancelMatch(self):
        self.match.cancel()

    def printStats(self):
        print ""
        print "==========================="
        print "| Current Score (round {}) |".format(self.getNumRound())
        print "==========================="
        for n in self.porder:
            p = self.players[n]
            print ""
            print p.nick
            print "Current score: ",self.getScoreFromPlayer(p.nick)
            print "*************************"

        if self.getWinner():
            print ""
            print "!!!!!!!!!!!!!!!!!!!!!!!!!"
            print " Winner:", self.getWinner()
            print "!!!!!!!!!!!!!!!!!!!!!!!!!"


