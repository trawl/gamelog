from controllers.baseengine import GameEngine
from controllers.statsengine import ParticularStatsEngine, StatsEngine
from games import load_builtin_games
from games.registry import registry


class GameEngineFactory:
    @classmethod
    def createMatch(cls, gname):
        load_builtin_games()
        definition = registry.get(gname)
        return definition.resolve(definition.engine_factory)() if definition else GameEngine()


class StatsEngineFactory:
    @classmethod
    def getStatsEngine(cls, gname):
        load_builtin_games()
        definition = registry.get(gname)
        return (
            definition.resolve(definition.stats_engine_factory)()
            if definition and definition.stats_engine_factory
            else StatsEngine()
        )

    @classmethod
    def getParticularStatsEngine(cls, gname):
        load_builtin_games()
        definition = registry.get(gname)
        return (
            definition.resolve(definition.particular_stats_engine_factory)()
            if definition and definition.particular_stats_engine_factory
            else ParticularStatsEngine()
        )
