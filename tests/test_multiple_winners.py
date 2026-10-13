"""Shared victories: players still tied after every tie-breaker all win.

Covers the match model, persistence, statistics, the board, and the tie rule
of each game.
"""

from core.engine.db import db
from core.registry import registry

PLAYERS = ["Ann", "Bob", "Cy"]


def started_match(game, players=PLAYERS):
    match = registry.create_match(game)
    match.setPlayers(list(players))
    match.startMatch()
    return match


def add_round(match, scores, extras=None):
    """Add a full round through the match's own rules (and winner check)."""
    extras = extras or {}
    rnd = match.createRound(len(match.getRounds()) + 1)
    for player in match.getPlayers():
        rnd.addInfo(player, scores.get(player, 0), extras.get(player, {}))
    match.addRound(rnd)
    return rnd


def add_entry(match, player, score, extras=None):
    """Append a single-player entry, folding it into the totals."""
    entry = match.createRound(len(match.rounds) + 1)
    entry.addInfo(player, score, extras or {})
    match.rounds.append(entry)
    match.totalScores[player] += score
    return entry


# --- Match model ----------------------------------------------------------------


def test_winners_are_kept_in_playing_order():
    match = started_match("Ratuki")
    match.setWinners(["Cy", "Ann"])
    assert match.getWinners() == ["Ann", "Cy"]
    assert match.getWinner() == "Ann"
    assert match.isWinner("Cy") and not match.isWinner("Bob")


def test_a_single_winner_still_works():
    match = started_match("Ratuki")
    match.winner = "Bob"
    assert match.getWinners() == ["Bob"]
    match.winner = None
    assert match.getWinners() == []
    assert match.getWinner() is None


def play_shared_ratuki():
    """Finish a Ratuki match in which Ann and Cy tie on 100."""
    engine = registry.create_engine("Ratuki")
    for player in PLAYERS:
        engine.addPlayer(player)
    engine.begin()
    engine.openRound(1)
    engine.setRoundWinner("Ann")
    for player, score in zip(PLAYERS, (100, 40, 100), strict=True):
        engine.addRoundInfo(player, score)
    engine.commitRound()
    return engine


def test_every_winner_is_persisted(gamedb):
    engine = play_shared_ratuki()
    assert engine.getWinners() == ["Ann", "Cy"]
    rows = db.queryDict(
        "SELECT nick, winner FROM MatchPlayer WHERE idMatch=? ORDER BY nick;",
        (engine.match.idMatch,),
    )
    assert {r["nick"]: r["winner"] for r in rows} == {"Ann": 1, "Bob": 0, "Cy": 1}


def test_stats_count_a_victory_for_each_winner(gamedb):
    play_shared_ratuki()
    stats = registry.create_stats_engine("Ratuki")
    stats.update()
    victories = {r["nick"]: r["victories"] for r in stats.getPlayerGameStats("Ratuki")}
    assert victories == {"Ann": 1, "Bob": 0, "Cy": 1}
    lastwinner = stats.getGameStats("Ratuki")["lastwinner"]
    assert sorted(lastwinner.split(", ")) == ["Ann", "Cy"]

    particular = registry.create_particular_stats_engine("Ratuki")
    particular.update(PLAYERS)
    lastwinner = particular.getGameStats("Ratuki")["lastwinner"]
    assert sorted(lastwinner.split(", ")) == ["Ann", "Cy"]


def test_last_winner_is_from_the_latest_match(gamedb):
    play_shared_ratuki()
    engine = registry.create_engine("Ratuki")
    for player in PLAYERS:
        engine.addPlayer(player)
    engine.begin()
    engine.openRound(1)
    engine.setRoundWinner("Bob")
    for player, score in zip(PLAYERS, (10, 120, 30), strict=True):
        engine.addRoundInfo(player, score)
    engine.commitRound()

    stats = registry.create_stats_engine("Ratuki")
    stats.update()
    assert stats.getGameStats("Ratuki")["lastwinner"] == "Bob"


def test_board_announces_and_marks_every_winner(gamedb, qapp):
    widget = registry.create_widget("Ratuki", PLAYERS, None, None)
    gi = widget.gameInput
    for player, score in zip(PLAYERS, (100, 40, 100), strict=True):
        gi.playerInputList[player].scoreSpinBox.setValue(score)
    gi.playerInputList["Ann"].setWinner()
    widget.commitRound()

    assert widget.isFinished()
    assert widget.gameStatusLabel.text() == "Ann, Cy share the victory!"
    boxes = widget.playerGroupBox
    assert boxes["Ann"].background is boxes["Ann"].winnerPixmap
    assert boxes["Cy"].background is boxes["Cy"].winnerPixmap
    assert boxes["Bob"].background is not boxes["Bob"].winnerPixmap


# --- Each game's tie rule ---------------------------------------------------------


def test_ratuki_tie_over_the_top():
    match = started_match("Ratuki")
    match.totalScores = {"Ann": 110, "Bob": 110, "Cy": 90}
    match.computeWinner()
    assert match.getWinners() == ["Ann", "Bob"]


def test_toma6_tie_on_the_lowest_score():
    match = started_match("Toma6")
    match.totalScores = {"Ann": 70, "Bob": 20, "Cy": 20}
    match.computeWinner()
    assert match.getWinners() == ["Bob", "Cy"]


def test_skullking_tie_after_the_last_hand():
    match = started_match("Skull King")
    match.totalScores = {"Ann": 300, "Bob": 120, "Cy": 300}
    for _ in range(match.maxRounds):
        match.rounds.append(match.createRound(len(match.rounds) + 1))
    match.computeWinner()
    assert match.getWinners() == ["Ann", "Cy"]


def test_qwirkle_tie_after_every_tie_breaker():
    match = started_match("Qwirkle")
    add_entry(match, "Ann", 50, {"qwirkles": 1})
    add_entry(match, "Bob", 50, {"qwirkles": 1})
    add_entry(match, "Cy", 20, {"qwirkles": 0})
    match.computeWinner()
    assert match.getWinners() == ["Ann", "Bob"]


def test_scrabble_tie_after_every_tie_breaker():
    match = started_match("Scrabble")
    add_entry(match, "Ann", 30, {})
    add_entry(match, "Cy", 30, {})
    match.computeWinner()
    assert match.getWinners() == ["Ann", "Cy"]


def test_catan_tie_with_equal_last_round_gains(gamedb):
    match = started_match("Catan", ["Ann", "Bob"])
    add_round(
        match,
        {"Ann": 8, "Bob": 8},
        {
            "Ann": {"settlements": 2, "cities": 2},
            "Bob": {"settlements": 2, "cities": 2},
        },
    )  # both on 10, both gained 8 this round
    assert match.getWinners() == ["Ann", "Bob"]


def test_azul_tie_on_score_and_rows(gamedb):
    match = started_match("Azul", ["Ann", "Bob"])
    add_round(match, {"Ann": 20, "Bob": 20})
    add_round(
        match,
        {"Ann": 7, "Bob": 7},
        {"Ann": {"rows": 1}, "Bob": {"rows": 1}},
    )
    assert match.getWinners() == ["Ann", "Bob"]


def test_azul_summer_pavilion_tie(gamedb):
    match = started_match("Azul Summer Pavilion", ["Ann", "Bob"])
    for _ in range(6):
        add_round(match, {"Ann": 10, "Bob": 10})
    assert match.getWinners() == ["Ann", "Bob"]
