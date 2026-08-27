from games import load_builtin_games
from games.registry import registry
from model.base import GenericMatch


class GameFactory:
    @classmethod
    def createMatch(cls, gname, players=()):
        print(f"Creating match instance for {gname}")
        load_builtin_games()
        definition = registry.get(gname)
        return (
            definition.resolve(definition.match_factory)(players)
            if definition
            else GenericMatch(players)
        )
