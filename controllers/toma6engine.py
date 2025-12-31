#!/usr/bin/env python
# -*- coding: utf-8 -*-

from typing import cast

from controllers.baseengine import readInput
from controllers.remigioengine import RemigioEngine
from model.toma6 import Toma6Match


class Toma6Engine(RemigioEngine):
    def __init__(self):
        if not hasattr(self, "game"):
            self.game = "Toma6"
        super(Toma6Engine, self).__init__()

    def getTop(self):
        return cast("Toma6Match", self.match).getTop()

    def printExtraStats(self):
        print("Match top: {}".format(self.getTop()))

    def runRoundPlayer(self, player, winner=None):
        score = 0
        score = readInput(
            "{} round score: ".format(player),
            int,
            lambda x: x > 0,
            "Sorry, invalid score number.",
        )
        self.addRoundInfo(player, score)


if __name__ == "__main__":
    re = Toma6Engine()
    re.gameStub()
