#!/usr/bin/env python
# -*- coding: utf-8 -*-
from gui.phase10 import Phase10Widget
from gui.remigio import RemigioWidget
from gui.ratuki import RatukiWidget
from gui.carcassone import CarcassoneWidget

class GameWidgetFactory:
    
    @classmethod
    def createGameWidget(cls,gname,players,parent):
        if gname in ['Phase10','Phase10Master']:
            return Phase10Widget(gname,players,None,parent)
        if gname == 'Remigio':
            return RemigioWidget(gname,players,None,parent)      
        if gname == 'Ratuki':
            return RatukiWidget(gname,players,None,parent)
        if gname == 'Carcassone':
            return CarcassoneWidget(gname,players,None,parent)
        return None
    
    @classmethod
    def resumeGameWidget(cls,gname,engine,parent):
        if gname in ['Phase10','Phase10Master']:
            return Phase10Widget(gname,None,engine,parent)
        if gname == 'Remigio':
            return RemigioWidget(gname,None,engine,parent)
        if gname == 'Ratuki':
            return RatukiWidget(gname,None,engine,parent)
        if gname == 'Carcassone':
            return CarcassoneWidget(gname,None,engine,parent)
        return None