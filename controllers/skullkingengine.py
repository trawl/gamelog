#!/usr/bin/env python
# -*- coding: utf-8 -*-

from controllers.pochaengine import PochaEngine, PochaStatsEngine, PochaParticularStatsEngine


class SkullKingEngine(PochaEngine):
    def __init__(self):
        super(SkullKingEngine, self).__init__()
        self.game = 'Skull King'
        self.hands = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]


class SkullKingStatsEngine(PochaStatsEngine):
    def __init__(self):
        super(SkullKingStatsEngine, self).__init__()
        self.game = "Skull King"
        self.define_queries()


class SkullKingParticularStatsEngine(PochaParticularStatsEngine):
    pass


if __name__ == "__main__":
    re = SkullKingEngine()
    re.gameStub()
