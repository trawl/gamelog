"""Remigio match and round models."""

from __future__ import annotations

from collections.abc import Sequence
from typing import cast

from core.engine.db import db
from core.model.base import GenericRound, GenericRoundMatch


class RemigioMatch(GenericRoundMatch):
    """Round match for Remigio: players drop out once they pass the top score."""

    def __init__(self, players: Sequence[str] = ()) -> None:
        super().__init__(players)
        self.game = "Remigio"
        self.activeplayers: list[str] = []
        self.playersoff: list[str] = []
        self.top = 100

    def playerStart(self, player: str) -> None:
        if self.getScoreFromPlayer(player) < self.top:
            self.activeplayers.append(player)
        else:
            self.playersoff.append(player)

    def addRound(self, rnd: GenericRound) -> None:
        """Apply the close-type multiplier to scores, then record the round."""
        closeType = cast("RemigioRound", rnd).getCloseType()
        if closeType > 1:
            for player in rnd.getScore().keys():  # noqa: SIM118
                rnd.setPlayerScore(player, closeType * rnd.getPlayerScore(player))
        GenericRoundMatch.addRound(self, rnd)

    def deleteRound(self, nrnd: int) -> None:
        """Remove a round and reinstate any player now back under the top."""
        super().deleteRound(nrnd)
        for player in self.playersoff[:]:
            if self.totalScores[player] < self.top:
                self.activeplayers.append(player)
                self.playersoff.remove(player)

    def computeWinner(self) -> None:
        """Retire players at or above the top; the last one standing wins."""
        for p in self.activeplayers[:]:
            if self.totalScores[p] >= self.top:
                self.activeplayers.remove(p)
                self.playersoff.append(p)

        if len(self.activeplayers) == 1:
            self.winner = self.activeplayers[0]

    def resumeMatch(self, idMatch: int) -> bool:
        """Reload the base match plus the top score and active/off players."""
        if not super().resumeMatch(idMatch):
            return False

        cur = db.execute(
            "SELECT value FROM MatchExtras WHERE idMatch =? and key='Top';",
            (idMatch,),
        )
        if cur:
            row = cur.fetchone()
            if row:
                self.top = int(row["value"])

        for player in self.getPlayers():
            self.playerStart(player)

        return True

    def resumeExtraInfo(self, player: str, key: str, value: str) -> dict:
        """Decode a persisted close-type statistic row."""
        extra = {}
        if key == "closeType":
            extra[key] = int(value)
        return extra

    def createRound(self, numround: int) -> RemigioRound:
        return RemigioRound(numround)

    def getActivePlayers(self) -> Sequence[str]:
        return self.activeplayers

    def getPlayersOff(self) -> list[str]:
        return self.playersoff

    def isPlayerOff(self, player: str) -> bool:
        return player in self.playersoff

    def getTop(self) -> int:
        return self.top

    def setTop(self, top: int) -> None:
        if top <= 0:
            return
        self.top = top

    def flushToDB(self) -> None:
        """Persist the base match plus the top score and per-round close types."""
        super().flushToDB()
        db.execute(
            "INSERT OR REPLACE INTO MatchExtras (idMatch,key,value) "
            "VALUES (?,'Top',?);",
            (self.idMatch, self.top),
        )
        for rnd in cast("list[RemigioRound]", self.rounds):
            db.execute(
                "INSERT OR REPLACE INTO RoundStatistics "
                "(idMatch,nick,idRound,key,value) "
                "VALUES (?,?,?,'closeType',?);",
                (self.idMatch, rnd.getWinner(), rnd.getNumRound(), rnd.closeType),
            )


class RemigioRound(GenericRound):
    """One Remigio round, carrying the winner's close type (score multiplier)."""

    def __init__(self, numround: int) -> None:
        super().__init__(numround)
        self.closeType = 1

    def addExtraInfo(self, player: str, extras: dict) -> None:
        """Record the winner's close type for this round from ``extras``."""
        player = str(player)
        if player == self.getWinner():
            try:
                self.closeType = extras["closeType"]
            except KeyError:
                pass

    def getCloseType(self) -> int:
        return self.closeType
