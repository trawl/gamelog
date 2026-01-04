#!/usr/bin/env python
# -*- coding: utf-8 -*-

from model.base import GenericRound, GenericRoundMatch


class Toma6Match(GenericRoundMatch):
    def __init__(self, players=[]):
        super(Toma6Match, self).__init__(players)
        self.game = "Toma6"
        self.top = 66

    def computeWinner(self):
        if max(self.totalScores.values()) >= self.top:
            winner = None
            minscore = 100000
            for player, score in self.totalScores.items():
                if score < minscore:
                    winner = player
                    minscore = score

            if winner is not None:
                self.winner = winner

    def createRound(self, numround):
        return Toma6Round(numround)

    def getTop(self):
        return self.top

    def setTop(self, top):
        self.top = top


class Toma6Round(GenericRound):
    pass
