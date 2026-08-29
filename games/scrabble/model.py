"""Scrabble match and entry models."""

from __future__ import annotations

from collections.abc import Sequence
from typing import ClassVar, cast

from core.engine.db import db
from core.model.base import GenericEntry, GenericRoundMatch


class ScrabbleMatch(GenericRoundMatch):
    """Round match for Scrabble, scored as per-turn entries with bonuses."""

    bonuses: ClassVar[dict] = {"dl": 2, "tl": 2, "dw": 2, "tw": 1, "bingo": 1}

    def __init__(self, players: Sequence[str] = ()) -> None:
        super().__init__(players)
        self.game = "Scrabble"
        self.dealingp = 1
        self.updatewinnereveryround = False

    def createRound(self, numround: int) -> ScrabbleEntry:
        return ScrabbleEntry(numround)

    def getBonuses(self) -> dict:
        return self.bonuses

    def flushToDB(self) -> None:
        """Persist the base match plus each entry's non-zero bonus tallies."""
        super().flushToDB()
        for entry in cast("list[ScrabbleEntry]", self.rounds):
            for bonus, tally in entry.getBonuses().items():
                if tally:
                    db.execute(
                        "INSERT OR REPLACE INTO RoundStatistics "
                        "(idMatch,nick,idRound,key,value) "
                        "VALUES (?,?,?,?,?);",
                        (
                            self.idMatch,
                            entry.getPlayer(),
                            entry.getNumEntry(),
                            bonus,
                            tally,
                        ),
                    )

    def computeWinner(self) -> None:
        """Pick the top total score, breaking ties by bonuses then best turn."""
        maxscore = max(self.totalScores.values())
        candidates = [
            player for player, score in self.totalScores.items() if score == maxscore
        ]
        if len(candidates) == 1:
            self.winner = candidates.pop()
            return
        # Draw: check who's got more bonuses
        bonuses_tally = dict.fromkeys(candidates, 0)
        for entry in cast("list[ScrabbleEntry]", self.getRounds()):
            try:
                bonuses_tally[entry.getPlayer()] += sum(entry.getBonuses().values())
            except KeyError:
                pass

        max_bonuses = max(bonuses_tally.values())

        for player, bonus_tally in bonuses_tally.items():
            if bonus_tally != max_bonuses:
                candidates.remove(player)

        if len(candidates) == 1:
            self.winner = candidates.pop()
            return

        # Draw: Check who's got max single play score
        max_entry_scores = dict.fromkeys(candidates, 0)
        for entry in cast("list[ScrabbleEntry]", self.getRounds()):
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


class ScrabbleEntry(GenericEntry):
    """A single Scrabble scoring entry carrying its per-bonus tallies."""

    def __init__(self, numround: int) -> None:
        super().__init__(numround)
        self.bonuses = {"dl": 0, "tl": 0, "dw": 0, "tw": 0, "bingo": 0}

    def addExtraInfo(self, player: str, extras: dict) -> None:
        """Record the bonus tallies for this entry from ``extras``."""
        try:
            self.bonuses = extras
        except KeyError:
            pass

    def getBonuses(self) -> dict:
        return self.bonuses

    def __repr__(self) -> str:
        return f"{self.getNumEntry()}: {self.getPlayer()} - {self.getPlayerScore()} | {self.getBonuses()}"
