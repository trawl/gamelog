#!/usr/bin/python
# -*- coding: utf-8 -*-

import datetime
from model.phase10 import *
from controllers.db import *

class Phase10Engine:
    def __init__(self):
        self.match = None
        self.players = dict()
        self.porder = list()

    def addPlayer(self,nick,fullName=""):
        if (fullName == ""):
            fullName = nick
        self.porder.append(nick)
        self.players[nick] = Player()
        self.players[nick].nick = nick
        cur = db.execute("Select * from Player where nick='"+nick+"'")
        ## Exists in db?
        user = cur.fetchone()

        #user=1

        if (user):
            print "USER:",user,
            self.players[nick].fullName = user['fullName']
        else:
            self.players[nick].fullName = fullName
            self.players[nick].dateCreation = datetime.datetime.now()
            db.execute("INSERT INTO Player (nick, fullName, dateCreation) values ('"+nick+"','"+fullName+"','"+str(self.players[nick].dateCreation)+"');")

    def begin(self,gname="Phase10"):
        if(gname == "Phase10"):
            self.match = Phase10Match(self.players)
        if(gname == "Phase10Master"):
            self.match = Phase10MasterMatch(self.players)

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

    def getRemainingPhasesFromPlayer(self, player):
        remaining = range (1,11)
        if (player in self.match.phasesCleared):
            for phase in self.match.phasesCleared[player]:
                remaining.remove(phase)
        return remaining


    def getCompletedPhasesFromPlayer(self,player):
        if (player in self.match.phasesCleared):
            return self.match.phasesCleared[player]
        else:
            return list()
    def hasPhaseCompleted(self,player,phase):
        if phase in self.getCompletedPhasesFromPlayer(player):
            return True
        else:
            return False

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
            print "Phases completed:", self.getCompletedPhasesFromPlayer(p.nick)
            print "Current score: ",self.getScoreFromPlayer(p.nick)
            print "*************************"

        if self.getWinner():
            print ""
            print "!!!!!!!!!!!!!!!!!!!!!!!!!"
            print " Winner:", self.getWinner()
            print "!!!!!!!!!!!!!!!!!!!!!!!!!"
