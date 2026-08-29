"""Statistics engines: aggregate match/player figures straight from SQLite.

``StatsEngine`` computes app-wide figures; ``ParticularStatsEngine`` restricts
them to matches played by an exact set of players. Games may subclass either to
add their own game-specific statistics.
"""

from __future__ import annotations

from core.engine.db import GameLogDB, db


class StatsEngine:
    """App-wide game, match and player statistics, queried on demand."""

    _lastwinnerquery = """
    SELECT Game_name AS game,
        nick AS lastwinner,
        DATETIME(finished) AS lastwinnerdate
    FROM Match JOIN MatchPlayer USING(idMatch)
    WHERE winner=1
    GROUP BY game
    HAVING MAX(strftime('%s', finished))
    ORDER BY game,finished;
    """

    _generalmatchstatsquery = """
     SELECT game,
        nplayers,
        TIME(MAX(elapsed),'unixepoch') AS maxduration,
        TIME(MIN(elapsed),'unixepoch') AS minduration,
        TIME(AVG(elapsed),'unixepoch') AS avgduration,
        MAX(CAST(maxscore as integer)) AS maxscore,
        MIN(CAST(minscore as integer)) AS minscore,
        CAST(ROUND(AVG(CAST(avgscore as integer))) as integer) AS avgscore
    FROM (
        SELECT Game_name as game,
            idMatch, elapsed,
            MAX( totalScore) AS maxscore,
            MIN( totalScore) AS minscore,
            AVG( totalScore) AS avgscore,
            count(nick) AS 'nplayers'
        FROM Match JOIN MatchPlayer USING (idMatch)
        WHERE state=1
        GROUP BY game, idMatch
        ) AS tmp
    GROUP BY game, nplayers ORDER BY game, nplayers;
    """

    _generalplayerstatsquery = """
    SELECT Game_name as game, nick,
        MAX(CAST(totalScore AS integer)) AS maxscore,
        MIN(CAST(totalScore AS integer)) AS minscore,
        CAST(ROUND(AVG(CAST(totalScore AS integer))) AS integer) AS avgscore,
        SUM(CAST(totalScore AS integer)) AS sumscore,
        SUM(winner) AS victories,
        COUNT(*) AS played,
        ROUND(CAST(SUM(winner) AS REAL)*100/COUNT(nick),2) as victoryp
    FROM Match JOIN MatchPlayer USING (idMatch)
    WHERE state=1
    GROUP BY game, nick
    ORDER BY game, victoryp DESC, played DESC;
    """

    def __init__(self) -> None:
        self.generalgamestats: list[dict] | None = None
        self.generalmatchstats: list[dict] | None = None
        self.generalplayerstats: list[dict] | None = None
        # Bound parameters for the queries below (populated by subclasses that
        # filter by player).
        self._params: tuple = ()

    def _bound_params(self, query: str) -> tuple:
        """Parameters to bind for ``query``.

        The player-filter clause (see ``ParticularStatsEngine``) is spliced in
        once per ``WHERE`` in the source query, so its parameters repeat the
        same number of times. Plain, unfiltered queries have no bound
        parameters. Subclasses that run their own filtered queries must bind
        with this helper.
        """
        if not self._params:
            return ()
        repeats = query.count("?") // len(self._params)
        return self._params * repeats

    def update(self, _players: list[str] | None = None) -> None:
        """Refresh the cached game, match and player statistics."""
        # Number of matches played
        try:
            self.generalgamestats = db.queryDict(
                self._lastwinnerquery, self._bound_params(self._lastwinnerquery)
            )
            self.generalmatchstats = db.queryDict(
                self._generalmatchstatsquery,
                self._bound_params(self._generalmatchstatsquery),
            )
            self.generalplayerstats = db.queryDict(
                self._generalplayerstatsquery,
                self._bound_params(self._generalplayerstatsquery),
            )
        except IndexError:
            pass

    def getGameStats(self, game: str) -> dict | None:
        """Return the last-winner row for ``game``, or ``None``."""
        if self.generalgamestats:
            for row in self.generalgamestats:
                if row["game"] == game:
                    return row
        return None

    def getMatchGameStats(self, game: str) -> list[dict] | None:
        """Return the per-player-count match statistics for ``game``."""
        if self.generalmatchstats:
            return [row for row in self.generalmatchstats if row["game"] == game]
        return None

    def getPlayerGameStats(self, game: str) -> list[dict] | None:
        """Return the per-player statistics for ``game``."""
        if self.generalplayerstats:
            return [row for row in self.generalplayerstats if row["game"] == game]
        return None


class ParticularStatsEngine(StatsEngine):
    """Statistics restricted to matches played by an exact set of players."""

    def __init__(self) -> None:
        super().__init__()
        self._lastwinnerquerybase = self._lastwinnerquery
        self._generalmatchstatsquerybase = self._generalmatchstatsquery
        self._generalplayerstatsquerybase = self._generalplayerstatsquery
        self.players: set[str] | None = None
        self._newclause = ""

    def update(self, players: list[str] | None = None) -> None:
        """Rebuild the player filter, then refresh all statistics."""
        self.updatePlayers(players)
        super().update()

    def updatePlayers(self, players: list[str] | None) -> None:
        """Rewrite the queries to keep only matches with exactly ``players``."""
        if players:
            splayers = set(players)
            if self.players != splayers:
                self.players = splayers
                # Fixed ordering so the placeholders and the bound parameters
                # line up (the nick list appears twice in the clause).
                plist = list(self.players)
                placeholders = ",".join("?" for _ in plist)
                self._newclause = (
                    "idMatch IN ("
                    "SELECT idMatch FROM MatchPlayer "
                    f"WHERE nick IN ({placeholders}) "
                    "GROUP BY idMatch "
                    "HAVING COUNT(*)=? and idMatch NOT IN ("
                    "SELECT idMatch FROM MatchPlayer "
                    f"WHERE nick NOT IN ({placeholders})))"
                )
                # Parameter order matches placeholder order in the clause:
                # first IN list, then COUNT(*)=?, then the NOT IN list.
                self._params = (*plist, len(plist), *plist)
                self._lastwinnerquery = self._lastwinnerquerybase.replace(
                    "WHERE", f"WHERE {self._newclause} AND"
                )
                self._generalmatchstatsquery = self._generalmatchstatsquerybase.replace(
                    "WHERE", f"WHERE {self._newclause} AND"
                )
                self._generalplayerstatsquery = (
                    self._generalplayerstatsquerybase.replace(
                        "WHERE", f"WHERE {self._newclause} AND"
                    )
                )


if __name__ == "__main__":
    db = GameLogDB()
    db.connectDB()
    #     se = StatsEngine()
    #     se.update()
    #     print(se.getMatchGameStats('Phase10Master'))
    #     print(se.getPlayerGameStats('Phase10Master'))

    pse = ParticularStatsEngine()
    pse.update(["Xavi", "Rosa", "Dani", "Joan"])
    print(pse.getMatchGameStats("Phase10Master"))
    print(pse.getPlayerGameStats("Phase10Master"))
