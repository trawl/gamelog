#!/usr/bin/env python
# -*- coding: utf-8 -*-

import datetime
from controllers.db import db


class Player(object):
    def __init__(self):
        self.nick = ""
        self.fullName = ""
        self.dateCreation = None


class GenericMatch(object):

    RUNNING = 0
    FINISHED = 1
    CANCELLED = 2
    PAUSED = 3
    SAVED = 4

    def __init__(self, players=[]):
        self.game = None
        self.players = players
        self.winner = None
        self.start = None
        self.resumed = None
        self.finish = None
        self.elapsed = 0
        self.totalScores = dict()
        self.idMatch = -1
        self.state = self.CANCELLED
        self.dealer = None
        self.dealingp = 0

    def resumeMatch(self, idMatch):
        if self.start is not None:
            return False
        if not isinstance(idMatch, int):
            return False
        cur = db.execute(
            "SELECT Game_name,state,started,elapsed "
            "FROM Match WHERE idMatch ={};".format(idMatch))
        row = cur.fetchone()
        if not row:
            return False
        if row['Game_name'] != self.game or row['state'] != self.SAVED:
            return False
        self.elapsed = int(row['elapsed'])
        self.start = datetime.datetime.strptime(
            row['started'], "%Y-%m-%d %H:%M:%S.%f")
        self.resumed = datetime.datetime.now()
        # Retrieve players
        self.players = []
        cur = db.execute(
            "SELECT rowid,nick,totalScore FROM MatchPlayer "
            "WHERE idMatch ={} ORDER BY rowid;".format(idMatch))
        for row in cur:
            player = str(row['nick'])
            self.players.append(player)
            self.totalScores[player] = int(row['totalScore'])

        self.state = self.RUNNING
        self.idMatch = idMatch
        return True

    def startMatch(self):
        self.start = datetime.datetime.now()
        self.resumed = self.start
        self.state = self.RUNNING
        for p in self.players:
            self.totalScores[p] = 0
            self.playerStart(p)

    def flushState(self, state):
        self.updateElapsed()
        self.state = state
        self.flushToDB()

    def updateElapsed(self):
        self.finish = datetime.datetime.now()
        timediff = self.finish - self.resumed
        self.elapsed += timediff.seconds

    def updateWinner(self):
        self.computeWinner()
        if self.winner:
            self.flushState(self.FINISHED)

    def getDealer(self): return self.dealer

    def setDealer(self, player):
        if player not in self.players:
            return
        self.dealer = player

    def getDealingPolicy(self): return self.dealingp

    def setDealingPolicy(self, policy):
        if policy not in [0, 1, 2, 3]:
            return
        self.dealingp = policy

    def cancel(self):
        if not self.isCancelled() and not self.winner:
            self.flushState(self.CANCELLED)
            print("{} Match Cancelled at {}".format(self.game, self.finish))

    def save(self):
        self.flushState(self.SAVED)
        print("{} Saved at {}".format(self.game, self.finish))

    def pause(self):
        if not self.isPaused():
            self.updateElapsed()
            self.state = self.PAUSED
            print("{} Paused at {}".format(self.game, self.finish))

    def unpause(self):
        if self.isPaused():
            self.resumed = datetime.datetime.now()
            self.state = self.RUNNING
            print("{} Resumed at {}".format(self.game, self.resumed))

    def flushToDB(self):
        if self.idMatch < 0:
            cur = db.execute("INSERT INTO Match (Game_name, state, started,"
                             "finished,elapsed) "
                             "VALUES ('{}',{},'{}','{}',{});".format(
                                self.game, self.state, str(self.start),
                                str(self.finish), self.elapsed))
            self.idMatch = cur.lastrowid
        else:
            cur = db.execute("INSERT OR REPLACE INTO Match (idMatch,Game_name,"
                             "state,started,finished,elapsed) "
                             "VALUES ({},'{}',{},'{}','{}',{});".format(
                                self.idMatch, self.game, self.state,
                                str(self.start), str(self.finish),
                                self.elapsed))
        for p in self.players:
            winner = 0
            if str(p) == self.getWinner():
                winner = 1
            db.execute("INSERT OR REPLACE INTO MatchPlayer"
                       "(idMatch,nick,totalScore,winner) "
                       "VALUES ({},'{}',{},{});".format(
                            str(self.idMatch), str(p),
                            self.getScoreFromPlayer(str(p)), winner))

    def getGameTime(self):
        hours, remainder = divmod(self.getGameSeconds(), 3600)
        minutes, seconds = divmod(remainder, 60)
        return "{0:02}:{1:02}:{2:02}".format(hours, minutes, seconds)

    def getGameSeconds(self):
        if self.isPaused() or self.winner:
            return self.elapsed
        else:
            timediff = datetime.datetime.now() - self.resumed
            return self.elapsed + timediff.seconds

    def getStartTime(self): return self.start

    def getPlayers(self): return self.players

    def setPlayers(self, players): self.players = players

    def getScoreFromPlayer(self, player): return self.totalScores[player]

    def getWinner(self): return self.winner

    def isPaused(self): return self.state == self.PAUSED

    def isRunning(self): return self.state == self.RUNNING

    def isCancelled(self): return self.state == self.CANCELLED

    # To be implemented in subclasses
    def playerStart(self, player): pass

    def computeWinner(self): pass


