"""Game-rule tests: winner computation and score accumulation.

The winner rules are pure domain logic and are exercised directly on the match
object (no database needed); one end-to-end test drives a full engine round
flow to cover accumulation + winner detection + persistence together.
"""

from core.registry import registry


def started_match(game, players):
    match = registry.create_match(game)
    match.setPlayers(list(players))
    match.startMatch()
    return match


# --- Ratuki: first to reach `top` wins, highest score if several cross it -----


def test_ratuki_highest_reaching_top_wins():
    match = started_match("Ratuki", ["Ann", "Bob"])
    match.totalScores["Ann"] = 110  # >= top (100)
    match.totalScores["Bob"] = 30
    match.computeWinner()
    assert match.getWinner() == "Ann"


def test_ratuki_no_winner_below_top():
    match = started_match("Ratuki", ["Ann", "Bob"])
    match.totalScores["Ann"] = 90
    match.totalScores["Bob"] = 30
    match.computeWinner()
    assert not match.getWinner()


# --- Toma6: game ends when someone reaches `top` (66); lowest score wins ------


def test_toma6_lowest_wins_when_top_reached():
    match = started_match("Toma6", ["Ann", "Bob"])
    match.totalScores["Ann"] = 70  # triggers game end (>= 66)
    match.totalScores["Bob"] = 15
    match.computeWinner()
    assert match.getWinner() == "Bob"


def test_toma6_no_winner_before_top():
    match = started_match("Toma6", ["Ann", "Bob"])
    match.totalScores["Ann"] = 40
    match.totalScores["Bob"] = 15
    match.computeWinner()
    assert not match.getWinner()


# --- Remigio: reaching `top` eliminates you; last player standing wins --------


def test_remigio_last_active_player_wins():
    match = started_match("Remigio", ["Ann", "Bob"])
    match.totalScores["Ann"] = 110  # eliminated
    match.totalScores["Bob"] = 30
    match.computeWinner()
    assert match.getWinner() == "Bob"


def test_remigio_no_winner_while_two_remain():
    match = started_match("Remigio", ["Ann", "Bob", "Cy"])
    match.totalScores["Ann"] = 110  # only one eliminated -> two still active
    match.totalScores["Bob"] = 30
    match.totalScores["Cy"] = 40
    match.computeWinner()
    assert not match.getWinner()


# --- Phase10: clearing all 10 phases wins; ties broken by lowest score --------


def test_phase10_completing_all_phases_wins():
    match = started_match("Phase10", ["Ann", "Bob"])
    match.phasesCleared = {"Ann": list(range(1, 11)), "Bob": [1, 2, 3]}
    match.totalScores = {"Ann": 50, "Bob": 20}
    match.computeWinner()
    assert match.getWinner() == "Ann"


def test_phase10_tie_broken_by_lowest_score():
    match = started_match("Phase10", ["Ann", "Bob"])
    match.phasesCleared = {"Ann": list(range(1, 11)), "Bob": list(range(1, 11))}
    match.totalScores = {"Ann": 50, "Bob": 20}
    match.computeWinner()
    assert match.getWinner() == "Bob"


# --- End-to-end: driving the engine accumulates scores and declares a winner --


def _play_round(engine, nround, scores, winner):
    engine.openRound(nround)
    engine.setRoundWinner(winner)
    for player, score in scores.items():
        engine.addRoundInfo(player, score, {})
    engine.commitRound()


def test_ratuki_full_round_flow(gamedb):
    engine = registry.create_engine("Ratuki")
    engine.addPlayer("Ann")
    engine.addPlayer("Bob")
    engine.begin()

    _play_round(engine, 1, {"Ann": 60, "Bob": 20}, "Ann")
    assert engine.getScoreFromPlayer("Ann") == 60
    assert not engine.getWinner()

    _play_round(engine, 2, {"Ann": 50, "Bob": 10}, "Ann")
    assert engine.getScoreFromPlayer("Ann") == 110  # accumulated across rounds
    assert engine.getWinner() == "Ann"
