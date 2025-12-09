#!/usr/bin/env python
# -*- coding: utf-8 -*-

import datetime
import random
from abc import abstractmethod
from typing import Callable, TypeVar

from controllers.db import db
from model.base import GenericRoundMatch, Player
from model.gamefactory import GameFactory


class GameEngine(object):
    NoDealer = 0
    RRDealer = 1
    WinnerDealer = 2
    StarterDealer = 3

    def __init__(self):
        self.players = dict()
        self.porder = list()
        if not hasattr(self, "game"):
            self.game = None
        self.match = GameFactory.createMatch(self.game)

    def addPlayer(self, nick, fullName=""):
        if fullName == "":
            fullName = nick
        self.porder.append(nick)
        self.players[nick] = Player()
        self.players[nick].nick = nick
        cur = db.execute("Select * from Player where nick='{}';".format(nick))
        # Exists in db?
        user = cur.fetchone()
        if user:
            self.players[nick].fullName = user["fullName"]
        else:
            self.players[nick].fullName = fullName
            self.players[nick].dateCreation = datetime.datetime.now()
            qd = str(self.players[nick].dateCreation)
            q = """INSERT INTO Player (nick, fullName, dateCreation)
                 VALUES ('{}','{}','{}');""".format(nick, fullName, qd)
            db.execute(q)

    def begin(self):
        if not self.match:
            self.match = GameFactory.createMatch(self.game)
        self.match.setPlayers(self.porder)
        self.match.startMatch()

    def resume(self, idMatch):
        if not self.match:
            self.match = GameFactory.createMatch(self.game)
        if self.match.resumeMatch(idMatch):
            for nick in self.match.getPlayers():
                self.addPlayer(nick)
            return True
        return False

    def getGame(self):
        return self.game

    def getWinner(self):
        if self.match:
            return self.match.getWinner()
        return None

    def getPlayers(self):
        return self.players

    def getListPlayers(self):
        return self.porder

    def setListPlayers(self, neworder):
        if sorted(neworder) == sorted(self.porder):
            self.porder = neworder

    def getScoreFromPlayer(self, player):
        try:
            if self.match:
                return self.match.getScoreFromPlayer(player)
            return 0
        except (KeyError, AttributeError):
            return 0

    def getGameMaxPlayers(self):
        cur = db.execute(
            "Select maxPlayers from Game where name='{}'".format(self.game)
        )
        r = cur.fetchone()
        return int(r["maxPlayers"])

    def pause(self):
        self.match.pause()

    def unpause(self):
        self.match.unpause()

    def save(self):
        self.match.save()

    def isPaused(self):
        return self.match.isPaused()

    def getGameSeconds(self):
        return self.match.getGameSeconds()

    def cancelMatch(self):
        self.match.cancel()

    def getDealingPolicy(self):
        return self.match.getDealingPolicy()

    def setDealingPolicy(self, policy):
        self.match.setDealingPolicy(policy)

    def getDealer(self):
        return self.match.getDealer()

    def setDealer(self, player):
        self.match.setDealer(player)

    def setPlayerOrder(self, porder):
        self.porder = porder

    def updateDealer(self):
        pass


