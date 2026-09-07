"""Discovery of saved matches and reconstruction of their engines."""

from __future__ import annotations

import sys
from typing import cast

from core.engine.base import GameEngine, RoundGameEngine, readInput
from core.engine.db import db
from core.registry import registry


class ResumeEngine:
    """Lists the saved matches for a game and rebuilds an engine from one."""

    def __init__(self, game: str) -> None:
        self.game = game
        self.candidates: dict[int, dict] = {}
        cur = db.execute(
            "SELECT idMatch, started, finished, elapsed "
            "FROM Match WHERE state=4 and Game_name=?",
            (self.game,),
        )
        for row in cur:
            self.candidates[row["idMatch"]] = {}
            self.candidates[row["idMatch"]]["started"] = row["started"]
            self.candidates[row["idMatch"]]["finished"] = row["finished"]
            self.candidates[row["idMatch"]]["elapsed"] = row["elapsed"]
            self.candidates[row["idMatch"]]["players"] = []

        for idMatch, match in self.candidates.items():
            cur = db.execute("SELECT nick FROM MatchPlayer WHERE idMatch=?", (idMatch,))
            for row in cur:
                match["players"].append(str(row["nick"]))

    def getCandidates(self) -> dict[int, dict]:
        """Return the saved matches, keyed by match id."""
        return self.candidates

    def resume(self, idMatch: int) -> GameEngine | None:
        """Rebuild and return the engine for ``idMatch``, or ``None``."""
        engine = registry.create_engine(self.game)
        if engine and engine.resume(idMatch):
            return engine
        return None


if __name__ == "__main__":
    from core.logging_config import configure_logging
    from games import load_builtin_games

    configure_logging("DEBUG")
    load_builtin_games()
    if not db.isConnected():
        db.connectDB()
    valid_games = [definition.name for definition in registry.definitions()]
    pmt = "Game to play ({}): ".format("/".join(valid_games))
    game = readInput(pmt, str, lambda x: x in valid_games)
    re = ResumeEngine(game)
    candidates = re.getCandidates()
    if not len(candidates):
        print(f"No {game} matches to restore found")
        sys.exit()
    else:
        print("Matches to restore:")
        for idMatch, match in candidates.items():
            msg = "{}) {} player match started at {}. Time played: {}. Players:{}"
            print(
                msg.format(
                    idMatch,
                    len(match["players"]),
                    match["started"],
                    match["elapsed"],
                    match["players"],
                )
            )
        print()
        idMatch = readInput("idMatch to resume: ", int, lambda x: x in candidates)
        print(f"Restoring match #{idMatch}")
        engine = re.resume(idMatch)
        if not engine:
            print(f"Could not restore match #{idMatch}")
            sys.exit()
        else:
            cast(RoundGameEngine, engine).runStubRoundLoop()
