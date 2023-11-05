#!/usr/bin/env python
# -*- coding: utf-8 -*-

from controllers.phase10engine import (Phase10Engine, Phase10MasterEngine,
                                       Phase10StatsEngine,
                                       Phase10ParticularStatsEngine)
from controllers.remigioengine import RemigioEngine
from controllers.ratukiengine import RatukiEngine
from controllers.carcassonneengine import (CarcassonneEngine,
                                           CarcassonneStatsEngine,
                                           CarcassonneParticularStatsEngine)
from controllers.pochaengine import (PochaEngine, PochaStatsEngine,
                                     PochaParticularStatsEngine)
from controllers.statsengine import StatsEngine, ParticularStatsEngine
from controllers.skullkingengine import SkullKingEngine


class GameEngineFactory:

    @classmethod
    def createMatch(cls, gname):
        if gname == 'Phase10':
            return Phase10Engine()
        if gname == 'Phase10Master':
            return Phase10MasterEngine()
        if gname == 'Remigio':
            return RemigioEngine()
        if gname == 'Ratuki':
            return RatukiEngine()
        if gname == 'Carcassonne':
            return CarcassonneEngine()
        if gname == 'Pocha':
            return PochaEngine()
        if gname == 'Skull King':
            return SkullKingEngine()

        return None


class StatsEngineFactory:
    @classmethod
    def getStatsEngine(cls, gname):
        if gname == 'Carcassonne':
            return CarcassonneStatsEngine()
        if gname in ('Phase10Master', 'Phase10'):
            return Phase10StatsEngine()
        if gname == 'Pocha':
            return PochaStatsEngine()
        return StatsEngine()

    @classmethod
    def getParticularStatsEngine(cls, gname):
        if gname == 'Carcassonne':
            return CarcassonneParticularStatsEngine()
        if gname in ('Phase10Master', 'Phase10'):
            return Phase10ParticularStatsEngine()
        if gname == 'Pocha':
            return PochaParticularStatsEngine()
        return ParticularStatsEngine()
