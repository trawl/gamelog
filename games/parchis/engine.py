"""Parchis play-time and statistics engines."""

from __future__ import annotations

from typing import cast

from core.engine.base import EntryGameEngine, readInput
from core.engine.stats import ParticularStatsEngine, StatsEngine
from games.parchis.model import ParchisMatch


class ParchisEngine(EntryGameEngine):
    """Entry-scored engine driving a Carcassonne match."""

    def __init__(self) -> None:
        if not hasattr(self, "game"):
            self.game = "Parchis"
        super().__init__()

    def runStubRoundPlayer(self, player: str, winner: str | None = None) -> None:
        """CLI harness: read one player's score and kills, then record it."""
        kills = []
        score = readInput(
            f"{player} goals: ",
            int,
            lambda x: 4 >= x >= 0,
            "Sorry, invalid score number.",
        )
        if not score:
            errmsg = "Sorry, invalid kill [{}]".format(",".join(self.getListPlayers()))
            more_kills = True
            while more_kills:
                kill = readInput(
                    "Kill: ", str, lambda x: x in [""] + self.getListPlayers(), errmsg
                )
                if kill:
                    kills.append(kill)
                else:
                    more_kills = False
        self.addEntry(player, score, {"kills": kills})

    def getKillsTally(self) -> dict[str, dict[str, int]]:
        """Generate a matrix of with the kill tally."""
        return cast(ParchisMatch, self.match).getKillsTally()

    def getComboTally(self) -> dict[str, int]:
        """Return the number of combos per player."""
        return cast(ParchisMatch, self.match).getComboTally()


class ParchisStatsEngine(StatsEngine):
    """Adds Parchis custom record statistics."""

    pass


class ParchisParticularStatsEngine(ParchisStatsEngine, ParticularStatsEngine):
    """Parchis record statistics restricted to an exact set of players."""

    pass


if __name__ == "__main__":
    re = ParchisEngine()
    re.gameStub()
