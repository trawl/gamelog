"""Skull King game engine, scoring logic and its statistics engines."""

from __future__ import annotations

from collections.abc import KeysView
from typing import cast

from games.pocha.engine import (
    PochaEngine,
    PochaParticularStatsEngine,
    PochaStatsEngine,
)
from games.skullking.model import SkullKingMatch


class SkullKingEngine(PochaEngine):
    """Pocha engine specialised with Skull King's bonus and scoring rules."""

    def __init__(self) -> None:
        if not hasattr(self, "game"):
            self.game = "Skull King"
        super().__init__()
        self.hands = cast("SkullKingMatch", self.match).getHands()

    def getScoringMode(self) -> str:
        return cast("SkullKingMatch", self.match).getScoringMode()

    def getRoundMode(self) -> str:
        return cast("SkullKingMatch", self.match).getRoundMode()

    def getRoundSequence(self, mode: str | None = None) -> list[int]:
        return cast("SkullKingMatch", self.match).getRoundSequence(mode)

    def setScoringMode(self, scoring_mode: str) -> None:
        cast("SkullKingMatch", self.match).setScoringMode(scoring_mode)

    def setRoundMode(self, round_mode: str) -> None:
        cast("SkullKingMatch", self.match).setRoundMode(round_mode)
        self.hands = cast("SkullKingMatch", self.match).getHands()

    def listBonusTypes(self) -> KeysView[str]:
        return cast("SkullKingMatch", self.match).listBonusTypes()

    def getBonusReps(self, bonus_name: str) -> int:
        return cast("SkullKingMatch", self.match).getBonusReps(bonus_name)

    def listScoringModes(self) -> list[str]:
        return cast("SkullKingMatch", self.match).listScoringModes()

    def listRoundModes(self) -> KeysView[str]:
        return cast("SkullKingMatch", self.match).listRoundModes()

    def computePlayerBonuses(self, bonuses: dict[str, int]) -> int:
        """Sum a player's bonus points across every active bonus type."""
        points = 0
        for btype in cast("SkullKingMatch", self.match).listBonusTypes():
            try:
                points += bonuses[btype] * cast("SkullKingMatch", self.match).getBonus(
                    btype
                )
            except KeyError:
                pass
        return points

    def computePlayerScoreClassic(
        self, expected: int, won: int, bonuses: dict[str, int]
    ) -> int:
        """Score a player's round under the classic/standard Skull King rules."""
        if expected == 0 and won == 0:
            return self.getNumRound() * 10 + self.computePlayerBonuses(bonuses)
        if expected == 0 and won != 0:
            return self.getNumRound() * -10
        if expected == won:
            return won * 20 + self.computePlayerBonuses(bonuses)
        try:
            roatan_penalty = bonuses["roatan"] * cast(
                "SkullKingMatch", self.match
            ).getBonus("roatan")
        except KeyError:
            roatan_penalty = 0
        return -10 * abs(expected - won) - roatan_penalty

    def computePlayerScoreRascal(
        self, expected: int, won: int, bonuses: dict[str, int]
    ) -> int:
        """Score a player's round under the Rascal (cannonball) rules."""
        diff = abs(won - expected)
        cannonball = "cannonball" in bonuses and bonuses["cannonball"]
        if cannonball:
            score = self.getNumRound() * 15 + self.computePlayerBonuses(bonuses)
        else:
            score = self.getNumRound() * 10 + self.computePlayerBonuses(bonuses)
        if diff == 0:
            return score
        if diff == 1 and not cannonball:
            return score // 2
        return 0

    def computePlayerScore(
        self, expected: int, won: int, bonuses: dict[str, int]
    ) -> int:
        """Dispatch to the scoring routine for the active scoring mode."""
        if self.getScoringMode() in ("classic_scoring", "standard_scoring"):
            return self.computePlayerScoreClassic(expected, won, bonuses)
        elif self.getScoringMode() == "rascal_scoring":
            return self.computePlayerScoreRascal(expected, won, bonuses)
        raise ValueError(f"Unknown scoring mode {self.getScoringMode()}")


class SkullKingStatsQueries:
    """SQL query templates for Skull King statistics."""

    hitsQuery = """
    SELECT player, max(hitp) as "max_hits", min(hitp) as "min_hits", round(avg(hitp),2) as "avg_hits" from (
        SELECT Round.idMatch as idm, Round.nick as "player",
                COUNT(Round.idRound) as "hits", CASE WHEN
        COALESCE(MatchExtras.value, 'standard_rounds') IN ('standard_rounds', 'barrage') THEN 10
            ELSE 5 END AS hands,     ROUND(
            COUNT(Round.idRound) * 100.0 /
            CASE
                WHEN COALESCE(MatchExtras.value, 'standard_rounds')
                    IN ('standard_rounds', 'barrage')
                THEN 10
                ELSE 5
            END,
            2
        ) AS hitp
            FROM Round,Match LEFT JOIN MatchExtras ON MatchExtras.idMatch = Match.idMatch
        AND MatchExtras.key = 'roundMode'
            WHERE Match.idMatch = Round.idMatch
                and Match.state = 1
                and Game_name="Skull King"
                and Round.score > 0
            group by idm, player
    ) as tmp
    group by player
    order by player
    """

    extremeRounds = """
    SELECT Round.nick as "player", max(score) as "max_round_score",
        min(score) as "min_round_score"
    FROM Round,Match
    WHERE Match.idMatch = Round.idMatch
        and Match.state = 1
        and Game_name="#GAMENAME#"
    group by player
   """


class SkullKingStatsEngine(PochaStatsEngine):
    """App-wide Skull King statistics, using its round-aware hit query."""

    def __init__(self) -> None:
        super().__init__()
        self.game = "Skull King"
        self.define_queries()

    def define_queries(self) -> None:
        """Bind the game name into the Skull King query templates."""
        q = SkullKingStatsQueries()
        self._hitsQuery = q.hitsQuery.replace("#GAMENAME#", self.game)
        self._extremeRounds = q.extremeRounds.replace("#GAMENAME#", self.game)


class SkullKingParticularStatsEngine(PochaParticularStatsEngine):
    """Skull King statistics restricted to an exact set of players."""

    def __init__(self) -> None:
        super().__init__()
        self.game = "Skull King"
        self.define_queries()

    def define_queries(self) -> None:
        """Bind the game name into the Skull King query templates."""
        q = SkullKingStatsQueries()
        self._hitsQuery = q.hitsQuery.replace("#GAMENAME#", self.game)
        self._extremeRounds = q.extremeRounds.replace("#GAMENAME#", self.game)


if __name__ == "__main__":
    re = SkullKingEngine()
    re.gameStub()
