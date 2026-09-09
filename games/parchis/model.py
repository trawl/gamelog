"""Parchis classic board game model."""

from __future__ import annotations

from collections.abc import Sequence
from typing import cast

from core.engine.db import db
from core.model.base import GenericEntry, GenericRoundMatch


class ParchisMatch(GenericRoundMatch):
    """Entry-based match for parchis, won by the first to get 4 tokens to the goal."""

    def __init__(self, players: Sequence[str] = ()) -> None:
        super().__init__(players)
        self.game = "Parchis"
        self.top = 4
        self.dealingp = 0

    def computeWinner(self) -> None:
        """Once any player reaches ``top``, the lowest total score wins."""
        if max(self.totalScores.values()) >= self.top:
            winner = None
            minscore = 100000
            for player, score in self.totalScores.items():
                if score < minscore:
                    winner = player
                    minscore = score

            if winner is not None:
                self.winner = winner

    def createRound(self, numround: int) -> GenericEntry:
        return ParchisEntry(numround)

    def getTop(self) -> int:
        return self.top

    def setTop(self, top: int) -> None:
        self.top = top

    def resumeExtraInfo(self, player: str, key: str, value: str) -> dict:
        """Decode a persisted entry-kind statistic row."""
        extra = {}
        if key == "kill":
            extra[key] = value
        return extra

    def getKillsTally(self) -> dict[str, dict[str, int]]:
        """Generate a matrix of with the kill tally."""
        kill_tally = {killer: dict.fromkeys(self.players, 0) for killer in self.players}
        for entry in cast("list[ParchisEntry]", self.rounds):
            for kill in entry.getKills():
                kill_tally[entry.getPlayer()][kill] += 1
        return kill_tally

    def getComboTally(self) -> dict[str, int]:
        """Return the number of combos per player."""
        combo_tally = dict.fromkeys(self.players, 0)
        for entry in cast("list[ParchisEntry]", self.rounds):
            combo_tally[entry.getPlayer()] += max(
                0, entry.getPlayerScore(entry.getPlayer()) - 1
            ) + max(0, len(entry.getKills()) - 1)
        return combo_tally

    def flushToDB(self) -> None:
        """Persist the base match plus each entry's kills if any"""
        super().flushToDB()
        for entry in cast("list[ParchisEntry]", self.rounds):
            for kill in entry.getKills():
                db.execute(
                    "INSERT OR REPLACE INTO RoundStatistics "
                    "(idMatch,nick,idRound,key,value) "
                    "VALUES (?,?,?,'kind',?);",
                    (self.idMatch, entry.getPlayer(), entry.getNumEntry(), kill),
                )


class ParchisEntry(GenericEntry):
    """A Parchis entry with extras."""

    def __init__(self, numround: int) -> None:
        super().__init__(numround)
        self.kills: list[str] = []

    def addExtraInfo(self, player: str, extras: dict) -> None:
        """Record the scoring kind for this entry from ``extras``."""
        try:
            if extras["kill"]:
                self.kills.append(extras["kill"])
        except KeyError:
            pass

    def getKills(self) -> list[str]:
        return self.kills
