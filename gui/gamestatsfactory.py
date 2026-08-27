from games import load_builtin_games
from games.registry import registry
from gui.gamestats import QuickStatsTW


class QSFactory:
    @classmethod
    def createQS(cls, gname, players, parent):
        load_builtin_games()
        definition = registry.get(gname)
        if definition and definition.quick_stats_factory:
            return definition.resolve(definition.quick_stats_factory)(
                gname, players, parent
            )
        return QuickStatsTW(gname, players, parent)
