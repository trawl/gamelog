"""Parchis play-time and statistics engines."""

from __future__ import annotations

from typing import cast

from core.engine.base import EntryGameEngine, readInput
from core.engine.db import db
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


class ParchisStatsQueries:
    """SQL query templates for Parchis kill and combo records.

    Kills are sourced straight from RoundEvents. A combo is any action past
    the first in a single entry (goals and kills both count, per
    ``ParchisMatch.getComboTally``), computed per entry as
    ``MAX(0, score + kills - 1)`` — kills counted via a LEFT JOIN so an entry
    with no RoundEvents rows still contributes 0, not NULL.

    Each record comes in two shapes, mirroring the columns Pocha/Skull King
    add to the generic stats tables: one row per player (that player's best
    ever, merged into ``generalplayerstats`` by nick) and one row per player
    count (the best achieved in a match with that many players, merged into
    ``generalmatchstats`` by nplayers — the same grouping ``maxscore`` uses).
    """

    playerMaxKillsQuery = """
    SELECT nick as player, MAX(killcount) as max_kills
    FROM (
        SELECT RoundEvents.nick as nick, RoundEvents.idMatch as idMatch,
            COUNT(*) as killcount
        FROM RoundEvents, Match
        WHERE Match.idMatch = RoundEvents.idMatch
            and Match.state=1
            and Game_name='Parchis'
            and eventType='kill'
        GROUP BY RoundEvents.idMatch, RoundEvents.nick
    )
    GROUP BY nick
    """

    matchMaxKillsQuery = """
    SELECT nplayers, MAX(killcount) as max_kills
    FROM (
        SELECT RoundEvents.nick as nick, RoundEvents.idMatch as idMatch,
            COUNT(*) as killcount
        FROM RoundEvents, Match
        WHERE Match.idMatch = RoundEvents.idMatch
            and Match.state=1
            and Game_name='Parchis'
            and eventType='kill'
        GROUP BY RoundEvents.idMatch, RoundEvents.nick
    ) as perplayer
    JOIN (SELECT idMatch, COUNT(nick) as nplayers FROM MatchPlayer GROUP BY idMatch) as np
        ON np.idMatch = perplayer.idMatch
    GROUP BY nplayers
    """

    playerMaxComboQuery = """
    SELECT nick as player, MAX(totalcombo) as max_combo
    FROM (
        SELECT idMatch, nick, SUM(combo) as totalcombo
        FROM (
            SELECT Round.idMatch as idMatch,
                Round.nick as nick,
                max(0, Round.score + COUNT(RoundEvents.seq) - 1) as combo
            FROM Match
            JOIN Round ON Match.idMatch = Round.idMatch
            LEFT JOIN RoundEvents
                ON RoundEvents.idMatch = Round.idMatch
                and RoundEvents.idRound = Round.idRound
                and RoundEvents.nick = Round.nick
                and RoundEvents.eventType = 'kill'
            WHERE Match.state = 1 and Game_name='Parchis'
            GROUP BY Round.idMatch,Round.idRound,Round.nick
        )
        GROUP BY idMatch, nick
    )
    GROUP BY nick
    """

    matchMaxComboQuery = """
    SELECT nplayers, MAX(totalcombo) as max_combo
    FROM (
        SELECT idMatch, nick, SUM(combo) as totalcombo
        FROM (
            SELECT Round.idMatch as idMatch,
                Round.nick as nick,
                max(0, Round.score + COUNT(RoundEvents.seq) - 1) as combo
            FROM Match
            JOIN Round ON Match.idMatch = Round.idMatch
            LEFT JOIN RoundEvents
                ON RoundEvents.idMatch = Round.idMatch
                and RoundEvents.idRound = Round.idRound
                and RoundEvents.nick = Round.nick
                and RoundEvents.eventType = 'kill'
            WHERE Match.state = 1 and Game_name='Parchis'
            GROUP BY Round.idMatch,Round.idRound,Round.nick
        )
        GROUP BY idMatch, nick
    ) as perplayer
    JOIN (SELECT idMatch, COUNT(nick) as nplayers FROM MatchPlayer GROUP BY idMatch) as np
        ON np.idMatch = perplayer.idMatch
    GROUP BY nplayers
    """


class ParchisStatsEngine(StatsEngine):
    """Adds max-kills and max-combo columns to the player and match tables."""

    def __init__(self) -> None:
        super().__init__()
        self.game = "Parchis"
        q = ParchisStatsQueries()
        self._playerMaxKillsQuery = q.playerMaxKillsQuery
        self._matchMaxKillsQuery = q.matchMaxKillsQuery
        self._playerMaxComboQuery = q.playerMaxComboQuery
        self._matchMaxComboQuery = q.matchMaxComboQuery

    def update(self, players: list[str] | None = None) -> None:
        """Refresh base statistics, then merge in the Parchis columns."""
        # `players` must reach ParticularStatsEngine.update() through MRO, or
        # the player filter it sets up in updatePlayers() is silently dropped.
        super().update(players)

        playerMaxKills = db.queryDict(
            self._playerMaxKillsQuery, self._bound_params(self._playerMaxKillsQuery)
        )
        playerMaxCombo = db.queryDict(
            self._playerMaxComboQuery, self._bound_params(self._playerMaxComboQuery)
        )
        if self.generalplayerstats:
            for row in playerMaxKills:
                for r2 in self.generalplayerstats:
                    if r2["nick"] == row["player"] and r2["game"] == self.game:
                        r2["max_kills"] = row["max_kills"]
                        break
            for row in playerMaxCombo:
                for r2 in self.generalplayerstats:
                    if r2["nick"] == row["player"] and r2["game"] == self.game:
                        r2["max_combo"] = row["max_combo"]
                        break

        matchMaxKills = db.queryDict(
            self._matchMaxKillsQuery, self._bound_params(self._matchMaxKillsQuery)
        )
        matchMaxCombo = db.queryDict(
            self._matchMaxComboQuery, self._bound_params(self._matchMaxComboQuery)
        )
        if self.generalmatchstats:
            for row in matchMaxKills:
                for r2 in self.generalmatchstats:
                    if r2["nplayers"] == row["nplayers"] and r2["game"] == self.game:
                        r2["max_kills"] = row["max_kills"]
                        break
            for row in matchMaxCombo:
                for r2 in self.generalmatchstats:
                    if r2["nplayers"] == row["nplayers"] and r2["game"] == self.game:
                        r2["max_combo"] = row["max_combo"]
                        break


class ParchisParticularStatsEngine(ParchisStatsEngine, ParticularStatsEngine):
    """Parchis kill/combo columns restricted to an exact set of players."""

    def updatePlayers(self, players: list[str] | None) -> None:
        """Splice the player filter into the Parchis column queries."""
        super().updatePlayers(players)
        if players:
            q = ParchisStatsQueries()
            clause = "WHERE {} AND".format("Match." + self._newclause)
            self._playerMaxKillsQuery = q.playerMaxKillsQuery.replace("WHERE", clause)
            self._matchMaxKillsQuery = q.matchMaxKillsQuery.replace("WHERE", clause)
            self._playerMaxComboQuery = q.playerMaxComboQuery.replace("WHERE", clause)
            self._matchMaxComboQuery = q.matchMaxComboQuery.replace("WHERE", clause)


if __name__ == "__main__":
    re = ParchisEngine()
    re.gameStub()
