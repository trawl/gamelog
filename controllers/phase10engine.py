#!/usr/bin/env python
# -*- coding: utf-8 -*-

from controllers.baseengine import RoundGameEngine,readInput
from controllers.db import db

class Phase10Engine(RoundGameEngine):
    def __init__(self):
        super(Phase10Engine,self).__init__()
        self.game = "Phase10"
                    
    def getPhases(self):
        cur = db.execute("Select key,value from GameExtras where Game_name='{}' and key like 'Phase %' order by key asc".format(self.game))
        return [row['value'] for row in cur ]

    def getRemainingPhasesFromPlayer(self, player):
        remaining = list(range(1,11))
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
    def hasPhaseRemaining(self,player,phase):
        if phase in self.getRemainingPhasesFromPlayer(player):
            return True
        else:
            return False

    def printExtraPlayerStats(self,player):
        print("Phases completed: {}".format(self.getCompletedPhasesFromPlayer(player)))
        
    def printExtraStats(self):
        print("Phases:")
        print("====================")
        for n,phase in enumerate(self.getPhases(),start=1):
            print(u"  Phase {0:02}: {1}".format(n,phase))
        print("====================")
        print("  Quick desc: s=set, r=run, c=colour, cr=colour run")
        print("  Example: 2s4 = 2 sets of 4 cards")
        
    def runStubRoundPlayer(self,player,winner):
        score = 0
        cleared = 1
        if self.getPhasesInOrderFlag():
            try: a_phase = self.getCompletedPhasesFromPlayer(player)[-1] + 1
            except IndexError: a_phase = 1
        else:
            a_phase = readInput("{} aimed phase number: ".format(player),int,lambda x: x > 0 and self.hasPhaseRemaining(player,x),"Sorry, phase not valid or already completed.")
        if not winner == player:
            score = readInput("{} round score: ".format(player),int,lambda x: x>0,"Sorry, invalid score number.")
            if (score>=50):
                cleared = readInput("Did {} complete phase {}?[1/0]: ".format(player,a_phase),int,lambda x: x in [0,1])
        self.addRoundInfo(player,score, {'aimedPhase':a_phase, 'isCompleted':cleared})
        
    def extraStubConfig(self):
        pio = readInput("Follow phases in order? [1/0]: ",int,lambda x: x in (0,1))
        self.setPhasesInOrderFlag(bool(pio))
        
    def getPhasesInOrderFlag(self): return self.match.getPhasesInOrderFlag()
     
    def setPhasesInOrderFlag(self,flag): self.match.setPhasesInOrderFlag(flag)
        

class Phase10MasterEngine(Phase10Engine):
    def __init__(self):
        super(Phase10MasterEngine,self).__init__()
        self.game = "Phase10Master"

if __name__ == "__main__":
    game = readInput('Game to play (Phase10/Phase10Master): ',str,lambda x: x in ['Phase10','Phase10Master'])
    if game == 'Phase10': pe = Phase10Engine()
    else: pe = Phase10MasterEngine()
    pe.gameStub()        
        