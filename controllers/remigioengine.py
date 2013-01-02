#!/usr/bin/env python
# -*- coding: utf-8 -*-

from controllers.baseengine import RoundGameEngine,readInput,gameStub
from model.remigio import RemigioRound

class RemigioEngine(RoundGameEngine):
    def __init__(self):
        RoundGameEngine.__init__(self)
        self.game = 'Remigio'
        
    def openRound(self):
        self.round = RemigioRound()

    def getActivePlayers(self):
        return self.match.getActivePlayers()
    
    def isPlayerOff(self,player):
        return self.match.isPlayerOff(player)

    def getTop(self):
        return self.match.getTop()
    
    def setTop(self,top):
        self.match.setTop(top)       

    def printExtraPlayerStats(self,player):
        if player not in self.getActivePlayers(): print("   Player Down!")

    def printExtraStats(self):
        print("Match top: {}".format(self.getTop()))

if __name__ == "__main__":
    
    re = RemigioEngine()
    def runRound(re,player,winner):
        score = 0
        closeType = 1
        if winner == player:
            closeType = readInput("{} close type: ".format(player),int,lambda x: x in [1,2,3,4],"Sorry, invalid Close Type number [1,2,3,4].")
        else:
            score = readInput("{} round score: ".format(player),int,lambda x: x>0,"Sorry, invalid score number.")
        re.addRoundInfo(player,score,{'closeType':closeType})        

    gameStub(re,runRound)

    
