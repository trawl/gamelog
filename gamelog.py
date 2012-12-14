#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Python generic imports
import sys
import argparse

# Program imports
from controllers.db import GameLogDB
from model.base import *
from model.phase10 import *
from gui.mainwindow import *

def cli():
    playersOrder=[]
    print "Welcome to Boardlog Stub"

    pe = Phase10Engine()
    nplayers = None

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
        nick = raw_input("Nick: ")
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
        #for n,p in pe.getPlayers().iteritems():
            p = pe.getPlayers()[n]
            iaw = (rnd_winner == n)
            c_phase = -1
            validInput = False;
            if iaw:
                while not validInput:
                    try:
                        c_phase = int(raw_input(n + " completed phase number: "))
                    except ValueError:
                        print "Sorry, invalid phase number."
                        continue
                    if (c_phase > 0 and not pe.hasPhaseCompleted(p,c_phase)):
                        validInput=True;
                    else:
                        print "Sorry, phase already completed."
            else:
                while not validInput:
                    try:
                        c_phase = int(raw_input(n + " completed phase number: "))
                    except ValueError:
                        print "Sorry, invalid phase number."
                        continue
                    if (c_phase >= 0 and not pe.hasPhaseCompleted(p,c_phase)):
                        validInput=True;
                    else:
                        print "Sorry, phase already completed."

            score = 0
            if not iaw:
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


            rnd.addRoundInfo(n,score,c_phase,iaw)
        pe.addRound(rnd)
        pe.printStats()
        nround+=1

def gui():
    app = QtGui.QApplication(sys.argv)
    mw = MainWindow()
    mw.show()
    sys.exit(app.exec_())

if __name__ == "__main__":

    parser = argparse.ArgumentParser(description='Game Log Utility')

    parser.add_argument('-c','--cli', action='store_true')
    parser.add_argument('-g','--gui', action='store_true',default=True)
    parser.add_argument('-d','--dev', action='store_true')

    args = parser.parse_args()

    db = GameLogDB()
    if args.dev:
        db.connectDB("db/gamelog-dev.db")
    else:
        db.connectDB()
    # At this time CLI is the only thing we have
    if (args.gui): gui()
    elif (args.cli): cli()
    #else: parser.print_help()
    else: gui()

    if db: db.disconnectDB()
