#!/usr/bin/env python
# -*- coding: utf-8 -*-

from controllers.db import db
from controllers.baseengine import readInput
from controllers.phase10engine import Phase10Engine,Phase10MasterEngine
from controllers.remigioengine import RemigioEngine

class ResumeEngine():
    
    def __init__(self,game):
        self.game = game
        self.candidates = {}
        cur = db.execute("SELECT idMatch,started,finished,elapsed FROM Match WHERE state=3 and Game_name='{}'".format(self.game))
        for row in cur:
            self.candidates[row['idMatch']] = {}
            self.candidates[row['idMatch']]['started'] = row['started']
            self.candidates[row['idMatch']]['finished'] = row['finished']
            self.candidates[row['idMatch']]['elapsed'] = row['elapsed']
            self.candidates[row['idMatch']]['players'] = []
            
        for idMatch,match in self.candidates.items():
            cur = db.execute("SELECT nick FROM MatchPlayer WHERE idMatch={}".format(idMatch))
            for row in cur:
                match['players'].append(str(row['nick']))

    def getCandidates(self): return self.candidates
    
    def resume(self,idMatch):
        if self.game == 'Phase10':
            engine = Phase10Engine()
        if self.game == 'Phase10Master':
            engine = Phase10MasterEngine()
        if self.game == 'Remigio':
            engine = RemigioEngine()
        
        if engine.resume(idMatch):
            return engine
        else:
            return None
        
        
if __name__ == "__main__":
    if not db.isConnected(): db.connectDB("../db/gamelog.db")
    game = readInput('Game to play (Phase10/Phase10Master/Remigio): ',str,lambda x: x in ['Phase10','Phase10Master','Remigio'])
    re = ResumeEngine(game)
    candidates = re.getCandidates()
    if not len(candidates):
        print("No {} matches to restore found".format(game))
        exit()
    else:
        print("Matches to restore:")
        for idMatch,match in candidates.items():
            print("{}) {} player match started at {}. Time played: {}. Players:{}".format(idMatch,len(match['players']),match['started'],match['elapsed'],match['players']))
        print("")
        idMatch = readInput('idMatch to resume: ',int,lambda x: x in candidates.keys())
        print("Restoring match #{}".format(idMatch))
        engine = re.resume(idMatch)
        if not engine:
            print("Could not restore match #{}".format(idMatch))
            exit()
        else:
            engine.runRoundLoop()
            
            
