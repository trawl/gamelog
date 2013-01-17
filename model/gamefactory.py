#!/usr/bin/env python
# -*- coding: utf-8 -*-


# Model
from model.phase10 import Phase10Match,Phase10MasterMatch
from model.remigio import RemigioMatch

class GameFactory:
    
    @classmethod
    def createMatch(cls,gname,players=[]):
        if gname == 'Phase10':
            return Phase10Match(players)
        if gname == 'Phase10Master':
            return Phase10MasterMatch(players)
        if gname == 'Remigio':
            return RemigioMatch(players)
        
        return None