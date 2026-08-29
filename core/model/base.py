"""Game-agnostic match/round domain models.

These classes hold the state and persistence logic shared by every game and
carry no Qt dependency. Concrete games subclass ``GenericMatch`` /
``GenericRoundMatch`` (and their round types) to add game-specific rules.
"""

from __future__ import annotations

import datetime
import logging
from abc import abstractmethod
from collections.abc import Sequence

from core.engine.db import db

logger = logging.getLogger(__name__)


class Player:
    """A registered player. Currently a lightweight record of identity."""

    def __init__(self) -> None:
        self.nick: str = ""
        self.fullName: str = ""
        self.dateCreation: datetime.datetime | None = None


class GenericMatch:
    """Base match: players, timing, winner and SQLite persistence.

    A match moves through the ``state`` values below over its lifetime and is
    flushed to the database whenever that state changes.
    """

    # Match states.
    RUNNING = 0
    FINISHED = 1
    CANCELLED = 2
    PAUSED = 3
    SAVED = 4

    def __init__(self, players: Sequence[str] = ()) -> None:
        self.game = "Generic"
        self.players: Sequence[str] = players
        self.winner: str | None = None
        self.start: datetime.datetime | None = None
        self.resumed: datetime.datetime = datetime.datetime.now(tz=datetime.UTC)
        self.finish: datetime.datetime | None = None
        self.elapsed = 0
        self.totalScores: dict[str, int] = {}
        self.idMatch = -1
        self.state = self.CANCELLED
        self.dealer: str | None = None
        self.dealingp = 0

    # --- Lifecycle ---------------------------------------------------------

    def resumeMatch(self, idMatch: int) -> bool:
        """Reload a previously saved match from the database.

        Returns ``True`` on success, or ``False`` if this match already
        started, the id is invalid, or no matching saved match exists.
        """
        if self.start is not None:
            return False
        if not isinstance(idMatch, int):
            return False
        cur = db.execute(
            "SELECT Game_name,state,started,elapsed FROM Match WHERE idMatch =?;",
            (idMatch,),
        )
        if not cur:
            return False
        row = cur.fetchone()
        if not row:
            return False
        if row["Game_name"] != self.game or row["state"] != self.SAVED:
            return False
        self.elapsed = int(row["elapsed"])
        try:
            self.start = datetime.datetime.strptime(
                row["started"], "%Y-%m-%d %H:%M:%S.%f%z"
            ).astimezone(datetime.UTC)
        except ValueError:
            self.start = datetime.datetime.strptime(
                row["started"], "%Y-%m-%d %H:%M:%S.%f"
            ).replace(tzinfo=datetime.UTC)
        self.resumed = datetime.datetime.now(tz=datetime.UTC)
        # Retrieve players
        self.players = []
        cur = db.execute(
            "SELECT rowid,nick,totalScore FROM MatchPlayer "
            "WHERE idMatch =? ORDER BY rowid;",
            (idMatch,),
        )
        for row in cur:
            player = str(row["nick"])
            self.players.append(player)
            self.totalScores[player] = int(row["totalScore"])

        self.state = self.RUNNING
        self.idMatch = idMatch
        return True

    def startMatch(self) -> None:
        """Begin a fresh match, zeroing every player's total score."""
        self.start = datetime.datetime.now(tz=datetime.UTC)
        self.resumed = self.start
        self.state = self.RUNNING
        for p in self.players:
            self.totalScores[p] = 0
            self.playerStart(p)

    def cancel(self) -> None:
        """Mark an unfinished match as cancelled and persist it."""
        if not self.isCancelled() and not self.winner:
            self.flushState(self.CANCELLED)
            logger.info("%s match cancelled at %s", self.game, self.finish)

    def save(self) -> None:
        """Persist the match in the SAVED state so it can be resumed later."""
        self.flushState(self.SAVED)
        logger.info("%s saved at %s", self.game, self.finish)

    def pause(self) -> None:
        """Suspend elapsed-time accounting while the match is paused."""
        if not self.isPaused():
            self.updateElapsed()
            self.state = self.PAUSED
            logger.debug("%s paused at %s", self.game, self.finish)

    def unpause(self) -> None:
        """Resume elapsed-time accounting after a pause."""
        if self.isPaused():
            self.resumed = datetime.datetime.now(tz=datetime.UTC)
            self.state = self.RUNNING
            logger.debug("%s resumed at %s", self.game, self.resumed)

    def updateWinner(self) -> None:
        """Recompute the winner and, if there is one, finish the match."""
        self.computeWinner()
        if self.winner:
            self.flushState(self.FINISHED)

    # --- Persistence -------------------------------------------------------

    def flushState(self, state: int) -> None:
        """Set ``state``, refresh elapsed time and write the match out."""
        self.updateElapsed()
        self.state = state
        self.flushToDB()

    def flushToDB(self) -> None:
        """Insert or update the Match and MatchPlayer rows for this match."""
        if self.idMatch is not None and self.idMatch < 0:
            cur = db.execute(
                "INSERT INTO Match (Game_name, state, started,"
                "finished,elapsed) "
                "VALUES (?,?,?,?,?);",
                (
                    self.game,
                    self.state,
                    str(self.start),
                    str(self.finish),
                    self.elapsed,
                ),
            )
            self.idMatch = cur.lastrowid
        else:
            cur = db.execute(
                "INSERT OR REPLACE INTO Match (idMatch,Game_name,"
                "state,started,finished,elapsed) "
                "VALUES (?,?,?,?,?,?);",
                (
                    self.idMatch,
                    self.game,
                    self.state,
                    str(self.start),
                    str(self.finish),
                    self.elapsed,
                ),
            )
        for p in self.players:
            winner = 0
            if str(p) == self.getWinner():
                winner = 1
            db.execute(
                "INSERT OR REPLACE INTO MatchPlayer"
                "(idMatch,nick,totalScore,winner) "
                "VALUES (?,?,?,?);",
                (self.idMatch, str(p), self.getScoreFromPlayer(str(p)), winner),
            )

    # --- Timing ------------------------------------------------------------

    def updateElapsed(self) -> None:
        """Add the time since the last resume to the elapsed-seconds total."""
        self.finish = datetime.datetime.now(tz=datetime.UTC)
        timediff = self.finish - self.resumed
        self.elapsed += timediff.seconds

    def getGameTime(self) -> str:
        """Return the total play time formatted as ``HH:MM:SS``."""
        hours, remainder = divmod(self.getGameSeconds(), 3600)
        minutes, seconds = divmod(remainder, 60)
        return f"{hours:02}:{minutes:02}:{seconds:02}"

    def getGameSeconds(self) -> int:
        """Return the total play time in seconds, including the live segment."""
        if self.isPaused() or self.winner:
            return self.elapsed
        else:
            timediff = datetime.datetime.now(tz=datetime.UTC) - self.resumed
            return self.elapsed + timediff.seconds

    def getStartTime(self) -> datetime.datetime | None:
        return self.start

    def getFinishTime(self) -> datetime.datetime | None:
        return self.finish

    def setStartTime(self, start: datetime.datetime | None) -> None:
        self.start = start

    def setFinishTime(self, finish: datetime.datetime | None) -> None:
        self.finish = finish

    def setGameSeconds(self, seconds: int) -> None:
        self.elapsed = seconds

    # --- Dealer ------------------------------------------------------------

    def getDealer(self) -> str | None:
        return self.dealer

    def setDealer(self, player: str) -> None:
        if player not in self.players:
            return
        self.dealer = player

    def getDealingPolicy(self) -> int:
        return self.dealingp

    def setDealingPolicy(self, policy: int) -> None:
        if policy not in [0, 1, 2, 3]:
            return
        self.dealingp = policy

    # --- Players & scores --------------------------------------------------

    def getPlayers(self) -> Sequence[str]:
        return self.players

    def setPlayers(self, players: Sequence[str]) -> None:
        self.players = players

    def getActivePlayers(self) -> Sequence[str]:
        """Players still in the match; all of them unless a game overrides."""
        return self.getPlayers()

    def isPlayerOff(self, player: str) -> bool:
        """Whether ``player`` has been eliminated. False unless overridden."""
        return False

    def getScoreFromPlayer(self, player: str) -> int:
        return self.totalScores[player]

    def getWinner(self) -> str | None:
        return self.winner

    # --- State queries -----------------------------------------------------

    def isPaused(self) -> bool:
        return self.state == self.PAUSED

    def isRunning(self) -> bool:
        return self.state == self.RUNNING

    def isCancelled(self) -> bool:
        return self.state == self.CANCELLED

    # --- Subclass hooks ----------------------------------------------------

    @abstractmethod
    def playerStart(self, player: str) -> None:
        """Initialise per-player state when a match starts."""

    @abstractmethod
    def computeWinner(self) -> None:
        """Set ``self.winner`` according to the game's rules, if decided."""


