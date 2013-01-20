#!/usr/bin/env python
# -*- coding: utf-8 -*-
from gui.phase10 import Phase10Widget
from gui.remigio import RemigioWidget

class GameWidgetFactory:
    
    @classmethod
    def createGameWidget(cls,gname,players,parent):
        if gname in ['Phase10','Phase10Master']:
            return Phase10Widget(gname,players,None,parent)
        if gname == 'Remigio':
            return RemigioWidget(gname,players,None,parent)      
        return None
    
    @classmethod
    def resumeGameWidget(cls,gname,engine,parent):
        if gname in ['Phase10','Phase10Master']:
            return Phase10Widget(gname,None,engine,parent)
        if gname == 'Remigio':
            return RemigioWidget(gname,None,engine,parent)      
        return None