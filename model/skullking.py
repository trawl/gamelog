#!/usr/bin/env python
# -*- coding: utf-8 -*-

from model.base import GenericRoundMatch


class SkullKingMatch(GenericRoundMatch):
    def __init__(self, players=[]):
        super(SkullKingMatch, self).__init__(players)
        self.game = 'Skull King'
        self.dealingp = 1
        self.maxRounds = 10

    def resumeMatch(self, idMatch):
        if not super(SkullKingMatch, self).resumeMatch(idMatch):
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
