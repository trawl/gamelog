#!/usr/bin/env python
# -*- coding: utf-8 -*-

from gui.gamestats import QuickStatsBox
from gui.carcassonne import CarcassonneQSBox

class QSBoxFactory:
    
    @classmethod
    def createQSBox(cls,gname,parent):
        if gname == 'Carcassonne':
            return CarcassonneQSBox(parent)
        return QuickStatsBox(gname,parent)
    