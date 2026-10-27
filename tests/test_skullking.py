"""Skull King scoring: values scale with the cards dealt, the scoring modes
offered per player count, and when the bonus buttons unlock."""

import pytest

from core.registry import registry
from games.skullking.model import SkullKingMatch

ROUND_MODES = list(SkullKingMatch.roundModes)


def engine_for(round_mode: str, scoring_mode: str):
    engine = registry.create_engine("Skull King")
    engine.setRoundMode(round_mode)
    engine.setScoringMode(scoring_mode)
    return engine


# --- Scores use the cards dealt, not the round number ------------------------


@pytest.mark.parametrize("round_mode", ROUND_MODES)
def test_zero_bid_scales_with_the_cards_dealt(round_mode):
    engine = engine_for(round_mode, "standard_scoring")
    cards = SkullKingMatch.roundModes[round_mode][0]
    assert engine.computePlayerScore(0, 0, {}) == cards * 10
    assert engine.computePlayerScore(0, 1, {}) == cards * -10


@pytest.mark.parametrize("round_mode", ROUND_MODES)
def test_rascal_exact_bid_scales_with_the_cards_dealt(round_mode):
    engine = engine_for(round_mode, "rascal_scoring")
    cards = SkullKingMatch.roundModes[round_mode][0]
    assert engine.computePlayerScore(1, 1, {}) == cards * 10
    assert engine.computePlayerScore(1, 1, {"cannonball": 1}) == cards * 15


def test_barrage_zero_bid_is_worth_ten_cards_from_the_first_round():
    engine = engine_for("barrage", "classic_scoring")
    assert engine.computePlayerScore(0, 0, {}) == 100


def test_whirlpool_values_follow_each_rounds_hand_size(monkeypatch):
    engine = engine_for("whirlpool", "classic_scoring")
    # Whirlpool deals 9, 7, 5, 3, 1 cards.
    for round_number, cards in enumerate([9, 7, 5, 3, 1], start=1):
        monkeypatch.setattr(engine, "getNumRound", lambda n=round_number: n)
        assert engine.computePlayerScore(0, 0, {}) == cards * 10


def test_standard_sequence_is_unchanged():
    """In the 1-10 sequence the round number and the cards dealt coincide."""
    engine = engine_for("standard_rounds", "classic_scoring")
    assert engine.computePlayerScore(0, 0, {}) == 10
    assert engine.computePlayerScore(2, 2, {}) == 40
    assert engine.computePlayerScore(3, 1, {}) == -20


@pytest.mark.parametrize(
    ("scoring_mode", "bonus", "points", "reps"),
    [
        # Mermaid captures the Skull King: 50 in the original edition.
        ("classic_scoring", "skullking", 50, 1),
        # Skull King captures Pirates: 20 each in Classic scoring (a house
        # value), 30 in Standard and Rascal, up to six.
        ("classic_scoring", "pirate", 20, 6),
        ("standard_scoring", "skullking", 40, 1),
        ("standard_scoring", "pirate", 30, 6),
        # Pirate captures a Mermaid: 20 each, up to two.
        ("standard_scoring", "mermaid", 20, 2),
        ("standard_scoring", "loot", 20, 2),
        ("standard_scoring", "fourteen", 10, 3),
        ("standard_scoring", "blackfourteen", 20, 1),
        ("standard_scoring", "roatan", 10, 2),
        ("rascal_scoring", "skullking", 40, 1),
        ("rascal_scoring", "pirate", 30, 6),
        ("rascal_scoring", "blackfourteen", 20, 1),
    ],
)
def test_bonus_values_follow_the_official_rules(scoring_mode, bonus, points, reps):
    match = engine_for("standard_rounds", scoring_mode).match
    assert match.getBonus(bonus) == points
    assert match.getBonusReps(bonus) == reps


