#!/usr/bin/env python
# -*- coding: utf-8 -*-

from controllers.baseengine import EntryGameEngine,readInput

class CarcassoneEngine(EntryGameEngine):
    def __init__(self):
        EntryGameEngine.__init__(self)
        self.game = 'Carcassone'
            
    def runStubEntryPlayer(self,player):
        score = readInput("{} score: ".format(player),int,lambda x: x>0,"Sorry, invalid score number.")
        kind = readInput("Kind: ",str,lambda x: x in self.match.getEntryKinds(),"Sorry, invalid kind [{}]".format(",".join(self.match.getEntryKinds())))
        self.addEntry(player,score,{'kind':kind})   
        
    def getEntryKinds(self): return self.match.getEntryKinds()


if __name__ == "__main__":
    re = CarcassoneEngine()
    re.gameStub()

    
