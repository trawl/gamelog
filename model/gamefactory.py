#!/usr/bin/env python
# -*- coding: utf-8 -*-

from model.base import GenericMatch
from model.carcassonne import CarcassonneMatch
from model.phase10 import Phase10MasterMatch, Phase10Match
from model.pocha import PochaMatch
from model.ratuki import RatukiMatch
from model.remigio import RemigioMatch
from model.skullking import SkullKingMatch
from model.toma6 import Toma6Match


class GameFactory:
    @classmethod
    def createMatch(cls, gname, players=[]):
        print("Creating match instance for {}".format(gname))
        if gname == "Phase10":
            return Phase10Match(players)
        if gname == "Phase10Master":
            return Phase10MasterMatch(players)
        if gname == "Remigio":
            return RemigioMatch(players)
        if gname == "Ratuki":
            return RatukiMatch(players)
        if gname == "Carcassonne":
            return CarcassonneMatch(players)
        if gname == "Pocha":
            return PochaMatch(players)
        if gname == "Skull King":
            return SkullKingMatch(players)
        if gname == "Toma6":
            return Toma6Match(players)

        return GenericMatch(players)
