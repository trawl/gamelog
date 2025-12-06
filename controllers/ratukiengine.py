#!/usr/bin/env python
# -*- coding: utf-8 -*-
from typing import cast

from controllers.baseengine import RoundGameEngine, readInput
from model.ratuki import RatukiMatch


class RatukiEngine(RoundGameEngine):
    def __init__(self):
        super(RatukiEngine, self).__init__()
        self.game = "Ratuki"

    def getTop(self):
        return cast("RatukiMatch", self.match).getTop()

    def setTop(self, top):
        cast("RatukiMatch", self.match).setTop(top)

    def printExtraStats(self):
        print("Match top: {}".format(self.getTop()))

    def extraStubConfig(self):
        top = readInput("Top score: ", int, lambda x: x > 0)
        self.setTop(top)

    def runRoundPlayer(self, player, winner=None):
        score = readInput(
            "{} round score: ".format(player),
            int,
            lambda x: True,
            "Sorry, invalid score number.",
        )
        self.addRoundInfo(player, score)


if __name__ == "__main__":
    re = RatukiEngine()
    re.gameStub()
