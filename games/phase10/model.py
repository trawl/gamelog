"""Phase 10 match and round models."""

from __future__ import annotations

import logging
import random
from collections.abc import Sequence
from typing import cast

from core.engine.db import db
from core.model.base import GenericRound, GenericRoundMatch

logger = logging.getLogger(__name__)

phases = {
    "Phase10": [
        "2s3",
        "1s3 1r4",
        "1s4 1r4",
        "1r7",
        "1r8",
        "1r9",
        "2s4",
        "1c7",
        "1s5 1s2",
        "1s5 1s3",
    ],
    "Phase10Master": [
        "4s2",
        "1c6",
        "1s4 1r4",
        "1r8",
        "1c7",
        "1r9",
        "2s4",
        "1cr4 1s3",
        "1s5 1s3",
        "1s5 1cr3",
    ],
}


class Phase10Match(GenericRoundMatch):
    """Round-based match for Phase 10, tracking phases cleared per player."""

    def __init__(self, players: Sequence[str] = ()) -> None:
        super().__init__(players)
        self.game = "Phase10"
        self.phasesinorder = True
        self.phasesCleared: dict[
            str, list[int]
        ] = {}  # player -> list of phases cleared

    def playerStart(self, player: str) -> None:
        self.phasesCleared[player] = []

    def playerAddRound(self, player: str, rnd: GenericRound) -> None:
        """Record the phase cleared by ``player`` in ``rnd``, if any."""
        rnd = cast("Phase10Round", rnd)
        if rnd.completedPhase[player]:
            self.phasesCleared[player].append(rnd.completedPhase[player])

    def deleteRound(self, nrnd: int) -> None:
        """Drop the round's cleared phases before removing it from the match."""
        try:
            rnd = cast("Phase10Round", self.rounds[nrnd - 1])
        except KeyError:
            return
        for player in self.getPlayers():
            if rnd.completedPhase[player]:
                self.phasesCleared[player].remove(rnd.completedPhase[player])
        super().deleteRound(nrnd)

    def computeWinner(self) -> None:
        """Pick the winner among players who cleared all 10 phases.

        Ties break on lowest total score, then on lowest last-round score,
        then at random.
        """
        playersIn10 = []
        for p, pc in self.phasesCleared.items():
            if len(pc) == 10:
                playersIn10.append(p)
        if playersIn10:
            # Ok, there are some players with all phases completed
            self.winner = None
            wcscores = {}
            # Let's see their scores, and select the ones with the lowest one
            for p in playersIn10:
                if self.totalScores[p] not in wcscores:
                    wcscores[self.totalScores[p]] = []
                wcscores[self.totalScores[p]].append(p)

            #             try:
            #                 minScore=sys.maxint
            #             except AttributeError:
            # Here we have the players with all phases completed and with the
            # lowest score in case of draw, the player with less points in the
            # last round is the winner
            candidates = wcscores[min(wcscores)]
            if len(candidates) == 1:
                self.winner = candidates[0]
                return

            min_last_round_score = min([self.rounds[-1].score[n] for n in candidates])
            last_round_candidates = [
                n
                for n in candidates
                if self.rounds[-1].score[n] == min_last_round_score
            ]

            if len(last_round_candidates) == 1:
                self.winner = last_round_candidates[0]
                return

            self.winner = random.choice(last_round_candidates)

    def createRound(self, numround: int) -> GenericRound:
        return Phase10Round(numround)

    def resumeMatch(self, idMatch: int) -> bool:
        """Reload the base match plus the phases-in-order flag and cleared phases."""
        if not super().resumeMatch(idMatch):
            return False

        cur = db.execute(
            "SELECT value FROM MatchExtras WHERE idMatch =? and key='PhasesInOrder';",
            (idMatch,),
        )
        if cur:
            row = cur.fetchone()
            if row:
                self.phasesinorder = bool(int(row["value"]))

        for player in self.getPlayers():
            if player not in self.phasesCleared:
                self.phasesCleared[player] = []

        return True

    def resumeExtraInfo(self, player: str, key: str, value: str | int) -> dict:
        """Decode a persisted PhaseAimed/PhaseCompleted statistic row."""
        if player not in self.phasesCleared:
            self.phasesCleared[player] = []
        extra = {}
        if key == "PhaseAimed":
            extra["aimedPhase"] = int(value)
        if key == "PhaseCompleted":
            value = int(value)
            if value > 0:
                extra["isCompleted"] = True
                self.phasesCleared[player].append(value)
            else:
                extra["isCompleted"] = False
        return extra

    def flushToDB(self) -> None:
        """Persist the base match plus the phases-in-order flag and round stats."""
        super().flushToDB()
        if self.phasesinorder:
            inorderflag = 1
        else:
            inorderflag = 0
        db.execute(
            "INSERT OR REPLACE INTO MatchExtras (idMatch,key,value) "
            "VALUES (?,'PhasesInOrder',?);",
            (self.idMatch, inorderflag),
        )
        for rnd in cast("list[Phase10Round]", self.rounds):
            for player in rnd.score.keys():  # noqa: SIM118
                db.execute(
                    "INSERT OR REPLACE INTO RoundStatistics "
                    "(idMatch,nick,idRound,key,value) "
                    "VALUES (?,?,?,'PhaseAimed',?);",
                    (self.idMatch, player, rnd.getNumRound(), rnd.aimedPhase[player]),
                )
                db.execute(
                    "INSERT OR REPLACE INTO RoundStatistics "
                    "(idMatch,nick,idRound,key,value) "
                    "VALUES (?,?,?,'PhaseCompleted',?);",
                    (
                        self.idMatch,
                        player,
                        rnd.getNumRound(),
                        rnd.completedPhase[player],
                    ),
                )

    def getPhasesInOrderFlag(self) -> bool:
        return self.phasesinorder

    def setPhasesInOrderFlag(self, flag: bool) -> None:
        if flag not in [True, False]:
            return
        logger.debug("Setting phases-in-order flag to %s", flag)
        self.phasesinorder = flag

    def getPhases(self) -> list[str]:
        return phases[self.game]


class Phase10Round(GenericRound):
    """A Phase 10 round: adds each player's aimed and completed phase."""

    def __init__(self, numround: int) -> None:
        GenericRound.__init__(self, numround)
        self.completedPhase: dict[str, int] = {}
        self.aimedPhase: dict[str, int] = {}

    def addExtraInfo(self, player: str, extras: dict) -> None:
        """Store the player's aimed phase and whether it was completed."""
        try:
            self.aimedPhase[player] = extras["aimedPhase"]
            if extras["isCompleted"]:
                self.completedPhase[player] = extras["aimedPhase"]
            else:
                self.completedPhase[player] = 0
        except KeyError:
            pass

    def getPlayerAimedPhase(self, player: str) -> int:
        try:
            return self.aimedPhase[player]
        except KeyError:
            return 0

    def getPlayerCompletedPhase(self, player: str) -> int:
        try:
            return self.completedPhase[player]
        except KeyError:
            return 0


class Phase10MasterMatch(Phase10Match):
    """Phase 10 Master variant, using the harder Master phase list."""

    def __init__(self, players: Sequence[str] = ()) -> None:
        super().__init__(players)
        self.game = "Phase10Master"
