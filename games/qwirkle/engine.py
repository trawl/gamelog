from typing import cast

from core.engine.base import EntryGameEngine, readInput
from core.engine.db import db
from core.engine.stats import ParticularStatsEngine, StatsEngine
from games.qwirkle.model import QwirkleMatch


class QwirkleEngine(EntryGameEngine):
    def __init__(self):
        if not hasattr(self, "game"):
            self.game = "Qwirkle"
        EntryGameEngine.__init__(self)

    def getBonuses(self):
        return cast(QwirkleMatch, self.match).getBonuses()

    def requiresExplicitFinish(self):
        return True

    def runStubRoundPlayer(self, player, winner=None):
        score = readInput(
            f"{player} score: ",
            int,
            lambda x: x > 0,
            "Sorry, invalid score number.",
        )
        errmsg = "Sorry, invalid kind [0-6]"
        kind = readInput("Qwirkle bonus?: ", int, lambda x: 0 <= x <= 6, errmsg)
        self.addEntry(player, score, {"kind": kind})


class QwirkleStatsEngine(StatsEngine):
    def __init__(self):
        super().__init__()
        self.game = "Qwirkle"
        self.singleKindRecord = None
        self.queries = {}
        self.define_queries()

    def define_queries(self):
        self.query_params = {
            "extreme_rounds": ("max_round_score", "min_round_score"),
            "max_qwirkles": ("max_qwirkles",),
        }
        self.queries["extreme_rounds"] = f"""
        SELECT Round.nick as "player", max(score) as "max_round_score",
            min(score) as "min_round_score"
        FROM Round,Match
        WHERE Match.idMatch = Round.idMatch
            and Match.state = 1
            and Game_name="{self.game}"
        group by player
        """
        self.queries["max_qwirkles"] = """
        SELECT player, MAX(qwirkles) as "max_qwirkles"
        FROM (
            SELECT Match.idMatch as "match",
                RoundStatistics.nick as "player",key,
 			SUM(value) as "qwirkles"
            FROM Match,Round,RoundStatistics
            WHERE Match.idMatch = Round.idMatch
                AND Round.idMatch = RoundStatistics.idMatch
                AND Round.idRound = RoundStatistics.idRound
                AND Round.nick = RoundStatistics.nick
                AND Match.state = 1
                AND Game_name='Qwirkle'
                AND key='qwirkles'
            GROUP BY "match", "player") AS TMP
        GROUP BY "player"
        """

    def update(self, players=None):
        super().update()
        if not self.generalplayerstats:
            return

        for q, params in self.query_params.items():
            query = self.queries[q]
            for row in db.queryDict(query, self._bound_params(query)):
                player = row["player"]
                for r2 in self.generalplayerstats:
                    if r2["nick"] == player and r2["game"] == self.game:
                        for p in params:
                            r2[p] = row[p]
                        break


class QwirkleParticularStatsEngine(QwirkleStatsEngine, ParticularStatsEngine):
    def updatePlayers(self, players):
        super().updatePlayers(players)
        if players:
            self.define_queries()
            for q in self.queries:
                self.queries[q] = self.queries[q].replace(
                    "WHERE", "WHERE {} AND".format("Match." + self._newclause)
                )


if __name__ == "__main__":
    re = QwirkleEngine()
    re.gameStub()
