#!/usr/bin/env python
# -*- coding: utf-8 -*-

from controllers.baseengine import RoundGameEngine,readInput


class PochaEngine(RoundGameEngine):
    def __init__(self):
        super(PochaEngine,self).__init__()
        self.game = 'Pocha'
        self.hands = [1,2,3,4,5,6,7,8,8,8,8,7,6,5,4,3,2,1]
        self.directions = ["going up"] * 7 + ['coins','cups','swords','clubs'] + ["going down"] * 7
        
    def runRoundPlayer(self,player,winner):
        score = readInput("{} round score: ".format(player),int,lambda x: True,"Sorry, invalid score number.")
        self.addRoundInfo(player,score)   

    def getHands(self,rnd=None):
        index = self.getNumRound()-1
        if rnd is not None: index = rnd - 1 
        return self.hands[index]
    
    def getDirection(self,rnd=None):
        index = self.getNumRound()-1
        if rnd is not None: index = rnd - 1 
        return self.directions[index]
        
if __name__ == "__main__":
    re = PochaEngine()
    re.gameStub()

    
