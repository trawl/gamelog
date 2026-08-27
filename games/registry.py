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


registry = GameRegistry()
