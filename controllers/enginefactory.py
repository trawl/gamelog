#!/usr/bin/env python
# -*- coding: utf-8 -*-

from controllers.phase10engine import Phase10Engine,Phase10MasterEngine
from controllers.remigioengine import RemigioEngine
from controllers.ratukiengine import RatukiEngine
from controllers.carcassoneengine import CarcassoneEngine

class GameEngineFactory:
    
    @classmethod
    def createMatch(cls,gname):
        if gname == 'Phase10': return Phase10Engine()
        if gname == 'Phase10Master': return Phase10MasterEngine()
        if gname == 'Remigio': return RemigioEngine()
        if gname == 'Ratuki': return RatukiEngine()
        if gname == 'Carcassone': return CarcassoneEngine()
        
        return None