class RoundGameEngine(GameEngine):
    match: "GenericRoundMatch"

    def begin(self):
        super(RoundGameEngine, self).begin()
        if self.getDealingPolicy() != self.NoDealer:
            self.match.setDealer(random.choice(self.porder))

    def openRound(self, nround):
        self.round = self.match.createRound(nround)

    def setRoundWinner(self, winner):
        self.round.setWinner(winner)

    def addRoundInfo(self, player, score, extras=None):
        self.round.addInfo(player, score, extras)

    def commitRound(self):
        self.match.addRound(self.round)
        self.updateDealer()

    def deleteRound(self, nrnd):
        self.match.deleteRound(nrnd)
        self.printStats()

    def getRounds(self):
        return self.match.getRounds()

    def getNumRound(self):
        return len(self.match.rounds) + 1

    def updateDealer(self):
        if self.match.getWinner():
            return
        if self.getDealingPolicy() == self.RRDealer:
            self.updateRRDealer()
        elif self.getDealingPolicy() == self.WinnerDealer:
            self.updateWinnerDealer()

    def updateRRDealer(self):
        candidate = (self.porder.index(self.getDealer()) + 1) % len(self.porder)
        self.match.setDealer(self.porder[candidate])

    def updateWinnerDealer(self):
        self.match.setDealer(self.round.getWinner())

    def printStats(self):
        lastround = self.getNumRound() - 1
        if lastround == 0:
            print("===========================")
            print("|{0:^25}|".format(self.game))
            print("===========================")
            print("")
            print("Players:")
            for n in self.porder:
                if n == self.getDealer():
                    print(" * {} (Dealer)".format(n))
                else:
                    print(" * {}".format(n))
            print("")
            policies = ["None", "Round Robin", "Winner", "Starter"]
            print("DealingPolicy: {}".format(policies[self.getDealingPolicy()]))
            self.printExtraStats()
            print("Game started at {}".format(self.match.getStartTime()))
            print("***************************")
        else:
            print("")
            print("===========================")
            print("|        Round {0:<3}        |".format(lastround))
            print("===========================")
            print("")
            print("Time played: {}".format(self.match.getGameTime()))
            self.printExtraStats()
            print("***************************")
            for n in self.porder:
                print("")
                if n == self.getDealer():
                    print("{} (Dealer)".format(n))
                else:
                    print(n)

                print("Current score: {}".format(self.getScoreFromPlayer(n)))
                self.printExtraPlayerStats(n)
                print("***************************")

            if self.getWinner():
                print("")
                print("!!!!!!!!! Winner: !!!!!!!!!")
                print("{0:^27}".format(self.getWinner()))
                print("!!!!!!!!!!!!!!!!!!!!!!!!!!!")
                print("")
                print(
                    "{} match finished at {}".format(self.game, datetime.datetime.now())
                )
                print("Time played {}".format(self.match.getGameTime()))
                print("")

    #
    # Helper functions for cli test
    #

    def gameStub(self):
        print("Welcome to {} Engine Stub".format(self.getGame()))

        if not db.isConnected():
            db.connectDB("../db/gamelog.db")

        playersOrder = []
        validPlayers = db.getPlayerNicks()
        maxPlayers = self.getGameMaxPlayers()

        errmsg = "Sorry, number of players must be between 2 and {}."
        errmsg = errmsg.format(self.getGameMaxPlayers())
        nplayers = readInput(
            "Number of players: ", int, lambda x: x >= 2 and x <= maxPlayers, errmsg
        )

        for i in range(1, nplayers + 1):
            print("Player {} Info:".format(i))
            errmsg = "Sorry, player not found in DB"
            nick = readInput("Nick: ", str, lambda x: x in validPlayers, errmsg)
            self.addPlayer(nick)
            playersOrder.append(nick)

        self.begin()
        option = readInput(
            "Dealing policy[0:None/1:RoundRobin/2:Winner]: ",
            int,
            lambda x: x in [0, 1, 2],
        )
        if option == 0:
            self.setDealingPolicy(RoundGameEngine.NoDealer)
        elif option == 1:
            self.setDealingPolicy(RoundGameEngine.RRDealer)
        elif option == 2:
            self.setDealingPolicy(RoundGameEngine.WinnerDealer)
        self.extraStubConfig()
        self.runStubRoundLoop()

    def runStubRoundLoop(self):
        self.printStats()
        while not self.getWinner():
            self.openRound(self.getNumRound())
            while True:
                pmt = (
                    "Round {} Winner (or p to pause, s to save and exit,"
                    " c to cancel without saving): "
                )
                pmt = pmt.format(self.getNumRound())
                errmsg = "Sorry, player not found in current match."
                rnd_winner = readInput(
                    pmt,
                    str,
                    lambda x: x in self.getListPlayers() or x in ("p", "s", "c"),
                    errmsg,
                )
                if rnd_winner == "p":
                    self.pause()
                    readInput("Press Enter to unpause...")
                    self.unpause()
                elif rnd_winner == "s":
                    self.save()
                    exit()
                elif rnd_winner == "c":
                    self.cancelMatch()
                    exit()
                else:
                    break

            self.setRoundWinner(rnd_winner)
            for n in self.getListPlayers():
                self.runRoundPlayer(n, rnd_winner)
            self.commitRound()
            self.printStats()

    def runRoundPlayer(self, _name, _winner=None):
        pass

    # To be implemented in subclasses
    @abstractmethod
    def printExtraStats(self):
        pass

    @abstractmethod
    def printExtraPlayerStats(self, player):
        pass

    @abstractmethod
    def runStubRoundPlayer(self, player, winner):
        pass

    @abstractmethod
    def extraStubConfig(self):
        pass


class EntryGameEngine(RoundGameEngine):
    def addEntry(self, player, score, extras=None):
        self.openRound(self.getNumRound())
        self.addRoundInfo(player, score, extras)
        self.commitRound()

    def finishGame(self):
        self.match.updateWinner()
        self.printStats()

    def runStubRoundLoop(self):
        self.printStats()
        while not self.getWinner():
            while True:
                pmt = (
                    "Enter player entry (or p to pause, "
                    "f to finish the game, "
                    "s to save and exit, c to cancel without saving):"
                )
                pmt = pmt.format(self.getNumEntry())
                errmsg = "Sorry, player not found in current match."
                entry_player = readInput(
                    pmt,
                    str,
                    lambda x: x in self.getListPlayers() or x in ("p", "s", "c", "f"),
                    errmsg,
                )
                if entry_player == "p":
                    self.pause()
                    readInput("Press Enter to unpause...")
                    self.unpause()
                elif entry_player == "f":
                    self.finishGame()
                    self.printStats()
                    exit()
                elif entry_player == "s":
                    self.save()
                    exit()
                elif entry_player == "c":
                    self.cancelMatch()
                    exit()
                else:
                    break
            self.runRoundPlayer(entry_player)
            self.printStats()

    @abstractmethod
    def getNumEntry(self):
        pass


#
# Helper functions for cli test
#
#

T = TypeVar("T")


def readInput(
    prompt: str,
    cast: Callable[[str], T] = str,
    validator: Callable[[T], bool] = lambda x: True,
    errormsg: str = "Sorry, invalid answer.",
) -> T:
    while True:
        try:
            value = cast(input(prompt))
            if validator(value):
                return value
            else:
                print(errormsg)
        except Exception:
            print(errormsg)