class GenericRoundMatch(GenericMatch):
    """A match played as an ordered list of rounds.

    Adds round persistence, running-total maintenance and per-round extra
    statistics on top of :class:`GenericMatch`.
    """

    def __init__(self, players: Sequence[str] = ()) -> None:
        super().__init__(players)
        self.rounds: list[GenericRound] = []
        self.dealer = None
        self.dealingp = 2
        self.updatewinnereveryround = True

    def resumeMatch(self, idMatch: int) -> bool:
        """Reload the base match plus its rounds, dealer and round extras."""
        if not super().resumeMatch(idMatch):
            return False
        cur = db.execute(
            "SELECT idRound,nick,winner,score FROM Round "
            "WHERE idMatch =? ORDER BY idRound;",
            (idMatch,),
        )
        current = 0
        rnd = None
        for row in cur:
            if row["idRound"] != current:
                current += 1
                if rnd is not None:
                    self.rounds.append(rnd)
                rnd = self.createRound(current)
            elif rnd is None:
                continue
            if row["winner"] == 1:
                rnd.setWinner(str(row["nick"]))
            rnd.addInfo(str(row["nick"]), int(row["score"]))
        if rnd is not None:
            self.rounds.append(rnd)

        cur = db.execute(
            "SELECT value FROM MatchExtras WHERE idMatch =? and key='Dealer';",
            (idMatch,),
        )
        row = cur.fetchone()
        if row:
            self.dealer = str(row["value"])

        cur = db.execute(
            "SELECT value FROM MatchExtras WHERE idMatch =? and key='DealingPolicy';",
            (idMatch,),
        )
        row = cur.fetchone()
        if row:
            self.dealingp = int(row["value"])

        cur = db.execute(
            "SELECT idRound,nick,key,value FROM RoundStatistics "
            "WHERE idMatch =? "
            "ORDER BY idRound,nick,key,value;",
            (idMatch,),
        )

        currentr = 0
        currentp = ""
        extras: dict[str, dict] = {}
        for row in cur:
            if row["idRound"] != currentr:
                if len(extras):
                    for player, extra in extras.items():
                        self.rounds[currentr - 1].addExtraInfo(player, extra)
                extras = {}
                currentp = ""
                currentr += 1

            if str(row["nick"]) != currentp:
                currentp = str(row["nick"])
                extras[currentp] = {}

            extras[currentp].update(
                self.resumeExtraInfo(currentp, str(row["key"]), str(row["value"]))
            )

        if len(extras):
            for player, extra in extras.items():
                self.rounds[currentr - 1].addExtraInfo(player, extra)

        return True

    def flushToDB(self) -> None:
        """Persist the base match plus every round and its extra statistics."""
        super().flushToDB()

        #         db.execute("BEGIN")
        db.execute("DELETE FROM Round where idMatch=?;", (self.idMatch,))
        db.execute("DELETE FROM RoundStatistics where idMatch=?;", (self.idMatch,))

        db.execute(
            "INSERT OR REPLACE INTO MatchExtras (idMatch,key,value) "
            "VALUES (?,'Dealer',?);",
            (self.idMatch, str(self.getDealer())),
        )
        db.execute(
            "INSERT OR REPLACE INTO MatchExtras (idMatch,key,value) "
            "VALUES (?,'DealingPolicy',?);",
            (self.idMatch, str(self.getDealingPolicy())),
        )

        for rnd in self.rounds:
            for player, score in rnd.getScore().items():
                winner = 0
                if rnd.getWinner() == player:
                    winner = 1
                db.execute(
                    "INSERT OR REPLACE INTO Round (idMatch, nick, "
                    "idRound, winner,score) "
                    "VALUES (?,?,?,?,?);",
                    (self.idMatch, str(player), rnd.getNumRound(), winner, score),
                )

    #         db.execute("COMMIT")

    def addRound(self, rnd: GenericRound) -> None:
        """Append a completed round and fold its scores into the totals."""
        self.rounds.append(rnd)
        for player, score in rnd.getScore().items():
            self.totalScores[player] += score
            self.playerAddRound(player, rnd)
        if self.updatewinnereveryround:
            self.updateWinner()

    def updateRound(self, rnd: GenericRound) -> None:
        """Replace an existing round in place, adjusting running totals."""
        try:
            oldrnd = self.rounds[rnd.getNumRound() - 1]
        except KeyError:
            return
        for player, score in oldrnd.getScore().items():
            self.totalScores[player] -= score
            self.totalScores[player] -= rnd.getPlayerScore(player)
        self.rounds[rnd.getNumRound() - 1] = rnd

    def deleteRound(self, nrnd: int) -> None:
        """Remove round ``nrnd`` (1-based) and renumber the rounds after it."""
        try:
            rnd = self.rounds[nrnd - 1]
        except KeyError:
            return
        for player, score in rnd.getScore().items():
            self.totalScores[player] -= score
        del self.rounds[nrnd - 1]
        for i, rnd in enumerate(self.rounds, start=1):
            rnd.setNumRound(i)

    def getRounds(self) -> list[GenericRound]:
        return self.rounds

    def getDealer(self) -> str | None:
        """The current dealer, or ``None`` once the 'no dealer' policy is set."""
        if self.dealingp == 3 and len(self.rounds) > 0:
            return None
        return self.dealer

    def createRound(self, numround: int) -> GenericRound:
        """Build the round object for round number ``numround``."""
        return GenericRound(numround)

    def resumeExtraInfo(self, _player: str, _key: str, _value: str) -> dict:
        """Decode a persisted round-statistic row. Empty unless overridden."""
        return {}

    @abstractmethod
    def playerAddRound(self, player: str, rnd: GenericRound) -> None:
        """Update per-player state after ``player`` records ``rnd``."""


