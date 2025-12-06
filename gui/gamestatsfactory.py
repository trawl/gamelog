#!/usr/bin/env python
# -*- coding: utf-8 -*-
from gui.carcassonne import CarcassonneQSTW
from gui.gamestats import QuickStatsTW
from gui.phase10 import Phase10QSTW
from gui.pocha import PochaQSTW


class QSFactory:
    @classmethod
    def createQS(cls, gname, players, parent):
        if gname == "Carcassonne":
            return CarcassonneQSTW(gname, players, parent)
        if gname in ("Phase10Master", "Phase10"):
            return Phase10QSTW(gname, players, parent)
        if gname == "Pocha":
            return PochaQSTW(gname, players, parent)
        return QuickStatsTW(gname, players, parent)
