"""Single source of truth for the games supported by the application."""

from collections.abc import Sequence
from dataclasses import dataclass
from importlib import import_module
from typing import Any

GameType = str | type[Any]


@dataclass(frozen=True)
class GameDefinition:
    name: str
    max_players: int
    description: str
    rules: str
    match_factory: GameType
    engine_factory: GameType
    widget_factory: GameType
    quick_stats_factory: GameType | None = None
    stats_engine_factory: GameType | None = None
    particular_stats_engine_factory: GameType | None = None

    def database_row(self) -> tuple[str, int, str, str]:
        return (self.name, self.max_players, self.description, self.rules)

    @staticmethod
    def resolve(factory: GameType) -> type[Any]:
        if not isinstance(factory, str):
            return factory
        module_name, separator, class_name = factory.partition(":")
        if not separator:
            raise ValueError(f"Invalid game factory reference: {factory}")
        return getattr(import_module(module_name), class_name)

    # -- object creation -------------------------------------------------
    # Each game knows how to build its own model / engine / widgets from the
    # references above.  Optional factories fall back to the framework
    # defaults.  Defaults are imported lazily so that building, say, a match
    # never drags in the Qt widget stack.

    def create_match(self, players=()) -> Any:
        return self.resolve(self.match_factory)(players)

    def create_engine(self) -> Any:
        return self.resolve(self.engine_factory)()

    def create_widget(self, gname, players=None, engine=None, parent=None) -> Any:
        return self.resolve(self.widget_factory)(gname, players, engine, parent)

    def create_stats_engine(self) -> Any:
        if self.stats_engine_factory:
            return self.resolve(self.stats_engine_factory)()
        from controllers.statsengine import StatsEngine

        return StatsEngine()

    def create_particular_stats_engine(self) -> Any:
        if self.particular_stats_engine_factory:
            return self.resolve(self.particular_stats_engine_factory)()
        from controllers.statsengine import ParticularStatsEngine

        return ParticularStatsEngine()

    def create_quick_stats(self, gname, players, parent) -> Any:
        if self.quick_stats_factory:
            return self.resolve(self.quick_stats_factory)(gname, players, parent)
        from gui.gamestats import QuickStatsTW

        return QuickStatsTW(gname, players, parent)


class GameRegistry:
    def __init__(self) -> None:
        self._definitions: dict[str, GameDefinition] = {}

    def register(self, definition: GameDefinition) -> None:
        if definition.name in self._definitions:
            raise ValueError(f"Game already registered: {definition.name}")
        self._definitions[definition.name] = definition

    def get(self, name: str | None) -> GameDefinition | None:
        if name is None:
            return None
        return self._definitions.get(name)

    def definitions(self) -> Sequence[GameDefinition]:
        return tuple(self._definitions.values())

    def _ensure_loaded(self) -> None:
        # Imported lazily to avoid a circular import: ``games`` imports this
        # module before ``load_builtin_games`` is defined.
        from games import load_builtin_games

        load_builtin_games()

    # -- object creation -------------------------------------------------
    # Convenience wrappers that resolve a game by name and delegate to its
    # definition, falling back to the framework defaults when the game is
    # unknown.  These replace the former per-layer factory classes.

    def create_match(self, name: str | None, players=()) -> Any:
        self._ensure_loaded()
        definition = self.get(name)
        if definition:
            return definition.create_match(players)
        from model.base import GenericMatch

        return GenericMatch(players)

    def create_engine(self, name: str | None) -> Any:
        self._ensure_loaded()
        definition = self.get(name)
        if definition:
            return definition.create_engine()
        from controllers.baseengine import GameEngine

        return GameEngine()

    def create_widget(
        self, name: str | None, players=None, engine=None, parent=None
    ) -> Any:
        self._ensure_loaded()
        definition = self.get(name)
        if not definition:
            return None
        return definition.create_widget(name, players, engine, parent)

    def create_stats_engine(self, name: str | None) -> Any:
        self._ensure_loaded()
        definition = self.get(name)
        if definition:
            return definition.create_stats_engine()
        from controllers.statsengine import StatsEngine

        return StatsEngine()

    def create_particular_stats_engine(self, name: str | None) -> Any:
        self._ensure_loaded()
        definition = self.get(name)
        if definition:
            return definition.create_particular_stats_engine()
        from controllers.statsengine import ParticularStatsEngine

        return ParticularStatsEngine()

    def create_quick_stats(self, name: str | None, players, parent) -> Any:
        self._ensure_loaded()
        definition = self.get(name)
        if definition:
            return definition.create_quick_stats(name, players, parent)
        from gui.gamestats import QuickStatsTW

        return QuickStatsTW(name, players, parent)


registry = GameRegistry()