class GenericRoundMatch(GenericMatch):

    def __init__(self, players=[]):
        super(GenericRoundMatch, self).__init__(players)
        self.rounds = list()
        self.dealer = None
        self.dealingp = 2
        self.updatewinnereveryround = True

    def resumeMatch(self, idMatch):
        if not super(GenericRoundMatch, self).resumeMatch(idMatch):
            return False
        cur = db.execute(
            "SELECT idRound,nick,winner,score FROM Round "
            "WHERE idMatch ={} ORDER BY idRound;".format(idMatch))
        current = 0
        rnd = None
        for row in cur:
            if row['idRound'] != current:
                current += 1
                if rnd is not None:
                    self.rounds.append(rnd)
                rnd = self.createRound(current)
            if row['winner'] == 1:
                rnd.setWinner(str(row['nick']))
            rnd.addInfo(str(row['nick']), int(row['score']))
        if rnd is not None:
            self.rounds.append(rnd)

        cur = db.execute(
            "SELECT value FROM MatchExtras "
            "WHERE idMatch ={} and key='Dealer';".format(idMatch))
        row = cur.fetchone()
        if row:
            self.dealer = str(row['value'])

        cur = db.execute(
            "SELECT value FROM MatchExtras "
            "WHERE idMatch ={} and key='DealingPolicy';".format(idMatch))
        row = cur.fetchone()
        if row:
            self.dealingp = int(row['value'])

        cur = db.execute(
            "SELECT idRound,nick,key,value FROM RoundStatistics "
            "WHERE idMatch ={} "
            "ORDER BY idRound,nick,key,value;".format(idMatch))

        currentr = 0
        currentp = ""
        extras = {}
        for row in cur:
            if row['idRound'] != currentr:
                if len(extras):
                    for player, extra in extras.items():
                        self.rounds[currentr-1].addExtraInfo(player, extra)
                extras = {}
                currentp = ""
                currentr += 1

            if str(row['nick']) != currentp:
                currentp = str(row['nick'])
                extras[currentp] = {}

            extras[currentp].update(self.resumeExtraInfo(
                currentp, str(row['key']), str(row['value'])))

        if len(extras):
            for player, extra in extras.items():
                self.rounds[currentr-1].addExtraInfo(player, extra)

        return True

    def flushToDB(self):
        super(GenericRoundMatch, self).flushToDB()

#         db.execute("BEGIN")
        db.execute("DELETE FROM Round where idMatch={};".format(self.idMatch))
        db.execute("DELETE FROM RoundStatistics "
                   "where idMatch={};".format(self.idMatch))

        db.execute("INSERT OR REPLACE INTO MatchExtras (idMatch,key,value) "
                   "VALUES ({},'Dealer','{}');".format(
                        self.idMatch, self.getDealer()))
        db.execute("INSERT OR REPLACE INTO MatchExtras (idMatch,key,value) "
                   "VALUES ({},'DealingPolicy','{}');".format(
                        self.idMatch, self.getDealingPolicy()))

        for rnd in self.rounds:
            for player, score in rnd.getScore().items():
                winner = 0
                if rnd.getWinner() == player:
                    winner = 1
                db.execute("INSERT OR REPLACE INTO Round (idMatch, nick, "
                           "idRound, winner,score) "
                           "VALUES ({},'{}',{},{},{});".format(
                                self.idMatch, str(player),
                                rnd.getNumRound(), winner, score))
#         db.execute("COMMIT")

    def addRound(self, rnd):
        self.rounds.append(rnd)
        for player, score in rnd.getScore().items():
            self.totalScores[player] += score
            self.playerAddRound(player, rnd)
        if self.updatewinnereveryround:
            self.updateWinner()

    def updateRound(self, rnd):
        try:
            oldrnd = self.rounds[rnd.getNumRound()-1]
        except KeyError:
            return
        for player, score in oldrnd.getScore():
            self.totalScores[player] -= score
            self.totalScores[player] -= rnd.getPlayerScore(player)
        self.rounds[rnd.getNumRound()-1] = rnd

    def deleteRound(self, nrnd):
        try:
            rnd = self.rounds[nrnd-1]
        except KeyError:
            return
        for player, score in rnd.getScore().items():
            self.totalScores[player] -= score
        del self.rounds[nrnd-1]
        for i, rnd in enumerate(self.rounds, start=1):
            rnd.setNumRound(i)

    def getRounds(self): return self.rounds

    def getDealer(self):
        if self.dealingp == 3 and len(self.rounds) > 0:
            return None
        return self.dealer

    # To be implemented in subclasses
    def playerAddRound(self, player, rnd): pass

    def resumeExtraInfo(self, player, key, value): return {}

    def createRound(self, numround): return GenericRound(numround)


class GenericRound(object):

    def __init__(self, numround):
        self.numround = numround
        self.score = dict()  # nick -> points
        self.winner = None

    def getNumRound(self): return self.numround

    def setNumRound(self, numround): self.numround = numround

    def setWinner(self, player): self.winner = player

    def getWinner(self): return self.winner

    def getPlayerScore(self, player):
        try:
            return self.score[player]
        except KeyError:
            return -1

    def setPlayerScore(self, player, score):
        try:
            self.score[player] = score
        except KeyError:
            pass

    def getScore(self): return self.score

    def addInfo(self, player, score, extras=None):
        self.score[player] = score
        if extras:
            self.addExtraInfo(player, extras)

    # To be implemented in subclasses
    def addExtraInfo(self, player, extras): pass


class GenericEntry(GenericRound):

    def __init__(self, numround):
        super(GenericEntry, self).__init__(numround)
        self.getNumEntry = self.getNumRound
        self.setNumEntry = self.setNumRound

    def getPlayerScore(self):
        if len(self.score) == 0:
            return -1
        for score in self.score.values():
            return score

    def getPlayer(self):
        if len(self.score) == 0:
            return -1
        for player in self.score.keys():
            return player
