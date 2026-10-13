"""ResumeEngine: discovering saved matches for a game and rebuilding an
engine from one."""

from core.engine.resume import ResumeEngine
from core.registry import registry


def test_get_candidates_lists_only_saved_matches_for_the_requested_game(gamedb):
    saved = registry.create_engine("Ratuki")
    saved.addPlayer("Ann")
    saved.addPlayer("Bob")
    saved.begin()
    saved.save()
    saved_id = saved.match.idMatch

    cancelled = registry.create_engine("Ratuki")
    cancelled.addPlayer("Cy")
    cancelled.begin()
    cancelled.cancelMatch()  # persisted, but not in the SAVED state

    other_game = registry.create_engine("Toma6")
    other_game.addPlayer("Ann")
    other_game.begin()
    other_game.save()  # saved, but for a different game

    candidates = ResumeEngine("Ratuki").getCandidates()

    assert set(candidates) == {saved_id}
    assert candidates[saved_id]["players"] == ["Ann", "Bob"]


def test_get_candidates_is_empty_when_nothing_is_saved(gamedb):
    assert ResumeEngine("Ratuki").getCandidates() == {}


def test_resume_rebuilds_the_engine_with_its_players(gamedb):
    engine = registry.create_engine("Ratuki")
    engine.addPlayer("Ann")
    engine.addPlayer("Bob")
    engine.begin()
    engine.save()
    id_match = engine.match.idMatch

    resumed = ResumeEngine("Ratuki").resume(id_match)

    assert resumed is not None
    assert set(resumed.getListPlayers()) == {"Ann", "Bob"}


def test_resume_returns_none_for_an_unknown_match(gamedb):
    assert ResumeEngine("Ratuki").resume(999999) is None
