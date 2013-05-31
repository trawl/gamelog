#!/usr/bin/env python
# -*- coding: utf-8 -*-


# Model
from model.phase10 import Phase10Match,Phase10MasterMatch
from model.remigio import RemigioMatch
from model.ratuki import RatukiMatch
from model.carcassonne import CarcassonneMatch

class GameFactory:
    
    @classmethod
    def createMatch(cls,gname,players=[]):
        print ("Creating match instance for {}".format(gname))
        if gname == 'Phase10': return Phase10Match(players)
        if gname == 'Phase10Master': return Phase10MasterMatch(players)
        if gname == 'Remigio': return RemigioMatch(players)
        if gname == 'Ratuki': return RatukiMatch(players)
        if gname == 'Carcassonne': return CarcassonneMatch(players)
        
        return None