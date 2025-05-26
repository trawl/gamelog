#!/usr/bin/env python
# -*- coding: utf-8 -*-

from model.pocha import PochaMatch

class SkullKingMatch(PochaMatch):
    def __init__(self, players=[]):
        super(SkullKingMatch, self).__init__(players)
        self.game = 'Skull King'
        self.dealingp = 1
        self.maxRounds = 10