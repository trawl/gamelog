#!/usr/bin/env python
# -*- coding: utf-8 -*-

from controllers.db import db
from model.base import GenericRoundMatch, GenericEntry


class CarcassonneMatch(GenericRoundMatch):
    def __init__(self, players=[]):
        super(CarcassonneMatch, self).__init__(players)
        self.game = 'Carcassonne'
        cur = db.execute(
            "SELECT value FROM GameExtras "
            "WHERE Game_name = '{}' and key='Kinds';".format(self.game))
        row = cur.fetchone()
        self.entry_kinds = [str(kind) for kind in row['value'].split(',')]
        self.dealingp = 3
        self.updatewinnereveryround = False

    def getEntryKinds(self): return self.entry_kinds

    def resumeExtraInfo(self, player, key, value):
        extra = {}
        if key == 'kind':
            extra[key] = value
        return extra

    def createRound(self, numround): return CarcassonneEntry(numround)

    def addRound(self, rnd):
        self.rounds.append(rnd)
        for player, score in rnd.getScore().items():
            self.totalScores[player] += score
            self.playerAddRound(player, rnd)

    def flushToDB(self):
        super(CarcassonneMatch, self).flushToDB()
        for entry in self.rounds:
            db.execute("INSERT OR REPLACE INTO RoundStatistics "
                       "(idMatch,nick,idRound,key,value) "
                       "VALUES ({},'{}',{},'kind','{}');".format(
                            self.idMatch, entry.getPlayer(),
                            entry.getNumEntry(), entry.getKind()))

    def computeWinner(self):
        maxscore = max(self.totalScores.values())
        candidates = [player for player,
                      score in self.totalScores.items() if score == maxscore]
        if len(candidates) == 1:
            self.winner = candidates.pop()
            return
        # Compute details for candidates
        details = {}
        for kind in self.getEntryKinds():
            details[kind] = {}
            for player in candidates:
                details[kind][player] = 0
        for entry in self.getRounds():
            details[entry.getKind()][entry.getPlayer()
                                     ] += entry.getPlayerScore()

        # Draw
        for kind in self.getEntryKinds():
            maxscore = max(details[kind].values())
            removed = []
            for player, score in details[kind].items():
                if score != maxscore:
                    candidates.remove(player)
                    removed.append(player)

            if len(candidates) == 1:
                self.winner = candidates.pop()
                return

            for k in details.keys():
                for player in removed:
                    del details[k][player]

        # Ultimate draw, pick the first candidate then...
        self.winner = candidates.pop()
        return


class CarcassonneEntry(GenericEntry):
    def __init__(self, numround):
        super(CarcassonneEntry, self).__init__(numround)
        self.kind = None

    def addExtraInfo(self, player, extras):
        try:
            self.kind = extras['kind']
        except KeyError:
            pass

    def getKind(self): return self.kind
