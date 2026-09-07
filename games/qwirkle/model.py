"""Qwirkle match model: an entry-scored game with qwirkle-bonus tie-breaking."""

from __future__ import annotations

from collections.abc import Sequence
from typing import ClassVar, cast

from core.engine.db import db
from core.model.base import GenericEntry, GenericRoundMatch


class QwirkleMatch(GenericRoundMatch):
    """Entry-based match for Qwirkle, won on total score with qwirkle tie-breaks."""

    bonuses: ClassVar[dict] = {"qwirkles": 6}

    def __init__(self, players: Sequence[str] = ()) -> None:
        super().__init__(players)
        self.game = "Qwirkle"
        self.dealingp = 1
        self.updatewinnereveryround = False

    def createRound(self, numround: int) -> QwirkleEntry:
        return QwirkleEntry(numround)

    def getBonuses(self) -> dict:
        return self.bonuses

    def flushToDB(self) -> None:
        """Persist the base match plus each entry's qwirkle-bonus count."""
        super().flushToDB()
        for entry in cast("list[QwirkleEntry]", self.rounds):
            if entry.getQwirkles():
                db.execute(
                    "INSERT OR REPLACE INTO RoundStatistics "
                    "(idMatch,nick,idRound,key,value) "
                    "VALUES (?,?,?,'qwirkles',?);",
                    (
                        self.idMatch,
                        entry.getPlayer(),
                        entry.getNumEntry(),
                        entry.getQwirkles(),
                    ),
                )

    def computeWinner(self) -> None:
        """Pick the highest-scoring player, breaking ties on qwirkles then best play."""
        maxscore = max(self.totalScores.values())
        candidates = [
            player for player, score in self.totalScores.items() if score == maxscore
        ]
        if len(candidates) == 1:
            self.winner = candidates.pop()
            return
        # Draw: check who's got more qwirkles
        qwirkles_tally = dict.fromkeys(candidates, 0)
        for entry in cast("list[QwirkleEntry]", self.getRounds()):
            qwirkles = entry.getQwirkles()
            if qwirkles:
                try:
                    qwirkles_tally[entry.getPlayer()] += qwirkles
                except KeyError:
                    pass

        max_qwirkles = max(qwirkles_tally.values())

        for player, qwirkles in qwirkles_tally.items():
            if qwirkles != max_qwirkles:
                candidates.remove(player)

        if len(candidates) == 1:
            self.winner = candidates.pop()
            return

        # Draw: Check who's got max single play score
        max_entry_scores = dict.fromkeys(candidates, 0)
        for entry in cast("list[QwirkleEntry]", self.getRounds()):
            try:
                max_entry_scores[entry.getPlayer()] = max(
                    max_entry_scores[entry.getPlayer()], entry.getPlayerScore()
                )
            except KeyError:
                pass
        max_entry_score = max(max_entry_scores.values())

        for player, score in max_entry_scores.items():
            if score != max_entry_score:
                candidates.remove(player)

        if len(candidates) == 1:
            self.winner = candidates.pop()
            return

        # Ultimate draw, pick the first candidate then...
        self.winner = candidates.pop()
        return


class QwirkleEntry(GenericEntry):
    """A single scoring entry, tracking the qwirkle bonuses it earned."""

    def __init__(self, numround: int) -> None:
        super().__init__(numround)
        self.bonuses: dict[str, int] = {"qwirkles": 0}

    def addExtraInfo(self, player: str, extras: dict) -> None:
        try:
            self.bonuses = extras
        except KeyError:
            pass

    def getBonuses(self) -> dict:
        return self.bonuses

    def getQwirkles(self) -> int:
        try:
            return self.bonuses["qwirkles"]
        except KeyError:
            return 0

    def __repr__(self) -> str:
        return f"{self.getNumEntry()}: {self.getPlayer()} - {self.getPlayerScore()} | {self.getBonuses()}"
