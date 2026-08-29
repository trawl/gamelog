"""Ratuki match model."""

from __future__ import annotations

from collections.abc import Sequence

from core.engine.db import db
from core.model.base import GenericRoundMatch


class RatukiMatch(GenericRoundMatch):
    """Round-based match for Ratuki, won by reaching a target ``top`` score."""

    def __init__(self, players: Sequence[str] = ()) -> None:
        super().__init__(players)
        self.game = "Ratuki"
        self.top = 100

    def resumeMatch(self, idMatch: int) -> bool:
        """Reload the base match, re-seed per-player state and the target score."""
        if not super().resumeMatch(idMatch):
            return False

        for player in self.getPlayers():
            self.playerStart(player)

        cur = db.execute(
            "SELECT value FROM MatchExtras WHERE idMatch =? and key='Top';",
            (idMatch,),
        )
        row = cur.fetchone()
        if row:
            self.top = int(row["value"])

        return True

    def computeWinner(self) -> None:
        """Set the winner as the highest scorer at or above the target score."""
        winner = None
        maxscore = self.top
        for player, score in self.totalScores.items():
            if score >= maxscore:
                winner = player
                maxscore = score

        if winner is not None:
            self.winner = winner

    def getTop(self) -> int:
        return self.top

    def setTop(self, top: int) -> None:
        if top <= 0:
            return
        self.top = top

    def flushToDB(self) -> None:
        """Persist the base match plus the target ``top`` score."""
        super().flushToDB()
        db.execute(
            "INSERT OR REPLACE INTO MatchExtras (idMatch,key,value) "
            "VALUES (?,'Top',?);",
            (self.idMatch, self.top),
        )
