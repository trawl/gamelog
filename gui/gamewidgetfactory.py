from games import load_builtin_games
from games.registry import registry


class GameWidgetFactory:
    @classmethod
    def createGameWidget(cls, gname, players, parent):
        load_builtin_games()
        definition = registry.get(gname)
        if not definition:
            return None
        return definition.resolve(definition.widget_factory)(gname, players, None, parent)

    @classmethod
    def resumeGameWidget(cls, gname, engine, parent):
        load_builtin_games()
        definition = registry.get(gname)
        if not definition:
            return None
        return definition.resolve(definition.widget_factory)(gname, None, engine, parent)
