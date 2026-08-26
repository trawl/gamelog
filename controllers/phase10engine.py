from typing import cast

from controllers.baseengine import RoundGameEngine, readInput
from controllers.db import db
from controllers.statsengine import ParticularStatsEngine, StatsEngine
from model.phase10 import Phase10Match


class Phase10Engine(RoundGameEngine):
    def __init__(self):
        if not hasattr(self, "game"):
            self.game = "Phase10"
        super().__init__()

    def getPhases(self):
        return cast(Phase10Match, self.match).getPhases()

    def getRemainingPhasesFromPlayer(self, player):
        remaining = list(range(1, 11))
        if (
            self.match is not None
            and player in cast("Phase10Match", self.match).phasesCleared
        ):
            for phase in cast("Phase10Match", self.match).phasesCleared[player]:
                remaining.remove(phase)
        return remaining

    def getCompletedPhasesFromPlayer(self, player):
        if player in cast("Phase10Match", self.match).phasesCleared:
            return cast("Phase10Match", self.match).phasesCleared[player]
        else:
            return []

    def hasPhaseCompleted(self, player, phase):
        return phase in self.getCompletedPhasesFromPlayer(player)

    def hasPhaseRemaining(self, player, phase):
        return phase in self.getRemainingPhasesFromPlayer(player)

    def printExtraPlayerStats(self, player):
        print(f"Phases completed: {self.getCompletedPhasesFromPlayer(player)}")

    def printExtraStats(self):
        print("Phases:")
        print("====================")
        for n, phase in enumerate(self.getPhases(), start=1):
            print(f"  Phase {n:02}: {phase}")
        print("====================")
        print("  Quick desc: s=set, r=run, c=colour, cr=colour run")
        print("  Example: 2s4 = 2 sets of 4 cards")

    def runStubRoundPlayer(self, player, winner):
        score = 0
        cleared = 1
        if self.getPhasesInOrderFlag():
            try:
                a_phase = self.getCompletedPhasesFromPlayer(player)[-1] + 1
            except IndexError:
                a_phase = 1
        else:
            a_phase = readInput(
                f"{player} aimed phase number: ",
                int,
                lambda x: x > 0 and self.hasPhaseRemaining(player, x),
                "Sorry, phase not valid or already completed.",
            )
        if winner != player:
            score = readInput(
                f"{player} round score: ",
                int,
                lambda x: x > 0,
                "Sorry, invalid score number.",
            )
            if score >= 50:
                cleared = readInput(
                    f"Did {player} complete phase {a_phase}?[1/0]: ",
                    int,
                    lambda x: x in [0, 1],
                )
        self.addRoundInfo(
            player, score, {"aimedPhase": a_phase, "isCompleted": cleared}
        )

    def extraStubConfig(self):
        pio = readInput("Follow phases in order? [1/0]: ", int, lambda x: x in (0, 1))
        self.setPhasesInOrderFlag(bool(pio))

    def getPhasesInOrderFlag(self):
        return cast("Phase10Match", self.match).getPhasesInOrderFlag()

    def setPhasesInOrderFlag(self, flag):
        cast("Phase10Match", self.match).setPhasesInOrderFlag(flag)


class Phase10MasterEngine(Phase10Engine):
    def __init__(self):
        if not hasattr(self, "game"):
            self.game = "Phase10Master"
        super().__init__()


if __name__ == "__main__":
    game = readInput(
        "Game to play (Phase10/Phase10Master): ",
        str,
        lambda x: x in ["Phase10", "Phase10Master"],
    )
    if game == "Phase10":
        pe = Phase10Engine()
    else:
        pe = Phase10MasterEngine()
    pe.gameStub()


class Phase10StatsQueries:
    worst_phases = """
        SELECT game, nick, min(pc) AS min_phases from (
            SELECT Match.Game_name as game,Match.idMatch AS match,
                rs.nick AS nick ,count(value) AS pc
            FROM RoundStatistics AS rs,Match
            WHERE rs.idMatch = Match.idMatch
                AND key = "PhaseCompleted"
                AND value <> 0
                AND state = 1
            GROUP BY game, Match.idMatch, rs.nick
        ) AS temp
        GROUP BY game, nick
    """
    damned_phases = """
        SELECT Game_name AS game, nick AS player, value AS phase,
            COUNT(value) AS times
        FROM Match,RoundStatistics
        WHERE
            Match.idMatch = RoundStatistics.idMatch
            AND key="PhaseAimed"
        GROUP BY game, player, phase
        ORDER BY game, player, phase
    """


class Phase10StatsEngine(StatsEngine):
    def __init__(self):
        super().__init__()
        q = Phase10StatsQueries()
        self._worst_phases = q.worst_phases
        self._damned_phases = q.damned_phases

    def update(self, players=None):
        super().update()
        self.wphases = db.queryDict(self._worst_phases)
        for row in self.wphases:
            game = row["game"]
            player = row["nick"]
            if self.generalplayerstats:
                for r2 in self.generalplayerstats:
                    if r2["nick"] == player and r2["game"] == game:
                        r2["min_phases"] = row["min_phases"]
                        break

        rows = db.queryDict(self._damned_phases)
        attempts = {}
        for row in rows:
            if row["game"] not in attempts:
                attempts[row["game"]] = {}
            if row["player"] not in attempts[row["game"]]:
                attempts[row["game"]][row["player"]] = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
            attempts[row["game"]][row["player"]][int(row["phase"]) - 1] = row["times"]
        if self.generalplayerstats:
            for row in self.generalplayerstats:
                if row["game"] in attempts and row["nick"] in attempts[row["game"]]:
                    times = attempts[row["game"]][row["nick"]]
                    max_times = max(times)
                    row["damned_phase"] = times.index(max_times) + 1


class Phase10ParticularStatsEngine(Phase10StatsEngine, ParticularStatsEngine):
    def updatePlayers(self, players):
        super().updatePlayers(players)
        if players:
            q = Phase10StatsQueries()
            self._worst_phases = q.worst_phases.replace(
                "WHERE", "WHERE {} AND".format("Match." + self._newclause)
            )
            self._damned_phases = q.damned_phases.replace(
                "WHERE", "WHERE {} AND".format("Match." + self._newclause)
            )
