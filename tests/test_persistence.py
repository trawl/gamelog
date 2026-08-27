"""Match persistence: every game can save and resume, round-tripping through
the parameterised SQL layer (including awkward player names)."""

import pytest

from core.registry import registry

APOSTROPHE = "O'Brien"
GAME_NAMES = sorted(d.name for d in registry.definitions())


@pytest.mark.parametrize("game", GAME_NAMES)
def test_save_and_resume_players(gamedb, game):
    engine = registry.create_engine(game)
    engine.addPlayer(APOSTROPHE)
    engine.addPlayer("Alice")
    engine.begin()
    engine.save()
    id_match = engine.match.idMatch
    assert id_match is not None and id_match > 0

    resumed = registry.create_engine(game)
    assert resumed.resume(id_match) is True
    assert set(resumed.getListPlayers()) == {APOSTROPHE, "Alice"}


def test_ratuki_round_roundtrip(gamedb):
    engine = registry.create_engine("Ratuki")
    engine.addPlayer(APOSTROPHE)
    engine.addPlayer("Alice")
    engine.begin()
    engine.openRound(1)
    engine.setRoundWinner(APOSTROPHE)
    engine.addRoundInfo(APOSTROPHE, 30, {})
    engine.addRoundInfo("Alice", 10, {})
    engine.commitRound()
    engine.save()

    resumed = registry.create_engine("Ratuki")
    assert resumed.resume(engine.match.idMatch)
    assert resumed.getScoreFromPlayer(APOSTROPHE) == 30
    assert resumed.getScoreFromPlayer("Alice") == 10
    assert len(resumed.getRounds()) == 1
