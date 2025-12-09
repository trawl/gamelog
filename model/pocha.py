#!/usr/bin/env python
# -*- coding: utf-8 -*-

from model.base import GenericRoundMatch


class PochaMatch(GenericRoundMatch):
    def __init__(self, players=[]):
        super(PochaMatch, self).__init__(players)
        self.game = "Pocha"
        self.dealingp = 1
        self.hands = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 12, 11, 10, 9, 8]
        self.maxRounds = 18

    def resumeMatch(self, idMatch):
        if not super(PochaMatch, self).resumeMatch(idMatch):
            return False

        for player in self.getPlayers():
            self.playerStart(player)

        return True

    def computeWinner(self):
        winner = None
        if len(self.rounds) < self.maxRounds:
            return None
        maxscore = -1000
        for player, score in self.totalScores.items():
            if score >= maxscore:
                winner = player
                maxscore = score

        if winner is not None:
            self.winner = winner

    def getHands(self):
        return self.hands
