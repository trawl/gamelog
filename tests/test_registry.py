"""The game registry: discovery, object creation, and fallbacks."""

from core.engine.base import GameEngine
from core.model.base import GenericMatch
from core.registry import registry

EXPECTED_GAMES = {
    "Carcassonne",
    "Phase10",
    "Phase10Master",
    "Pocha",
    "Qwirkle",
    "Ratuki",
    "Remigio",
    "Scrabble",
    "Skull King",
    "Toma6",
}


def test_all_games_registered():
    names = {d.name for d in registry.definitions()}
    assert EXPECTED_GAMES <= names


def test_every_definition_resolves_model_and_engine():
    for d in registry.definitions():
        assert callable(d.resolve(d.match_factory)), d.name
        assert callable(d.resolve(d.engine_factory)), d.name


def test_create_match_and_engine():
    match = registry.create_match("Ratuki", ["Ann", "Bob"])
    assert match.getPlayers() == ["Ann", "Bob"]
    engine = registry.create_engine("Ratuki")
    assert engine.getGame() == "Ratuki"


def test_unknown_game_falls_back_to_generics():
    assert isinstance(registry.create_match("NoSuchGame", ()), GenericMatch)
    assert isinstance(registry.create_engine("NoSuchGame"), GameEngine)
    assert registry.create_widget("NoSuchGame") is None


def test_optional_factories_default_when_missing():
    # Toma6 registers no stats/quick-stats factories -> framework defaults.
    from core.engine.stats import ParticularStatsEngine, StatsEngine

    assert isinstance(registry.create_stats_engine("Toma6"), StatsEngine)
    assert isinstance(
        registry.create_particular_stats_engine("Toma6"), ParticularStatsEngine
    )
