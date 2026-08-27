"""Statistics engines, including the dynamic player-filter clause."""

import pytest

from core.registry import registry

PLAYERS = ["O'Brien", "Alice", "Bob"]
PARTICULAR_GAMES = sorted(
    d.name for d in registry.definitions() if d.particular_stats_engine_factory
)


@pytest.mark.parametrize("game", PARTICULAR_GAMES)
def test_particular_stats_run_cleanly(gamedb, game):
    engine = registry.create_particular_stats_engine(game)
    engine.update(PLAYERS)  # builds and runs the parameterised IN-clause queries
    # No exception == the query bound correctly; result may legitimately be empty.
    engine.getPlayerGameStats(game)


def test_particular_stats_param_count():
    from core.engine.stats import ParticularStatsEngine

    engine = ParticularStatsEngine()
    engine.updatePlayers(["O'Brien", "Alice"])
    # One nick list, the count, then the nick list again -> 2n + 1.
    assert len(engine._params) == 2 * 2 + 1


def test_general_stats_have_no_bound_params(gamedb):
    from core.engine.stats import StatsEngine

    engine = StatsEngine()
    engine.update()  # unfiltered queries -> no bound parameters, no error
    assert engine._params == ()
