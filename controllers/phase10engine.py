#!/usr/bin/env python
# -*- coding: utf-8 -*-

from controllers.baseengine import RoundGameEngine,gameStub,readInput
from model.phase10 import Phase10Round
from controllers.db import db

class Phase10Engine(RoundGameEngine):
    def __init__(self):
        RoundGameEngine.__init__(self)
        self.game = "Phase10"
        
    def openRound(self):
        self.round = Phase10Round()
                    
    def getPhases(self):
        # Empty phase (0)
        phases = {'key':[""],'desc':[""]}
        cur = db.execute("Select key,value from GameExtras where Game_name='{}' and key like'Phase %'".format(self.game))
        for row in cur:
            phases["key"].append(row['key'])
            phases["desc"].append(row['value'])
        return phases

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
    def hasPhaseRemaining(self,player,phase):
        if phase in self.getRemainingPhasesFromPlayer(player):
            return True
        else:
            return False

    def printExtraPlayerStats(self,player):
        print("Phases completed: {}".format(self.getCompletedPhasesFromPlayer(player)))


class Phase10MasterEngine(Phase10Engine):
    def __init__(self):
        Phase10Engine.__init__(self)
        self.game = "Phase10Master"

if __name__ == "__main__":
    def runRound(pe,player,winner):
        score = 0
        cleared = 1
        a_phase = readInput("{} aimed phase number: ".format(player),int,lambda x: x > 0 and pe.hasPhaseRemaining(player,x),"Sorry, phase not valid or already completed.")
        if not winner == player:
            cleared = readInput("Did {} complete phase {}?[1/0]: ".format(player,a_phase),int,lambda x: x in [0,1])
            score = readInput("{} round score: ".format(player),int,lambda x: x>0,"Sorry, invalid score number.")
        pe.addRoundInfo(player,score, {'aimedPhase':a_phase, 'isCompleted':cleared})
        
    game = readInput('Game to play (Phase10/Phase10Master): ',str,lambda x: x in ['Phase10','Phase10Master'])
    if game == 'Phase10': pe = Phase10Engine()
    else: pe = Phase10MasterEngine()
    gameStub(pe,runRound)        
        