"""Skull King match model: Pocha with configurable rounds and bonus scoring."""

from __future__ import annotations

from collections.abc import KeysView, Sequence
from typing import ClassVar

from core.engine.db import db
from games.pocha.model import PochaMatch


class SkullKingMatch(PochaMatch):
    """Pocha variant adding selectable round sequences and bonus scoring modes."""

    roundModes: ClassVar[dict] = {
        "standard_rounds": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
        "even": [2, 4, 6, 8, 10],
        "brawl": [6, 7, 8, 9, 10],
        "skirmish": 5 * [5],
        "barrage": 10 * [10],
        "whirlpool": [9, 7, 5, 3, 1],
    }
    scoringModes: ClassVar[dict] = {
        "classic_scoring": {
            "skullking": {"bonus": 50, "reps": 1},
            "pirate": {"bonus": 20, "reps": 6},
        },
        "standard_scoring": {
            "skullking": {"bonus": 40, "reps": 1},
            "pirate": {"bonus": 20, "reps": 6},
            "mermaid": {"bonus": 20, "reps": 2},
            "loot": {"bonus": 20, "reps": 2},
            "fourteen": {"bonus": 10, "reps": 3},
            "blackfourteen": {"bonus": 1, "reps": 1},
            "roatan": {"bonus": 10, "reps": 2},
        },
    }
    scoringModes["rascal_scoring"] = scoringModes["standard_scoring"] | {
        "cannonball": {"bonus": 0, "reps": 1}
    }

    def __init__(self, players: Sequence[str] = ()) -> None:
        super().__init__(players)
        self.game = "Skull King"
        self.dealingp = 1
        self.scoringMode = "classic_scoring"
        if len(self.players) > 6:
            self.scoringMode = "standard_scoring"
        self.setRoundMode("standard_rounds")

    def getBonus(self, bonus_name: str) -> int:
        try:
            return self.scoringModes[self.scoringMode][bonus_name]["bonus"]
        except KeyError:
            return 0

    def getBonusReps(self, bonus_name: str) -> int:
        try:
            return self.scoringModes[self.scoringMode][bonus_name]["reps"]
        except KeyError:
            return 0

    def listBonusTypes(self) -> KeysView[str]:
        return self.scoringModes[self.scoringMode].keys()

    def listScoringModes(self) -> list[str]:
        """List the scoring modes available for the current player count."""
        return [
            sm
            for sm in self.scoringModes
            if len(self.players) <= 6
            or len(self.players) > 7
            and sm != "classic_scoring"
        ]

    @classmethod
    def listRoundModes(cls) -> KeysView[str]:
        return cls.roundModes.keys()

    def getScoringMode(self) -> str:
        return self.scoringMode

    def setScoringMode(self, smode: str) -> None:
        """Set the active scoring mode, rejecting unknown names."""
        if smode not in self.scoringModes:
            raise ValueError(
                f"Invalid Scoring Mode type {smode}. Possible values are: {', '.join(self.scoringModes)}"
            )
        self.scoringMode = smode

    def getRoundMode(self) -> str:
        return self.roundMode

    def getRoundSequence(self, mode: str | None = None) -> list[int]:
        """Return the hand-size sequence for ``mode`` (default: current mode)."""
        if mode is None:
            mode = self.roundMode
        return self.roundModes[mode]

    def setRoundMode(self, rmode: str) -> None:
        """Set the round mode and derive the hand sequence and round count."""
        if rmode not in self.roundModes:
            raise ValueError(
                f"Invalid Round Mode type {rmode}. Possible values are: {', '.join(self.roundModes.keys())}"
            )
        self.roundMode = rmode
        self.hands = self.roundModes[self.roundMode]
        self.maxRounds = len(self.hands)

    def getHands(self) -> list[int]:
        return self.roundModes[self.roundMode]

    def resumeMatch(self, idMatch: int) -> bool:
        """Reload the base match plus the persisted scoring and round modes."""
        if not super().resumeMatch(idMatch):
            return False

        cur = db.execute(
            "SELECT value FROM MatchExtras WHERE idMatch =? and key='scoringMode';",
            (idMatch,),
        )
        if cur:
            row = cur.fetchone()
            if row:
                self.scoringMode = row["value"]

        cur = db.execute(
            "SELECT value FROM MatchExtras WHERE idMatch =? and key='roundMode';",
            (idMatch,),
        )
        if cur:
            row = cur.fetchone()
            if row:
                self.roundMode = row["value"]

        for player in self.getPlayers():
            self.playerStart(player)

        return True

    def flushToDB(self) -> None:
        """Persist the base match plus the scoring and round modes."""
        super().flushToDB()
        db.execute(
            "INSERT OR REPLACE INTO MatchExtras (idMatch,key,value) "
            "VALUES (?,'scoringMode',?);",
            (self.idMatch, self.scoringMode),
        )
        db.execute(
            "INSERT OR REPLACE INTO MatchExtras (idMatch,key,value) "
            "VALUES (?,'roundMode',?);",
            (self.idMatch, self.roundMode),
        )
