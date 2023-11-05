#!/usr/bin/env python
# -*- coding: utf-8 -*-
from gui.phase10 import Phase10Widget
from gui.remigio import RemigioWidget
from gui.ratuki import RatukiWidget
from gui.pocha import PochaWidget
from gui.skullking import SkullKingWidget
from gui.carcassonne import CarcassonneWidget


class GameWidgetFactory:

    @classmethod
    def createGameWidget(cls, gname, players, parent):
        if gname in ['Phase10', 'Phase10Master']:
            return Phase10Widget(gname, players, None, parent)
        if gname == 'Remigio':
            return RemigioWidget(gname, players, None, parent)
        if gname == 'Ratuki':
            return RatukiWidget(gname, players, None, parent)
        if gname == 'Carcassonne':
            return CarcassonneWidget(gname, players, None, parent)
        if gname == 'Pocha':
            return PochaWidget(gname, players, None, parent)
        if gname == 'Skull King':
            return SkullKingWidget(gname, players, None, parent)
        return None

    @classmethod
    def resumeGameWidget(cls, gname, engine, parent):
        if gname in ['Phase10', 'Phase10Master']:
            return Phase10Widget(gname, None, engine, parent)
        if gname == 'Remigio':
            return RemigioWidget(gname, None, engine, parent)
        if gname == 'Ratuki':
            return RatukiWidget(gname, None, engine, parent)
        if gname == 'Carcassonne':
            return CarcassonneWidget(gname, None, engine, parent)
        if gname == 'Pocha':
            return PochaWidget(gname, None, engine, parent)
        if gname == 'Skull King':
            return SkullKingWidget(gname, None, engine, parent)
        return None
