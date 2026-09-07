"""Carcassonne match and entry models."""

from __future__ import annotations

from collections.abc import Sequence
from typing import cast

from core.engine.db import db
from core.model.base import GenericEntry, GenericRound, GenericRoundMatch


class CarcassonneMatch(GenericRoundMatch):
    """Round match for Carcassonne, scored as per-kind entries."""

    def __init__(self, players: Sequence[str] = ()) -> None:
        super().__init__(players)
        self.game = "Carcassonne"
        self.entry_kinds = ["City", "Road", "Cloister", "Field", "Goods", "Fair"]
        self.dealingp = 3
        self.updatewinnereveryround = False

    def getEntryKinds(self) -> list[str]:
        return self.entry_kinds

    def resumeExtraInfo(self, player: str, key: str, value: str) -> dict:
        """Decode a persisted entry-kind statistic row."""
        extra = {}
        if key == "kind":
            extra[key] = value
        return extra

    def createRound(self, numround: int) -> CarcassonneEntry:
        return CarcassonneEntry(numround)

    def addRound(self, rnd: GenericRound) -> None:
        """Append an entry and fold its score into the totals (no winner check)."""
        self.rounds.append(rnd)
        for player, score in rnd.getScore().items():
            self.totalScores[player] += score
            self.playerAddRound(player, rnd)

    def flushToDB(self) -> None:
        """Persist the base match plus each entry's scoring kind."""
        super().flushToDB()
        for entry in cast("list[CarcassonneEntry]", self.rounds):
            db.execute(
                "INSERT OR REPLACE INTO RoundStatistics "
                "(idMatch,nick,idRound,key,value) "
                "VALUES (?,?,?,'kind',?);",
                (self.idMatch, entry.getPlayer(), entry.getNumEntry(), entry.getKind()),
            )

    def computeWinner(self) -> None:
        """Pick the highest total score, breaking ties by per-kind totals."""
        maxscore = max(self.totalScores.values())
        candidates = [
            player for player, score in self.totalScores.items() if score == maxscore
        ]
        if len(candidates) == 1:
            self.winner = candidates.pop()
            return
        # Compute details for candidates
        details = {}
        for kind in self.getEntryKinds():
            details[kind] = {}
            for player in candidates:
                details[kind][player] = 0
        for entry in cast("list[CarcassonneEntry]", self.getRounds()):
            details[cast("str", entry.getKind())][entry.getPlayer()] += (
                entry.getPlayerScore()
            )

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

            for k in details:  # noqa: PLC0206
                for player in removed:
                    del details[k][player]

        # Ultimate draw, pick the first candidate then...
        self.winner = candidates.pop()
        return


class CarcassonneEntry(GenericEntry):
    """A single Carcassonne scoring entry tagged with its feature kind."""

    def __init__(self, numround: int) -> None:
        super().__init__(numround)
        self.kind: str | None = None

    def addExtraInfo(self, player: str, extras: dict) -> None:
        """Record the scoring kind for this entry from ``extras``."""
        try:
            self.kind = extras["kind"]
        except KeyError:
            pass

    def getKind(self) -> str | None:
        return self.kind
