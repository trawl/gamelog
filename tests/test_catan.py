"""Catan-specific rules: victory points from holdings, the target-points
winner, persistence of holding changes, and the holdings tracker widget
(cities replace settlements, awards have a single holder)."""

from core.registry import registry

PLAYERS = ["Ann", "Bob"]


def started_match(players=PLAYERS):
    match = registry.create_match("Catan")
    match.setPlayers(list(players))
    match.startMatch()
    return match


def add_round(match, changes):
    rnd = match.createRound(len(match.getRounds()) + 1)
    for player in match.getPlayers():
        delta = changes.get(player, {})
        rnd.addInfo(player, match.victoryPoints(delta), delta)
    match.addRound(rnd)
    return rnd


# --- Victory points and holdings ---------------------------------------------


def test_victory_points_weigh_each_holding():
    match = started_match()
    state = {
        "settlements": 3,
        "cities": 2,
        "longestroad": 1,
        "largestarmy": 1,
        "vpcards": 1,
    }
    assert match.victoryPoints(state) == 3 + 4 + 2 + 2 + 1


def test_player_state_sums_round_changes():
    match = started_match()
    add_round(match, {"Ann": {"settlements": 2}, "Bob": {"settlements": 2}})
    add_round(match, {"Ann": {"settlements": -1, "cities": 1, "longestroad": 1}})
    assert match.getPlayerState("Ann") == {
        "settlements": 1,
        "cities": 1,
        "longestroad": 1,
        "largestarmy": 0,
        "vpcards": 0,
    }
    assert match.totalScores == {"Ann": 5, "Bob": 2}


def test_initial_state_has_the_setup_settlements():
    match = started_match()
    assert match.getInitialState()["settlements"] == 2
    assert match.victoryPoints(match.getInitialState()) == 2


# --- Winner -----------------------------------------------------------------


def test_no_winner_below_top(gamedb):
    match = started_match()
    add_round(match, {"Ann": {"settlements": 5, "cities": 2}})  # 9 points
    assert match.getWinner() is None


def test_reaching_top_wins(gamedb):
    match = started_match()
    add_round(match, {"Ann": {"settlements": 4, "cities": 2}})  # 8 points
    add_round(match, {"Ann": {"largestarmy": 1}})  # 10 points
    assert match.getWinner() == "Ann"


def test_tie_over_top_goes_to_last_round_gainer(gamedb):
    match = started_match()
    add_round(
        match,
        {
            "Ann": {"settlements": 5, "cities": 2},  # 9
            "Bob": {"settlements": 4, "cities": 2},  # 8
        },
    )
    add_round(
        match,
        {"Ann": {"vpcards": 1}, "Bob": {"longestroad": 1}},
    )  # both on 10, Bob gained more this round
    assert match.getWinner() == "Bob"


def test_highest_score_over_top_wins(gamedb):
    match = started_match()
    add_round(
        match,
        {
            "Ann": {"settlements": 5, "cities": 3},  # 11
            "Bob": {"settlements": 4, "cities": 3},  # 10
        },
    )
    assert match.getWinner() == "Ann"


def test_custom_top(gamedb):
    match = started_match()
    match.setTop(12)
    add_round(match, {"Ann": {"settlements": 4, "cities": 3}})  # 10 points
    assert match.getWinner() is None


# --- Persistence --------------------------------------------------------------


def test_round_roundtrip(gamedb):
    engine = registry.create_engine("Catan")
    for player in PLAYERS:
        engine.addPlayer(player)
    engine.begin()
    engine.setTop(12)
    engine.openRound(1)
    engine.addRoundInfo("Ann", 4, {"settlements": 1, "cities": 1, "vpcards": 1})
    engine.addRoundInfo("Bob", 2, {"settlements": 2})
    engine.commitRound()
    engine.openRound(2)
    engine.addRoundInfo("Ann", 2, {"longestroad": 1})
    engine.addRoundInfo("Bob", 0, {})
    engine.commitRound()
    engine.save()

    resumed = registry.create_engine("Catan")
    assert resumed.resume(engine.match.idMatch)
    assert resumed.getTop() == 12
    assert len(resumed.getRounds()) == 2
    assert resumed.getScoreFromPlayer("Ann") == 6
    assert resumed.getScoreFromPlayer("Bob") == 2
    assert resumed.getPlayerState("Ann") == engine.getPlayerState("Ann")
    assert resumed.getPlayerState("Bob") == engine.getPlayerState("Bob")
    assert resumed.getRounds()[1].getChanges("Ann")["longestroad"] == 1


# --- Holdings tracker widget ---------------------------------------------------


def make_widget():
    return registry.create_widget("Catan", PLAYERS, None, None)


def test_first_round_starts_with_setup_settlements(qapp, gamedb):
    widget = make_widget()
    states = widget.gameInput.getStates()
    assert all(state["settlements"] == 2 for state in states.values())
    assert widget.commitRoundSanityCheck()
    widget.commitRound()
    assert widget.engine.getScoreFromPlayer("Ann") == 2
    assert not widget.gameInput.hasChanges()
    assert not widget.commitRoundSanityCheck()


def test_city_replaces_a_settlement(qapp, gamedb):
    widget = make_widget()
    ann = widget.gameInput.playerInputList["Ann"]
    ann.stepCounter("cities", 1)
    assert ann.getState()["cities"] == 1
    assert ann.getState()["settlements"] == 1
    assert ann.getScore() == 3

    ann.stepCounter("cities", 1)
    ann.stepCounter("cities", 1)  # no settlement left to upgrade
    assert ann.getState()["cities"] == 2
    assert ann.getState()["settlements"] == 0

    ann.stepCounter("cities", -1)  # undoing an upgrade gives it back
    assert ann.getState()["cities"] == 1
    assert ann.getState()["settlements"] == 1


def test_counters_respect_piece_limits(qapp, gamedb):
    widget = make_widget()
    ann = widget.gameInput.playerInputList["Ann"]
    for _ in range(10):
        ann.stepCounter("settlements", 1)
    assert ann.getState()["settlements"] == 5
    for _ in range(10):
        ann.stepCounter("settlements", -1)
    assert ann.getState()["settlements"] == 0


def test_awards_have_a_single_holder(qapp, gamedb):
    widget = make_widget()
    widget.commitRound()  # setup round
    ann = widget.gameInput.playerInputList["Ann"]
    bob = widget.gameInput.playerInputList["Bob"]
    ann.awardButtons["longestroad"].setChecked(True)
    widget.commitRound()
    assert widget.engine.getScoreFromPlayer("Ann") == 4

    bob.awardButtons["longestroad"].setChecked(True)
    assert ann.getState()["longestroad"] == 0
    assert ann.getScore() == -2
    assert bob.getScore() == 2
    widget.commitRound()
    assert widget.engine.getScoreFromPlayer("Ann") == 2
    assert widget.engine.getScoreFromPlayer("Bob") == 4
    assert widget.engine.getRounds()[-1].getWinner() == "Bob"


def test_reaching_top_finishes_the_match(qapp, gamedb):
    widget = make_widget()
    ann = widget.gameInput.playerInputList["Ann"]
    for _ in range(3):
        ann.stepCounter("settlements", 1)
    for _ in range(4):
        ann.stepCounter("cities", 1)
    ann.awardButtons["largestarmy"].setChecked(True)  # 1 + 8 + 2 = 11
    widget.commitRound()
    assert widget.engine.getWinner() == "Ann"
    assert widget.isFinished()
