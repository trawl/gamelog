#!/usr/bin/env python
# -*- coding: utf-8 -*-

from gui.gamestats import QuickStatsBox
from gui.carcassonne import CarcassonneQSBox
from gui.phase10 import Phase10QSBox
from gui.pocha import PochaQSBox

class QSBoxFactory:
    
    @classmethod
    def createQSBox(cls,gname,parent):
        if gname == 'Carcassonne':
            return CarcassonneQSBox(parent)
        if gname in ('Phase10Master','Phase10'): 
            return Phase10QSBox(gname,parent)
        if gname == 'Pocha':
            return PochaQSBox(gname,parent)
        return QuickStatsBox(gname,parent)
    