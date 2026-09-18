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


# --- Qwirkle: score wins; ties broken by qwirkle count, then best single play -


def _add_entry(match, player, score, extras=None):
    """Append one scoring entry directly to ``match``, folding it into totals."""
    entry = match.createRound(len(match.rounds) + 1)
    entry.addInfo(player, score, extras)
    match.rounds.append(entry)
    match.totalScores[player] += score
    return entry


def test_qwirkle_high_score_wins_outright():
    match = started_match("Qwirkle", ["Ann", "Bob"])
    _add_entry(match, "Ann", 100, {"qwirkles": 0})
    _add_entry(match, "Bob", 80, {"qwirkles": 0})
    match.computeWinner()
    assert match.getWinner() == "Ann"


def test_qwirkle_tie_broken_by_qwirkle_count():
    match = started_match("Qwirkle", ["Ann", "Bob"])
    _add_entry(match, "Ann", 50, {"qwirkles": 2})
    _add_entry(match, "Bob", 50, {"qwirkles": 1})
    match.computeWinner()
    assert match.getWinner() == "Ann"


def test_qwirkle_tie_broken_by_best_single_play():
    match = started_match("Qwirkle", ["Ann", "Bob"])
    _add_entry(match, "Ann", 60, {"qwirkles": 0})
    _add_entry(match, "Ann", 40, {"qwirkles": 0})
    _add_entry(match, "Bob", 50, {"qwirkles": 0})
    _add_entry(match, "Bob", 50, {"qwirkles": 0})
    match.computeWinner()
    assert (
        match.getWinner() == "Ann"
    )  # same total and qwirkles, but a bigger single play


# --- Scrabble: score wins; ties broken by bonus count, then best single play --

ZERO_BONUSES = {"dl": 0, "tl": 0, "dw": 0, "tw": 0, "bingo": 0}


def test_scrabble_high_score_wins_outright():
    match = started_match("Scrabble", ["Ann", "Bob"])
    _add_entry(match, "Ann", 100, ZERO_BONUSES)
    _add_entry(match, "Bob", 80, ZERO_BONUSES)
    match.computeWinner()
    assert match.getWinner() == "Ann"


def test_scrabble_tie_broken_by_bonus_count():
    match = started_match("Scrabble", ["Ann", "Bob"])
    _add_entry(match, "Ann", 50, {**ZERO_BONUSES, "dw": 1})
    _add_entry(match, "Bob", 50, ZERO_BONUSES)
    match.computeWinner()
    assert match.getWinner() == "Ann"


def test_scrabble_tie_broken_by_best_single_play():
    match = started_match("Scrabble", ["Ann", "Bob"])
    _add_entry(match, "Ann", 60, ZERO_BONUSES)
    _add_entry(match, "Ann", 40, ZERO_BONUSES)
    _add_entry(match, "Bob", 50, ZERO_BONUSES)
    _add_entry(match, "Bob", 50, ZERO_BONUSES)
    match.computeWinner()
    assert match.getWinner() == "Ann"


# --- Pocha: highest total wins, but only once every hand has been played -----


def _pad_rounds(match, count):
    """Add ``count`` placeholder rounds, as if that many hands had been played."""
    for _ in range(count):
        match.rounds.append(match.createRound(len(match.rounds) + 1))


def test_pocha_no_winner_before_last_hand():
    match = started_match("Pocha", ["Ann", "Bob"])
    match.totalScores = {"Ann": 100, "Bob": 20}
    _pad_rounds(match, match.maxRounds - 1)
    match.computeWinner()
    assert not match.getWinner()


def test_pocha_highest_score_wins_after_last_hand():
    match = started_match("Pocha", ["Ann", "Bob"])
    match.totalScores = {"Ann": 100, "Bob": 20}
    _pad_rounds(match, match.maxRounds)
    match.computeWinner()
    assert match.getWinner() == "Ann"


def test_pocha_tie_goes_to_the_last_player_at_the_max_score():
    """``computeWinner`` scans with ``>=``, so a tie favours iteration order --
    a fragile behaviour worth pinning down explicitly."""
    match = started_match("Pocha", ["Ann", "Bob"])
    match.totalScores = {"Ann": 50, "Bob": 50}
    _pad_rounds(match, match.maxRounds)
    match.computeWinner()
    assert match.getWinner() == "Bob"


# --- Skull King: a Pocha variant, so the same rules apply over its own hands --


def test_skullking_highest_score_wins_after_last_hand():
    match = started_match("Skull King", ["Ann", "Bob"])
    match.totalScores = {"Ann": 100, "Bob": 20}
    _pad_rounds(match, match.maxRounds)
    match.computeWinner()
    assert match.getWinner() == "Ann"


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
