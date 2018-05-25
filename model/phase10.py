#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
from controllers.db import db
from model.base import GenericRoundMatch, GenericRound


class Phase10Match(GenericRoundMatch):

    def __init__(self, players=[]):
        super(Phase10Match, self).__init__(players)
        self.game = "Phase10"
        self.phasesinorder = True
        self.phasesCleared = dict()  # player -> list of phases cleared

    def playerStart(self, player):   self.phasesCleared[player] = list()

    def playerAddRound(self, player, rnd):
        if (rnd.completedPhase[player]):
            self.phasesCleared[player].append(rnd.completedPhase[player])

    def deleteRound(self, nrnd):
        try:
            rnd = self.rounds[nrnd-1]
        except KeyError:
            return
        for player in self.getPlayers():
            if (rnd.completedPhase[player]):
                self.phasesCleared[player].remove(rnd.completedPhase[player])
        super(Phase10Match, self).deleteRound(nrnd)

    def computeWinner(self):

        playersIn10 = list()
        for p, pc in self.phasesCleared.items():
            if (len(pc) == 10):
                playersIn10.append(p)
        if (playersIn10):
            # Ok, there are some players with all phases completed
            self.winner = None
            wcscores = dict()
            # Let's see their scores, and select the ones with the lowest one
            for p in playersIn10:
                if self.totalScores[p] not in wcscores:
                    wcscores[self.totalScores[p]] = list()
                wcscores[self.totalScores[p]].append(p)

#             try:
#                 minScore=sys.maxint
#             except AttributeError:
            minScore = sys.maxsize
            # Here we have the players with all phases completed and with the
            # lowest score in case of draw, the player with less points in the
            # last round is the winner
            candidates = wcscores[sorted(wcscores)[0]]
            for n in candidates:
                if self.rounds[-1].score[n] < minScore:
                    self.winner = n
                    minScore = self.rounds[-1].score[n]

    def createRound(self, numround): return Phase10Round(numround)

    def resumeMatch(self, idMatch):
        if not super(Phase10Match, self).resumeMatch(idMatch):
            return False

        cur = db.execute(
            "SELECT value FROM MatchExtras "
            "WHERE idMatch ={} and key='PhasesInOrder';".format(idMatch))
        row = cur.fetchone()
        if row:
            self.phasesinorder = bool(int(row['value']))

        for player in self.getPlayers():
            if player not in self.phasesCleared:
                self.phasesCleared[player] = []

        return True

    def resumeExtraInfo(self, player, key, value):
        if player not in self.phasesCleared:
            self.phasesCleared[player] = []
        extra = {}
        if (key == 'PhaseAimed'):
            extra['aimedPhase'] = int(value)
        if (key == 'PhaseCompleted'):
            value = int(value)
            if value > 0:
                extra['isCompleted'] = True
                self.phasesCleared[player].append(value)
            else:
                extra['isCompleted'] = False
        return extra

    def flushToDB(self):
        super(Phase10Match, self).flushToDB()
        if self.phasesinorder:
            inorderflag = 1
        else:
            inorderflag = 0
        db.execute("INSERT OR REPLACE INTO MatchExtras (idMatch,key,value) "
                   "VALUES ({},'PhasesInOrder','{}');".format(
                        self.idMatch, inorderflag))
        for rnd in self.rounds:
            for player in rnd.score.keys():
                db.execute("INSERT OR REPLACE INTO RoundStatistics "
                           "(idMatch,nick,idRound,key,value) "
                           "VALUES ({},'{}',{},'PhaseAimed','{}');".format(
                                self.idMatch, player, rnd.getNumRound(),
                                rnd.aimedPhase[player]))
                db.execute("INSERT OR REPLACE INTO RoundStatistics "
                           "(idMatch,nick,idRound,key,value) "
                           "VALUES ({},'{}',{},'PhaseCompleted','{}');".format(
                                self.idMatch, player, rnd.getNumRound(),
                                rnd.completedPhase[player]))

    def getPhasesInOrderFlag(self): return self.phasesinorder

    def setPhasesInOrderFlag(self, flag):
        if flag not in [True, False]:
            return
        print("Setting phases in order flag to {}".format(flag))
        self.phasesinorder = flag


class Phase10Round(GenericRound):

    def __init__(self, numround):
        GenericRound.__init__(self, numround)
        self.completedPhase = dict()  # nick -> Phase idx or 0
        self.aimedPhase = dict()

    def addExtraInfo(self, player, extras):
        try:
            self.aimedPhase[player] = extras['aimedPhase']
            if extras['isCompleted']:
                self.completedPhase[player] = extras['aimedPhase']
            else:
                self.completedPhase[player] = 0
        except KeyError:
            pass

    def getPlayerAimedPhase(self, player):
        try:
            return self.aimedPhase[player]
        except KeyError:
            return 0

    def getPlayerCompletedPhase(self, player):
        try:
            return self.completedPhase[player]
        except KeyError:
            return 0


class Phase10MasterMatch(Phase10Match):

    def __init__(self, players=[]):
        super(Phase10MasterMatch, self).__init__(players)
        self.game = 'Phase10Master'
