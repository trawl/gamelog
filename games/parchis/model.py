"""Parchis classic board game model."""

from __future__ import annotations

from collections.abc import Sequence
from typing import cast

from core.model.base import GenericEntry, GenericRoundMatch


class ParchisMatch(GenericRoundMatch):
    """Entry-based match for parchis, won by the first to get 4 tokens to the goal."""

    def __init__(self, players: Sequence[str] = ()) -> None:
        super().__init__(players)
        self.game = "Parchis"
        self.top = 4
        self.dealingp = 0

    def computeWinner(self) -> None:
        """Once any player reaches ``top``, the highest total score wins."""
        self.winner = next(
            (key for key, value in self.totalScores.items() if value == 4), None
        )

    def createRound(self, numround: int) -> GenericEntry:
        return ParchisEntry(numround)

    def getTop(self) -> int:
        return self.top

    def setTop(self, top: int) -> None:
        self.top = top

    def getKillsTally(self) -> dict[str, dict[str, int]]:
        """Generate a matrix of with the kill tally."""
        kill_tally = {killer: dict.fromkeys(self.players, 0) for killer in self.players}
        for entry in cast("list[ParchisEntry]", self.rounds):
            for kill in entry.getKills():
                kill_tally[entry.getPlayer()][kill] += 1
        return kill_tally

    def getComboTally(self) -> dict[str, int]:
        """Return the number of combos per player.

        A combo is any action past the first in a single entry: goals and
        kills both count, so an entry with score 2 and 2 kills is 3 combos
        (4 actions, minus the first).
        """
        combo_tally = dict.fromkeys(self.players, 0)
        for entry in cast("list[ParchisEntry]", self.rounds):
            combo_tally[entry.getPlayer()] += max(
                0,
                entry.getPlayerScore(entry.getPlayer()) + len(entry.getKills()) - 1,
            )
        return combo_tally


class ParchisEntry(GenericEntry):
    """A Parchis entry with extras."""

    def __init__(self, numround: int) -> None:
        super().__init__(numround)
        self.kills: list[str] = []

    def addExtraInfo(self, player: str, extras: dict) -> None:
        """Record the scoring kind for this entry from ``extras``."""
        try:
            if extras["kills"]:
                self.kills = extras["kills"]
        except KeyError:
            pass

    def getExtraEvents(self, player: str) -> list[tuple[str, str | None, str | None]]:
        """One ordered 'kill' event per victim, for persistence as RoundEvents."""
        if player != self.getPlayer():
            return []
        return [("kill", victim, None) for victim in self.kills]

    def addExtraEvent(
        self, player: str, eventType: str, target: str | None, value: str | None
    ) -> None:
        """Restore a persisted kill event for this entry."""
        if eventType == "kill" and target:
            self.kills.append(target)

    def getKills(self) -> list[str]:
        return self.kills
