import datetime
import logging
import random
import sys
from abc import abstractmethod
from collections.abc import Callable
from typing import TypeVar

from core.engine.db import db
from core.model.base import GenericRoundMatch, Player
from core.registry import registry

logger = logging.getLogger(__name__)


class GameEngine:
    NoDealer = 0
    RRDealer = 1
    WinnerDealer = 2
    StarterDealer = 3

    def __init__(self):
        self.players = {}
        self.porder = []
        if not hasattr(self, "game"):
            self.game = None
        self.match = registry.create_match(self.game)

    def addPlayer(self, nick, fullName=""):
        if fullName == "":
            fullName = nick
        self.porder.append(nick)
        self.players[nick] = Player()
        self.players[nick].nick = nick
        cur = db.execute("Select * from Player where nick=?;", (nick,))
        # Exists in db?
        user = cur.fetchone()
        if user:
            self.players[nick].fullName = user["fullName"]
        else:
            self.players[nick].fullName = fullName
            self.players[nick].dateCreation = datetime.datetime.now(tz=datetime.UTC)
            qd = str(self.players[nick].dateCreation)
            db.execute(
                "INSERT INTO Player (nick, fullName, dateCreation) VALUES (?,?,?);",
                (nick, fullName, qd),
            )

    def begin(self):
        if not self.match:
            self.match = registry.create_match(self.game)
        self.match.setPlayers(self.porder)
        self.match.startMatch()

    def resume(self, idMatch):
        if not self.match:
            self.match = registry.create_match(self.game)
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
        cur = db.execute("Select maxPlayers from Game where name=?", (self.game,))
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

    def getStartTime(self):
        return self.match.getStartTime()

    def getFinishTime(self):
        return self.match.getFinishTime()

    def getGameSeconds(self):
        return self.match.getGameSeconds()

    def requiresExplicitFinish(self) -> bool:
        return False

    def updateTimes(self, start, finish, seconds):
        self.match.setStartTime(start)
        self.match.setFinishTime(finish)
        self.match.setGameSeconds(seconds)
        logger.debug("Updated times: %s | %s | %s", start, finish, seconds)
        self.match.flushToDB()

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

    def __init__(self):
        super().__init__()
        self.starting_dealer = None

    def begin(self):
        super().begin()
        if self.getDealingPolicy() != self.NoDealer:
            self.starting_dealer = random.choice(self.porder)
            self.match.setDealer(self.starting_dealer)

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
        self.updateDealer(back=True)
        self.printStats()

    def getRounds(self):
        return self.match.getRounds()

    def getNumRound(self):
        return len(self.match.rounds) + 1

    def updateDealer(self, back=False):
        if self.match.getWinner():
            return
        if self.getDealingPolicy() == self.RRDealer:
            self.updateRRDealer(back)
        elif self.getDealingPolicy() == self.WinnerDealer:
            self.updateWinnerDealer(back)

    def updateRRDealer(self, back=False):
        increment = -1 if back else 1
        candidate = (self.porder.index(self.getDealer()) + increment) % len(self.porder)
        self.match.setDealer(self.porder[candidate])

    def updateWinnerDealer(self, back=False):
        try:
            newdealer = self.getRounds()[-1].getWinner()
        except IndexError:
            newdealer = self.starting_dealer
        self.match.setDealer(newdealer)

    def printStats(self):
        # The board is a verbose console dump; skip it entirely unless debug
        # logging is on. (Kept as prints so the ASCII board stays intact,
        # including subclass printExtra* hooks.)
        if not logger.isEnabledFor(logging.DEBUG):
            return
        lastround = self.getNumRound() - 1
        if lastround == 0:
            print("===========================")
            print(f"|{self.game:^25}|")
            print("===========================")
            print()
            print("Players:")
            for n in self.porder:
                if n == self.getDealer():
                    print(f" * {n} (Dealer)")
                else:
                    print(f" * {n}")
            print()
            policies = ["None", "Round Robin", "Winner", "Starter"]
            print(f"DealingPolicy: {policies[self.getDealingPolicy()]}")
            self.printExtraStats()
            print(f"Game started at {self.match.getStartTime()}")
            print("***************************")
        else:
            print()
            print("===========================")
            print(f"|        Round {lastround:<3}        |")
            print("===========================")
            print()
            print(f"Time played: {self.match.getGameTime()}")
            self.printExtraStats()
            print("***************************")
            for n in self.porder:
                print()
                if n == self.getDealer():
                    print(f"{n} (Dealer)")
                else:
                    print(n)

                print(f"Current score: {self.getScoreFromPlayer(n)}")
                self.printExtraPlayerStats(n)
                print("***************************")

            if self.getWinner():
                print()
                print("!!!!!!!!! Winner: !!!!!!!!!")
                print(f"{self.getWinner():^27}")
                print("!!!!!!!!!!!!!!!!!!!!!!!!!!!")
                print()
                print(
                    f"{self.game} match finished at {datetime.datetime.now(tz=datetime.UTC)}"
                )
                print(f"Time played {self.match.getGameTime()}")
                print()

    #
    # Helper functions for cli test
    #

    def gameStub(self):
        # CLI test harness: turn on debug logging so printStats() shows the
        # board (it is silent at the default level).
        from core.logging_config import configure_logging

        configure_logging("DEBUG")
        print(f"Welcome to {self.getGame()} Engine Stub")

        if not db.isConnected():
            db.connectDB()

        playersOrder = []
        validPlayers = db.getPlayerNicks()
        maxPlayers = self.getGameMaxPlayers()

        errmsg = "Sorry, number of players must be between 2 and {}."
        errmsg = errmsg.format(self.getGameMaxPlayers())
        nplayers = readInput(
            "Number of players: ", int, lambda x: x >= 2 and x <= maxPlayers, errmsg
        )

        for i in range(1, nplayers + 1):
            print(f"Player {i} Info:")
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
                    sys.exit()
                elif rnd_winner == "c":
                    self.cancelMatch()
                    sys.exit()
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
                    sys.exit()
                elif entry_player == "s":
                    self.save()
                    sys.exit()
                elif entry_player == "c":
                    self.cancelMatch()
                    sys.exit()
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


def readInput[T](
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
        except Exception:  # noqa: BLE001
            print(errormsg)
