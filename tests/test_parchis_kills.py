"""Parchis kills: repeatable per-entry events persisted via RoundEvents,
generalising RoundStatistics' one-row-per-key limit."""

from core.registry import registry


def test_kills_roundtrip_through_round_events(gamedb):
    engine = registry.create_engine("Parchis")
    engine.addPlayer("Alice")
    engine.addPlayer("Bob")
    engine.addPlayer("Carol")
    engine.begin()

    engine.addEntry("Alice", 1, {"kills": ["Bob", "Bob", "Carol"]})
    engine.addEntry("Bob", 0, {"kills": ["Carol"]})
    engine.save()
    id_match = engine.match.idMatch

    rows = gamedb.queryDict(
        "SELECT nick,idRound,seq,eventType,target FROM RoundEvents "
        "WHERE idMatch=? ORDER BY idRound,seq",
        (id_match,),
    )
    assert rows == [
        {"nick": "Alice", "idRound": 1, "seq": 0, "eventType": "kill", "target": "Bob"},
        {"nick": "Alice", "idRound": 1, "seq": 1, "eventType": "kill", "target": "Bob"},
        {
            "nick": "Alice",
            "idRound": 1,
            "seq": 2,
            "eventType": "kill",
            "target": "Carol",
        },
        {"nick": "Bob", "idRound": 2, "seq": 0, "eventType": "kill", "target": "Carol"},
    ]

    resumed = registry.create_engine("Parchis")
    assert resumed.resume(id_match) is True
    assert [r.getKills() for r in resumed.getRounds()] == [
        ["Bob", "Bob", "Carol"],
        ["Carol"],
    ]
    tally = resumed.getKillsTally()
    assert tally["Alice"]["Bob"] == 2
    assert tally["Alice"]["Carol"] == 1
    assert tally["Bob"]["Carol"] == 1


def test_entry_without_kills_writes_no_round_events(gamedb):
    engine = registry.create_engine("Parchis")
    engine.addPlayer("Alice")
    engine.addPlayer("Bob")
    engine.begin()

    engine.addEntry("Alice", 2)
    engine.save()
    id_match = engine.match.idMatch

    rows = gamedb.queryDict("SELECT * FROM RoundEvents WHERE idMatch=?", (id_match,))
    assert rows == []


def test_other_games_do_not_write_round_events(gamedb):
    """RoundEvents is additive: games that never override the hooks stay silent."""
    engine = registry.create_engine("Ratuki")
    engine.addPlayer("Alice")
    engine.addPlayer("Bob")
    engine.begin()
    engine.openRound(1)
    engine.addRoundInfo("Alice", 30, {})
    engine.addRoundInfo("Bob", 10, {})
    engine.commitRound()
    engine.save()
    id_match = engine.match.idMatch

    rows = gamedb.queryDict("SELECT * FROM RoundEvents WHERE idMatch=?", (id_match,))
    assert rows == []
