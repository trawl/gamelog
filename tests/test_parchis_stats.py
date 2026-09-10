"""Parchis max-kills/max-combo columns merged into the generic player and
match statistics tables (the RoundEvents-backed analogue of Skull King's
max_hits/avg_hits columns)."""

from core.registry import registry


def _play_finished_match(players, entries):
    """Play ``entries`` (player, score, kills) until the match auto-finishes."""
    engine = registry.create_engine("Parchis")
    for player in players:
        engine.addPlayer(player)
    engine.begin()
    for player, score, kills in entries:
        engine.addEntry(player, score, {"kills": kills})
    assert engine.getWinner() is not None  # sanity: the match actually finished
    return engine


def _player_row(stats, nick):
    return next(r for r in stats.getPlayerGameStats("Parchis") if r["nick"] == nick)


def _match_row(stats, nplayers):
    return next(
        r for r in stats.getMatchGameStats("Parchis") if r["nplayers"] == nplayers
    )


def test_player_columns_report_each_players_own_best(gamedb):
    # Alice's whole match is one entry: 3 kills, combo = 4+3-1 = 6.
    _play_finished_match(["Alice", "Bob"], [("Alice", 4, ["Bob", "Bob", "Bob"])])
    # Bob spreads 4 kills over two entries (2 each): combo = 1 + 5 = 6.
    _play_finished_match(
        ["Bob", "Carol"],
        [("Bob", 0, ["Carol", "Carol"]), ("Bob", 4, ["Carol", "Carol"])],
    )

    stats = registry.create_stats_engine("Parchis")
    stats.update()

    alice = _player_row(stats, "Alice")
    assert alice["max_kills"] == 3
    assert alice["max_combo"] == 6

    bob = _player_row(stats, "Bob")
    assert bob["max_kills"] == 4  # summed across both of his entries
    assert bob["max_combo"] == 6


def test_match_columns_grouped_by_player_count(gamedb):
    # 2-player match: 3 kills total.
    _play_finished_match(["Alice", "Bob"], [("Alice", 4, ["Bob", "Bob", "Bob"])])
    # 3-player match: 4 kills total (2+2), higher than the 2-player match.
    _play_finished_match(
        ["Carol", "Dave", "Eve"],
        [("Carol", 0, ["Dave", "Dave"]), ("Carol", 4, ["Dave", "Dave"])],
    )

    stats = registry.create_stats_engine("Parchis")
    stats.update()

    assert _match_row(stats, 2)["max_kills"] == 3
    assert _match_row(stats, 3)["max_kills"] == 4


def test_particular_columns_filter_by_exact_player_set(gamedb):
    # Match A: Alice kills Bob twice (Alice's entry -- kills are attributed
    # to the entry's player, not the victim).
    _play_finished_match(["Alice", "Bob"], [("Alice", 4, ["Bob", "Bob"])])
    # Match B: Bob kills Carol three times.
    _play_finished_match(["Bob", "Carol"], [("Bob", 4, ["Carol", "Carol", "Carol"])])

    unfiltered = registry.create_stats_engine("Parchis")
    unfiltered.update()
    assert _player_row(unfiltered, "Bob")["max_kills"] == 3

    filtered = registry.create_particular_stats_engine("Parchis")
    filtered.update(["Alice", "Bob"])
    assert _player_row(filtered, "Alice")["max_kills"] == 2
    # Match B is excluded by the filter, and Bob never killed anyone in
    # match A (only Alice scored there), so his column is absent, not 0.
    assert "max_kills" not in _player_row(filtered, "Bob")


def test_unfinished_match_is_excluded_from_columns(gamedb):
    engine = registry.create_engine("Parchis")
    engine.addPlayer("Alice")
    engine.addPlayer("Bob")
    engine.begin()
    engine.addEntry("Alice", 1, {"kills": ["Bob", "Bob"]})  # does not reach top=4
    assert engine.getWinner() is None

    stats = registry.create_stats_engine("Parchis")
    stats.update()
    assert stats.getPlayerGameStats("Parchis") is None
    assert stats.getMatchGameStats("Parchis") is None
