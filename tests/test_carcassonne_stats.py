"""Carcassonne kind-record statistics: regression coverage for the player
filter that CarcassonneParticularStatsEngine.update() used to silently drop."""

from core.registry import registry


def _play_finished_match(players, entries):
    """Play ``entries`` (player, score, kind) then explicitly finish the match."""
    engine = registry.create_engine("Carcassonne")
    for player in players:
        engine.addPlayer(player)
    engine.begin()
    for player, score, kind in entries:
        engine.addEntry(player, score, {"kind": kind})
    engine.finishGame()
    assert engine.getWinner() is not None  # sanity: the match is FINISHED (state=1)
    return engine


def test_particular_kind_records_filter_by_exact_player_set(gamedb):
    _play_finished_match(["Alice", "X"], [("Alice", 10, "City")])
    _play_finished_match(["Bob", "Y"], [("Bob", 20, "City")])

    unfiltered = registry.create_stats_engine("Carcassonne")
    unfiltered.update()
    single = unfiltered.getSingleKindRecords()
    assert any(r["player"] == "Bob" and r["points"] == 20 for r in single)

    filtered = registry.create_particular_stats_engine("Carcassonne")
    filtered.update(["Alice", "X"])
    single = filtered.getSingleKindRecords()
    match = filtered.getMatchKindRecords()

    # With the filter actually applied, Bob's higher-scoring match must be
    # excluded -- before the fix, `players` never reached updatePlayers() via
    # ParchisStatsEngine's MRO-mirrored bug, so this returned Bob's 20 too.
    assert not any(r["player"] == "Bob" for r in single)
    assert not any(r["player"] == "Bob" for r in match)
    assert any(r["player"] == "Alice" and r["points"] == 10 for r in single)
    assert any(r["player"] == "Alice" and r["points"] == 10 for r in match)