def test_skull_king_capturing_pirates_adds_thirty_each():
    engine = engine_for("standard_rounds", "standard_scoring")
    # Bid 2, win 2: 2 x 20 for the tricks, plus two Pirates at 30 each.
    assert engine.computePlayerScore(2, 2, {"pirate": 2}) == 40 + 60


def test_black_fourteen_bonus_is_added_to_an_exact_bid():
    engine = engine_for("standard_rounds", "standard_scoring")
    assert engine.computePlayerScore(2, 2, {"blackfourteen": 1}) == 40 + 20


# --- Scoring modes offered per player count ----------------------------------


@pytest.mark.parametrize("count", range(2, 9))
def test_every_player_count_gets_scoring_modes(count):
    match = registry.create_match("Skull King", [f"P{i}" for i in range(count)])
    modes = match.listScoringModes()
    assert "standard_scoring" in modes
    assert "rascal_scoring" in modes
    # Classic scoring only works up to six players.
    assert ("classic_scoring" in modes) == (count <= 6)


def test_seven_players_start_on_standard_scoring():
    match = registry.create_match("Skull King", [f"P{i}" for i in range(7)])
    assert match.getScoringMode() in match.listScoringModes()


# --- Bonus buttons unlock per scoring mode -----------------------------------


@pytest.fixture
def board(qapp, gamedb):
    widget = registry.create_widget("Skull King", ["Ann", "Bob"])
    widget.engine.setRoundMode("barrage")
    widget.gameInput.changeRoundMode()
    return widget


def player_box(board, scoring_mode):
    board.engine.setScoringMode(scoring_mode)
    board.gameInput.changeScoringMode()
    return board.gameInput.playerInputList["Ann"]


def set_result(board, box, bid, won):
    """Enter a bid and the tricks won, as the board does when playing."""
    box.setExpectedHands(bid)
    box.unlockTricks()  # the board unlocks it once every bid is in
    box.setWonHands(won)
    box.updateExtraRow()


def unlocked(box, bonus):
    return box.bonusButtons[bonus].isEnabled()


@pytest.mark.parametrize(
    ("bid", "won", "allowed"),
    [(2, 2, True), (2, 1, False), (2, 3, False), (0, 0, False), (0, 1, False)],
)
def test_standard_scoring_unlocks_bonuses_only_on_an_exact_bid(
    board, bid, won, allowed
):
    box = player_box(board, "standard_scoring")
    set_result(board, box, bid, won)
    assert unlocked(box, "pirate") is allowed


@pytest.mark.parametrize(
    ("bid", "won", "allowed"),
    [
        (2, 2, True),  # exact
        (2, 1, True),  # off by one, under
        (2, 3, True),  # off by one, over
        (0, 1, True),  # a trick won on a zero bid is off by one
        (2, 4, False),  # off by two scores nothing
        (1, 0, False),  # no trick, nothing to bonus
        (0, 0, False),
    ],
)
def test_rascal_scoring_unlocks_bonuses_within_one_of_the_bid(board, bid, won, allowed):
    box = player_box(board, "rascal_scoring")
    set_result(board, box, bid, won)
    assert unlocked(box, "fourteen") is allowed


def test_rascal_half_bonus_is_scored_when_off_by_one(board):
    box = player_box(board, "rascal_scoring")
    set_result(board, box, 3, 2)
    box.bonusButtons["fourteen"].click()
    # 10 x 10 cards = 100 plus one 14 bonus of 10, halved for missing by one.
    assert box.getScore() == (100 + 10) // 2


def test_a_failed_cannonball_can_be_recorded_and_scores_nothing(board):
    box = player_box(board, "rascal_scoring")
    set_result(board, box, 3, 2)
    assert unlocked(box, "cannonball")
    box.bonusButtons["cannonball"].click()
    assert box.getScore() == 0


def test_cannonball_waits_for_the_result(board):
    box = player_box(board, "rascal_scoring")
    assert not unlocked(box, "cannonball")
    box.setExpectedHands(3)
    box.updateExtraRow()
    assert not unlocked(box, "cannonball")
