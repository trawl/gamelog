#!/usr/bin/env python
# -*- coding: utf-8 -*-

from controllers.baseengine import RoundGameEngine

class Phase10Engine(RoundGameEngine):
    def __init__(self):
        RoundGameEngine.__init__(self)
        self.game = "Phase10"

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

class Phase10MasterEngine(Phase10Engine):
    def __init__(self):
        Phase10Engine.__init__(self)
        self.game = "Phase10Master"
        
        
if __name__ == "__main__":
    from model.phase10 import Phase10Round
    from controllers.db import GameLogDB,db
    playersOrder=[]
    print "Welcome to Phase10 Engine Stub"
    
    db = GameLogDB()
    db.connectDB("../db/gamelog.db")
    
    validInput = False;
    while not validInput:
        game = raw_input("Game to play (Phase10/Phase10Master): ")
        if game in ['Phase10','Phase10Master']:
            validInput = True
        else:
            print "Sorry, game not valid."

    if game == 'Phase10': pe = Phase10Engine()
    else: pe = Phase10MasterEngine()
        
    nplayers = None
    validPlayers = db.getPlayerNicks()

    while (not isinstance(nplayers,int) or (isinstance(nplayers,int) and (nplayers < 2 or nplayers > pe.getGameMaxPlayers()))):
        try:
            if nplayers is None:
                pass
            elif not isinstance(nplayers,int):
                print "Sorry, number not valid."
            elif (nplayers < 2 or nplayers > pe.getGameMaxPlayers()):
                print "Sorry, number of players must be between 2 and",str(pe.getGameMaxPlayers())+"."

            nplayers = int(raw_input("Number of players: "))
        except ValueError:
            nplayers="ValueError"
            pass

    for i in range (1,nplayers+1):
        print "Player",i,"Info:"
        validInput = False;
        while not validInput:
            nick = raw_input("Nick: ")
            if(nick in validPlayers):
                validInput = True
            else:
                print "Sorry, player not found in DB"
        pe.addPlayer(nick)
        playersOrder.append(nick)

    pe.begin()
    pe.printStats()
    nround=1;
    while not pe.getWinner():
        rnd = Phase10Round()
        rnd_winner  = raw_input("Round " + str(nround) +" Winner: ")
        while rnd_winner not in playersOrder:
            print"Sorry, player not found in current match."
            rnd_winner  = raw_input("Round " + str(nround) +" Winner: ")

        for n in playersOrder:
            p = pe.getPlayers()[n]
            iaw = (rnd_winner == n)
            score = 0
            c_phase = -1
            a_phase = -1
            cleared = 1
            validInput = False;
            while not validInput:
                try:
                    a_phase = int(raw_input(n + " aimed phase number: "))
                except ValueError:
                    print "Sorry, invalid phase number."
                    continue
                if (a_phase > 0 and pe.hasPhaseRemaining(n,a_phase)):
                    validInput=True;
                else:
                    print "Sorry, phase not valid or already completed."
            
            if not iaw:
                validInput = False;
                while not validInput:
                    try:
                        cleared = int(raw_input(n + " completed phase "+ str(a_phase) +"?{1/0]: "))
                    except ValueError:
                        print "Sorry, invalid answer"
                        continue
                    if (cleared in [1,0]):
                        validInput=True;
                    else:
                        print "Sorry, invalid answer."
                
                validInput = False;
                while not validInput:
                    try:
                        score = int(raw_input(n + " round score: "))
                    except ValueError:
                        print "Sorry, invalid phase number."
                    if(score>0 and score%5==0):
                        validInput = True
                    else:
                        print "Sorry, invalid score number."


            if cleared: c_phase = a_phase
            else: c_phase = 0
            print("Adding round info {} {} {} {}".format(n,score,a_phase,c_phase))
            rnd.addRoundInfo(n,score,a_phase,c_phase)
            
        pe.addRound(rnd)
        pe.printStats()
        nround+=1
    
    