class GenericRound:
    """One round of a match: a per-player score map and an optional winner."""

    def __init__(self, numround: int) -> None:
        self.numround = numround
        self.score: dict[str, int] = {}
        self.winner: str | None = None

    def getNumRound(self) -> int:
        return self.numround

    def setNumRound(self, numround: int) -> None:
        self.numround = numround

    def setWinner(self, player: str) -> None:
        self.winner = player

    def getWinner(self) -> str | None:
        return self.winner

    def getPlayerScore(self, player: str) -> int:
        try:
            return self.score[player]
        except KeyError:
            return -1

    def setPlayerScore(self, player: str, score: int) -> None:
        try:
            self.score[player] = score
        except KeyError:
            pass

    def getScore(self) -> dict[str, int]:
        return self.score

    def addInfo(self, player: str, score: int, extras: dict | None = None) -> None:
        """Record ``player``'s score and, optionally, their round extras."""
        self.score[player] = score
        if extras:
            self.addExtraInfo(player, extras)

    @abstractmethod
    def addExtraInfo(self, player: str, extras: dict) -> None:
        """Attach game-specific extra statistics for ``player``."""


class GenericEntry(GenericRound):
    """A single-score 'round' (one entry per player) for non-round games."""

    def __init__(self, numround: int) -> None:
        super().__init__(numround)
        self.getNumEntry = self.getNumRound
        self.setNumEntry = self.setNumRound

    def getPlayerScore(self, player: str | None = None) -> int:
        if len(self.score) == 0:
            return -1
        for score in self.score.values():
            return score
        return -1

    def getPlayer(self) -> str:
        """Return this entry's single player, or ``""`` if none recorded yet."""
        for player in self.score:
            return player
        return ""
        return -1
