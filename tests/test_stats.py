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


@pytest.mark.parametrize("game", PARTICULAR_GAMES)
def test_particular_stats_update_applies_the_player_filter(gamedb, game):
    from tests.test_playerstats import _match

    _match(game, {"O'Brien": (9, True), "Alice": (1, False)})
    _match(game, {"O'Brien": (9, True), "Alice": (1, False), "Bob": (2, False)})
    engine = registry.create_particular_stats_engine(game)

    # update(players) alone must filter: game engines overriding update() have
    # to pass the players on rather than drop them.
    engine.update(["O'Brien", "Alice"])
    rows = engine.getPlayerGameStats(game) or []
    assert {r["nick"]: r["played"] for r in rows} == {"O'Brien": 1, "Alice": 1}

    engine.update(PLAYERS)
    rows = engine.getPlayerGameStats(game) or []
    assert {r["nick"]: r["played"] for r in rows} == dict.fromkeys(PLAYERS, 1)


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


# --- Performance index --------------------------------------------------------


def _performance(rows):
    return {r["nick"]: r["performance"] for r in rows}


def _seed_mixed_games():
    """A 2-player duel, a 4-player match, a shared win and a match with no
    winner, so that every special case of the index is exercised."""
    from tests.test_playerstats import _match

    _match("Ratuki", {"Ann": (9, True), "Bob": (1, False)})
    _match(
        "Ratuki",
        {"Ann": (1, False), "Bob": (9, True), "Cy": (2, False), "Dan": (3, False)},
    )
    _match("Ratuki", {"Ann": (5, True), "Cy": (5, True), "Dan": (1, False)})
    _match("Ratuki", {"Ann": (0, False), "Bob": (0, False)})  # nobody won
    _match("Ratuki", {"Ann": (9, True), "Bob": (1, False)}, state=2)  # not finished
    _match("Toma6", {"Zoe": (0, False), "Bob": (0, False)})  # only no-winner


def test_general_performance_matches_the_player_statistics(gamedb):
    from core.engine.playerstats import player_summary
    from core.engine.stats import StatsEngine

    _seed_mixed_games()
    engine = StatsEngine()
    engine.update()

    ratuki = _performance(engine.getPlayerGameStats("Ratuki") or [])
    # Ann: expected 1/2 + 1/4 + 1/3, earned 1 + 0 + 1/2 (the nobody-won match
    # and the unfinished one count for nothing).
    assert ratuki["Ann"] == pytest.approx(1.5 / (1 / 2 + 1 / 4 + 1 / 3))
    assert ratuki["Cy"] == pytest.approx(0.5 / (1 / 4 + 1 / 3))
    assert ratuki["Dan"] == 0
    for nick, value in ratuki.items():
        assert value == pytest.approx(player_summary(nick, ("Ratuki",)).performance)

    toma6 = _performance(engine.getPlayerGameStats("Toma6") or [])
    assert toma6 == {"Bob": None, "Zoe": None}


def test_particular_performance_binds_the_player_filter(gamedb):
    from core.engine.stats import ParticularStatsEngine
    from tests.test_playerstats import _match

    _seed_mixed_games()
    _match("Ratuki", {"O'Brien": (9, True), "Ann": (1, False)})
    _match("Ratuki", {"O'Brien": (1, False), "Ann": (9, True)})
    _match("Ratuki", {"O'Brien": (5, True), "Ann": (5, True)})
    _match("Ratuki", {"O'Brien": (9, True), "Ann": (1, False), "Bob": (0, False)})

    engine = ParticularStatsEngine()
    engine.update(["Ann", "O'Brien"])

    rows = _performance(engine.getPlayerGameStats("Ratuki") or [])
    assert set(rows) == {"Ann", "O'Brien"}
    # Three matches with exactly these two players; the 3-player one and the
    # earlier Ann/Bob matches do not count. O'Brien: 1 + 0 + 1/2 over 3/2.
    assert rows["O'Brien"] == pytest.approx(1.5 / 1.5)
    assert rows["Ann"] == pytest.approx(1.5 / 1.5)
    played = {r["nick"]: r["played"] for r in engine.getPlayerGameStats("Ratuki") or []}
    assert played == {"Ann": 3, "O'Brien": 3}

    # A different exact set: only the shared-win match qualifies.
    engine.update(["Ann", "Cy", "Dan"])
    shared = _performance(engine.getPlayerGameStats("Ratuki") or [])
    assert shared["Ann"] == pytest.approx(0.5 / (1 / 3))
    assert shared["Cy"] == pytest.approx(shared["Ann"])
    assert shared["Dan"] == 0


def test_quick_stats_show_the_performance_after_victory_percent(qapp, gamedb):
    from core.ui.game.stats import GeneralQuickStats

    _seed_mixed_games()
    box = GeneralQuickStats("Ratuki", None)

    keys = box.playerStatsKeys
    assert keys[keys.index("victoryp") + 1] == "performance"
    assert len(keys) == len(box.playerStatsHeaders)

    table = box.playerStatsTable
    column = keys.index("performance")
    cells = {}
    for row in range(table.rowCount()):
        nick, cell = table.item(row, 0), table.item(row, column)
        assert nick is not None and cell is not None
        cells[nick.text()] = cell.text()
    assert cells["Dan"] == "0.00×"
    assert cells["Ann"].endswith("×")
    header = table.horizontalHeaderItem(column)
    assert header is not None
    assert "chance" in header.toolTip()


@pytest.mark.parametrize("game", sorted(d.name for d in registry.definitions()))
def test_every_game_reports_the_performance(gamedb, game):
    from tests.test_playerstats import _match

    _match(game, {"Ann": (9, True), "Bob": (1, False)})
    _match(game, {"Ann": (1, False), "Bob": (9, True), "Cy": (2, False)})

    general = registry.create_stats_engine(game)
    general.update()
    # As the quick-stats box does: set the players, then refresh.
    particular = registry.create_particular_stats_engine(game)
    particular.updatePlayers(["Ann", "Bob"])
    particular.update()

    def ann(engine):
        rows = {r["nick"]: r for r in engine.getPlayerGameStats(game) or []}
        return rows["Ann"]["performance"]

    assert ann(general) == pytest.approx(1 / (1 / 2 + 1 / 3))
    assert ann(particular) == pytest.approx(2.0)  # only the duel has these two
