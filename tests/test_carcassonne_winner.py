"""Carcassonne's winner tie-break: total score, then a sequential elimination
by each feature kind's total (City, Road, Cloister, ...), in that order."""

from core.registry import registry


def started_match(players):
    match = registry.create_match("Carcassonne")
    match.setPlayers(list(players))
    match.startMatch()
    return match


def _add_entry(match, player, score, kind):
    entry = match.createRound(len(match.rounds) + 1)
    entry.addInfo(player, score, {"kind": kind})
    match.rounds.append(entry)
    match.totalScores[player] += score


def test_high_score_wins_outright():
    match = started_match(["Ann", "Bob"])
    _add_entry(match, "Ann", 20, "City")
    _add_entry(match, "Bob", 10, "City")
    match.computeWinner()
    assert match.getWinner() == "Ann"


def test_tie_broken_by_the_first_kind_with_a_clear_leader():
    match = started_match(["Ann", "Bob"])
    _add_entry(match, "Ann", 10, "City")
    _add_entry(match, "Bob", 10, "City")  # tied on City -- no elimination yet
    _add_entry(match, "Ann", 5, "Road")
    _add_entry(match, "Bob", 3, "Road")  # Bob loses on Road -> eliminated
    _add_entry(match, "Bob", 2, "Field")  # brings totals back to a 15-15 tie

    match.computeWinner()
    assert match.totalScores == {"Ann": 15, "Bob": 15}
    assert match.getWinner() == "Ann"


def test_ultimate_tie_picks_the_last_candidate():
    """Every kind is tied (nothing scored beyond City), so the cascade never
    narrows the field -- the fallback picks arbitrarily via ``list.pop()``."""
    match = started_match(["Ann", "Bob"])
    _add_entry(match, "Ann", 10, "City")
    _add_entry(match, "Bob", 10, "City")
    match.computeWinner()
    assert match.getWinner() == "Bob"
