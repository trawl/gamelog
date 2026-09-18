"""Phase 10-specific rules: the deeper winner tie-break levels (score, then
last-round score, then random) and phase bookkeeping when a round is added
or undone."""

from core.registry import registry
from games.phase10 import model as phase10_model


def started_match(players):
    match = registry.create_match("Phase10")
    match.setPlayers(list(players))
    match.startMatch()
    return match


def _add_round(match, scores, completed):
    """Append a round with each player's score and whether they cleared phase 1."""
    rnd = match.createRound(len(match.rounds) + 1)
    for player, score in scores.items():
        rnd.addInfo(
            player,
            score,
            {"aimedPhase": 1, "isCompleted": completed.get(player, False)},
        )
    match.rounds.append(rnd)
    return rnd


# --- computeWinner: score tie broken by last-round score, then at random -----


def test_tie_broken_by_last_round_score():
    match = started_match(["Ann", "Bob", "Cy"])
    match.phasesCleared = {p: list(range(1, 11)) for p in ["Ann", "Bob", "Cy"]}
    match.totalScores = {"Ann": 100, "Bob": 100, "Cy": 200}
    _add_round(match, {"Ann": 5, "Bob": 8, "Cy": 5}, {})
    match.computeWinner()
    assert match.getWinner() == "Ann"  # same total as Bob, but a lower last round


def test_ultimate_tie_is_broken_at_random(monkeypatch):
    match = started_match(["Ann", "Bob"])
    match.phasesCleared = {p: list(range(1, 11)) for p in ["Ann", "Bob"]}
    match.totalScores = {"Ann": 100, "Bob": 100}
    _add_round(match, {"Ann": 5, "Bob": 5}, {})

    monkeypatch.setattr(phase10_model.random, "choice", lambda seq: seq[-1])
    match.computeWinner()
    assert match.getWinner() == "Bob"


def test_no_winner_until_someone_clears_all_ten_phases():
    match = started_match(["Ann", "Bob"])
    match.phasesCleared = {"Ann": list(range(1, 10)), "Bob": [1, 2]}
    match.totalScores = {"Ann": 50, "Bob": 20}
    match.computeWinner()
    assert not match.getWinner()


# --- Round bookkeeping: clearing / un-clearing a phase -----------------------


def test_playerAddRound_records_the_cleared_phase():
    match = started_match(["Ann", "Bob"])
    rnd = _add_round(match, {"Ann": 0, "Bob": 15}, {"Ann": True, "Bob": False})
    for player in rnd.getScore():
        match.playerAddRound(player, rnd)
    assert match.phasesCleared["Ann"] == [1]
    assert match.phasesCleared["Bob"] == []


def test_delete_round_reverts_the_cleared_phase():
    match = started_match(["Ann", "Bob"])
    rnd = _add_round(match, {"Ann": 0, "Bob": 15}, {"Ann": True, "Bob": False})
    match.playerAddRound("Ann", rnd)
    match.playerAddRound("Bob", rnd)
    assert match.phasesCleared["Ann"] == [1]

    match.deleteRound(1)
    assert match.phasesCleared["Ann"] == []
