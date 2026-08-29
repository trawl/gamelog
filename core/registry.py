"""Single source of truth for the games supported by the application."""

from collections.abc import Sequence
from dataclasses import dataclass
from importlib import import_module
from typing import Any

GameType = str | type[Any]


@dataclass(frozen=True)
class GameDefinition:
    """Immutable description of one game and how to build its objects.

    Factory fields are either a class or a lazy ``"module:Class"`` reference
    (resolved on demand by :meth:`resolve`), so registering a game never
    imports its Qt widgets. Optional factories fall back to framework defaults.
    """

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
        """Return the columns stored in the Game table for this game."""
        return (self.name, self.max_players, self.description, self.rules)

    @staticmethod
    def resolve(factory: GameType) -> type[Any]:
        """Resolve a factory reference to a class, importing it if needed."""
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

    def create_match(self, players: Sequence[str] = ()) -> Any:
        return self.resolve(self.match_factory)(players)

    def create_engine(self) -> Any:
        return self.resolve(self.engine_factory)()

    def create_widget(
        self,
        gname: str,
        players: Sequence[str] | None = None,
        engine: Any = None,
        parent: Any = None,
    ) -> Any:
        return self.resolve(self.widget_factory)(gname, players, engine, parent)

    def create_stats_engine(self) -> Any:
        if self.stats_engine_factory:
            return self.resolve(self.stats_engine_factory)()
        from core.engine.stats import StatsEngine

        return StatsEngine()

    def create_particular_stats_engine(self) -> Any:
        if self.particular_stats_engine_factory:
            return self.resolve(self.particular_stats_engine_factory)()
        from core.engine.stats import ParticularStatsEngine

        return ParticularStatsEngine()

    def create_quick_stats(
        self, gname: str, players: Sequence[str], parent: Any
    ) -> Any:
        if self.quick_stats_factory:
            return self.resolve(self.quick_stats_factory)(gname, players, parent)
        from core.ui.gamestats import QuickStatsTW

        return QuickStatsTW(gname, players, parent)


class GameRegistry:
    """Registry of every known game, keyed by name.

    Games register themselves at import time; the ``create_*`` helpers resolve
    a game by name and delegate to its definition, falling back to the
    framework defaults when the name is unknown.
    """

    def __init__(self) -> None:
        self._definitions: dict[str, GameDefinition] = {}

    def register(self, definition: GameDefinition) -> None:
        """Add a game definition, rejecting a duplicate name."""
        if definition.name in self._definitions:
            raise ValueError(f"Game already registered: {definition.name}")
        self._definitions[definition.name] = definition

    def get(self, name: str | None) -> GameDefinition | None:
        """Return the definition for ``name``, or ``None`` if not registered."""
        if name is None:
            return None
        return self._definitions.get(name)

    def definitions(self) -> Sequence[GameDefinition]:
        """Return all registered game definitions."""
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

    def create_match(self, name: str | None, players: Sequence[str] = ()) -> Any:
        self._ensure_loaded()
        definition = self.get(name)
        if definition:
            return definition.create_match(players)
        from core.model.base import GenericMatch

        return GenericMatch(players)

    def create_engine(self, name: str | None) -> Any:
        self._ensure_loaded()
        definition = self.get(name)
        if definition:
            return definition.create_engine()
        from core.engine.base import GameEngine

        return GameEngine()

    def create_widget(
        self,
        name: str | None,
        players: Sequence[str] | None = None,
        engine: Any = None,
        parent: Any = None,
    ) -> Any:
        self._ensure_loaded()
        definition = self.get(name)
        if not definition:
            return None
        return definition.create_widget(definition.name, players, engine, parent)

    def create_stats_engine(self, name: str | None) -> Any:
        self._ensure_loaded()
        definition = self.get(name)
        if definition:
            return definition.create_stats_engine()
        from core.engine.stats import StatsEngine

        return StatsEngine()

    def create_particular_stats_engine(self, name: str | None) -> Any:
        self._ensure_loaded()
        definition = self.get(name)
        if definition:
            return definition.create_particular_stats_engine()
        from core.engine.stats import ParticularStatsEngine

        return ParticularStatsEngine()

    def create_quick_stats(
        self, name: str | None, players: Sequence[str], parent: Any
    ) -> Any:
        self._ensure_loaded()
        definition = self.get(name)
        if definition:
            return definition.create_quick_stats(definition.name, players, parent)
        from core.ui.gamestats import QuickStatsTW

        # Unknown-game fallback: name is only None in degenerate/unused paths.
        return QuickStatsTW(name or "", players, parent)


registry = GameRegistry()
