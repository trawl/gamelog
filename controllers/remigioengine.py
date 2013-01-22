#!/usr/bin/env python
# -*- coding: utf-8 -*-

from controllers.baseengine import RoundGameEngine,readInput

class RemigioEngine(RoundGameEngine):
    def __init__(self):
        RoundGameEngine.__init__(self)
        self.game = 'Remigio'

    def getActivePlayers(self): return self.match.getActivePlayers()
    
    def isPlayerOff(self,player): return self.match.isPlayerOff(player)

    def getTop(self): return self.match.getTop()
    
    def setTop(self,top): self.match.setTop(top)       

    def printExtraPlayerStats(self,player):
        if player not in self.getActivePlayers(): print("   Player Down!")

    def printExtraStats(self): 
        print("Match top: {}".format(self.getTop()))
        
    def updateRRDealer(self):
        candidate = self.porder.index(self.getDealer())
        while True:
            candidate = (candidate + 1)%len(self.porder)
            player = self.porder[candidate]
            if not self.isPlayerOff(player):
                self.match.setDealer(player)
                break
            
    def runStubRoundPlayer(self,player,winner):
        score = 0
        closeType = 1
        if winner == player:
            closeType = readInput("{} close type: ".format(player),int,lambda x: x in [1,2,3,4],"Sorry, invalid Close Type number [1,2,3,4].")
        else:
            score = readInput("{} round score: ".format(player),int,lambda x: x>0,"Sorry, invalid score number.")
        self.addRoundInfo(player,score,{'closeType':closeType})   
        
    def extraStubConfig(self):
        top = readInput("Top score: ",int,lambda x: x > 0)
        self.setTop(top)


if __name__ == "__main__":
    re = RemigioEngine()
    re.gameStub()

    
