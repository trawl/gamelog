#!/usr/bin/env python
# -*- coding: utf-8 -*-

from controllers.db import db
from controllers.baseengine import RoundGameEngine
from model.remigio import RemigioRound

class RemigioEngine(RoundGameEngine):
    def __init__(self):
        RoundGameEngine.__init__(self)
        self.game = 'Remigio'
        
    def openRound(self):
        self.round = RemigioRound()

    def getActivePlayers(self):
        return self.match.getActivePlayers()

    def getTop(self):
        return self.match.getTop()
    
    def setTop(self,top):
        self.match.setTop(top)       

    def printExtraPlayerStats(self,player):
        if player not in self.getActivePlayers(): print("   Player Down!")

    def printExtraStats(self):
        print("Match top: {}".format(self.getTop()))

if __name__ == "__main__":
    playersOrder=[]
    print("Welcome to Remigio Engine Stub")
    
    db.connectDB("../db/gamelog.db")

    re = RemigioEngine()
    nplayers = None
    
    validPlayers = db.getPlayerNicks()

    while (not isinstance(nplayers,int) or (isinstance(nplayers,int) and (nplayers < 2 or nplayers > re.getGameMaxPlayers()))):
        try:
            if nplayers is None:
                pass
            elif not isinstance(nplayers,int):
                print("Sorry, number not valid.")
            elif (nplayers < 2 or nplayers > re.getGameMaxPlayers()):
                print("Sorry, number of players must be between 2 and {}.".format(re.getGameMaxPlayers()))

            nplayers = int(raw_input("Number of players: "))
        except ValueError:
            nplayers="ValueError"
            pass

    for i in range (1,nplayers+1):
        print ("Player {} Info:".format(i))
        validInput = False;
        while not validInput:
            nick = raw_input("Nick: ")
            if(nick in validPlayers):
                validInput = True
            else:
                print("Sorry, player not found in DB")
        re.addPlayer(nick)
        playersOrder.append(nick)

    re.begin()
    re.printStats()
    nround=1;
    while not re.getWinner():
        re.openRound()
        rnd_winner  = raw_input("Round {} Winner: ".format(nround))
        while rnd_winner not in playersOrder:
            print("Sorry, player not found in current match.")
            rnd_winner  = raw_input("Round {} Winner: ".format(nround))

        for n in playersOrder:
        #for n,p in re.getPlayers().iteritems():
            p = re.getPlayers()[n]
            iaw = (rnd_winner == n)
            closeType = 1
            validInput = False;
            if iaw:
                while not validInput:
                    try:
                        closeType = int(raw_input("{} close type: ".format(n)))
                    except ValueError:
                        print("Sorry, invalid Close Type number [1,2,3,4].")
                        continue
                    if (closeType in [1,2,3,4]):
                        validInput=True;
                    else:
                        print("Sorry, invalid Close Type number [1,2,3,4].")

            score = 0
            if not iaw:
                validInput = False;
                while not validInput:
                    try:
                        score = int(raw_input("{} round score: ".format(n)))
                    except ValueError:
                        print("Sorry, invalid score number.")
                    if(score>0):
                        validInput = True
                    else:
                        print("Sorry, invalid score number.")
            re.addRoundInfo(n,score,{'closeType':closeType})
        re.commitRound()
        re.printStats()
        nround+=1
    
    
