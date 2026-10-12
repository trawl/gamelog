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


def test_players_start_with_the_setup_settlements():
    match = started_match()
    assert match.totalScores == {"Ann": 2, "Bob": 2}
    assert match.getPlayerState("Ann")["settlements"] == 2
    assert match.victoryPoints(match.getInitialState()) == 2


def test_player_state_adds_round_changes_to_setup():
    match = started_match()
    add_round(match, {"Ann": {"settlements": -1, "cities": 1, "longestroad": 1}})
    assert match.getPlayerState("Ann") == {
        "settlements": 1,
        "cities": 1,
        "longestroad": 1,
        "largestarmy": 0,
        "vpcards": 0,
    }
    assert match.totalScores == {"Ann": 5, "Bob": 2}


# --- Winner -----------------------------------------------------------------


def test_no_winner_below_top(gamedb):
    match = started_match()
    add_round(match, {"Ann": {"settlements": 3, "cities": 2}})  # 9 points
    assert match.getWinner() is None


def test_reaching_top_wins(gamedb):
    match = started_match()
    add_round(match, {"Ann": {"settlements": 2, "cities": 2}})  # 8 points
    add_round(match, {"Ann": {"largestarmy": 1}})  # 10 points
    assert match.getWinner() == "Ann"


def test_tie_over_top_goes_to_last_round_gainer(gamedb):
    match = started_match()
    add_round(
        match,
        {
            "Ann": {"settlements": 3, "cities": 2},  # 9
            "Bob": {"settlements": 2, "cities": 2},  # 8
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
            "Ann": {"settlements": 3, "cities": 3},  # 11
            "Bob": {"settlements": 2, "cities": 3},  # 10
        },
    )
    assert match.getWinner() == "Ann"


# --- Persistence --------------------------------------------------------------


def test_round_roundtrip(gamedb):
    engine = registry.create_engine("Catan")
    for player in PLAYERS:
        engine.addPlayer(player)
    engine.begin()
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
    assert len(resumed.getRounds()) == 2
    assert resumed.getScoreFromPlayer("Ann") == 8
    assert resumed.getScoreFromPlayer("Bob") == 4
    assert resumed.getPlayerState("Ann") == engine.getPlayerState("Ann")
    assert resumed.getPlayerState("Bob") == engine.getPlayerState("Bob")
    assert resumed.getRounds()[1].getChanges("Ann")["longestroad"] == 1


# --- Holdings tracker widget ---------------------------------------------------


def make_widget():
    return registry.create_widget("Catan", PLAYERS, None, None)


def test_board_starts_with_the_setup_settlements(gamedb, qapp):
    widget = make_widget()
    assert widget.engine.getScoreFromPlayer("Ann") == 2
    states = widget.gameInput.getStates()
    assert all(state["settlements"] == 2 for state in states.values())
    assert not widget.gameInput.hasChanges()
    assert not widget.commitRoundSanityCheck()


def test_each_edit_is_committed_at_once(gamedb, qapp):
    from PySide6.QtCore import Qt
    from PySide6.QtTest import QTest

    widget = make_widget()
    assert widget.commitRoundButton.isHidden()
    ann = widget.gameInput.playerInputList["Ann"]
    button = ann.bonusButtons["settlements"]
    QTest.mouseClick(button, Qt.MouseButton.LeftButton)
    assert widget.engine.getScoreFromPlayer("Ann") == 3
    assert button.count == 3
    QTest.mouseClick(button, Qt.MouseButton.RightButton)
    QTest.mouseClick(button, Qt.MouseButton.RightButton)
    assert widget.engine.getScoreFromPlayer("Ann") == 1
    assert button.count == 1
    assert len(widget.engine.getRounds()) == 3
    assert not widget.gameInput.hasChanges()


def test_undo_reverts_the_last_edit_without_asking(gamedb, qapp):
    widget = make_widget()
    ann = widget.gameInput.playerInputList["Ann"]
    ann.stepCounter("cities", 1)
    assert widget.engine.getScoreFromPlayer("Ann") == 3
    widget.undoCommit()
    assert widget.engine.getRounds() == []
    assert widget.engine.getScoreFromPlayer("Ann") == 2
    assert ann.getState()["cities"] == 0
    assert ann.bonusButtons["settlements"].count == 2


def test_city_replaces_a_settlement(gamedb, qapp):
    widget = make_widget()
    ann = widget.gameInput.playerInputList["Ann"]
    ann.stepCounter("cities", 1)
    assert ann.getState()["cities"] == 1
    assert ann.getState()["settlements"] == 1
    assert widget.engine.getScoreFromPlayer("Ann") == 3

    ann.stepCounter("cities", 1)
    ann.stepCounter("cities", 1)  # no settlement left to upgrade
    assert ann.getState()["cities"] == 2
    assert ann.getState()["settlements"] == 0
    assert len(widget.engine.getRounds()) == 2

    ann.stepCounter("cities", -1)  # undoing an upgrade gives it back
    assert ann.getState()["cities"] == 1
    assert ann.getState()["settlements"] == 1


def test_counters_respect_piece_limits(gamedb, qapp):
    widget = make_widget()
    ann = widget.gameInput.playerInputList["Ann"]
    for _ in range(10):
        ann.stepCounter("settlements", 1)
    assert ann.getState()["settlements"] == 5
    for _ in range(10):
        ann.stepCounter("settlements", -1)
    assert ann.getState()["settlements"] == 0


def test_awards_have_a_single_holder(gamedb, qapp):
    widget = make_widget()
    ann = widget.gameInput.playerInputList["Ann"]
    bob = widget.gameInput.playerInputList["Bob"]
    ann.bonusButtons["longestroad"].click()
    assert widget.engine.getScoreFromPlayer("Ann") == 4

    bob.bonusButtons["longestroad"].click()  # one round: Bob takes it from Ann
    assert len(widget.engine.getRounds()) == 2
    assert ann.getState()["longestroad"] == 0
    assert ann.bonusButtons["longestroad"].count == 0
    assert widget.engine.getScoreFromPlayer("Ann") == 2
    assert widget.engine.getScoreFromPlayer("Bob") == 4
    last = widget.engine.getRounds()[-1]
    assert last.getPlayerScore("Ann") == -2
    assert last.getWinner() == "Bob"


def test_custom_player_colours(gamedb, qapp):
    widget = make_widget()
    assert widget.playerColour("Ann").name() == "#f37c21"  # orange
    assert widget.playerColour("Bob").name() == "#969696"  # white, drawn grey


def test_reaching_top_finishes_the_match(gamedb, qapp):
    widget = make_widget()
    ann = widget.gameInput.playerInputList["Ann"]
    for _ in range(3):
        ann.stepCounter("settlements", 1)
    for _ in range(4):
        ann.stepCounter("cities", 1)
    ann.toggleAward("largestarmy")  # 1 + 8 + 2 = 11
    assert widget.engine.getWinner() == "Ann"
    assert widget.isFinished()


def test_player_boxes_use_at_most_three_columns(gamedb, qapp):
    expected = {2: [2], 3: [3], 4: [2, 2], 5: [3, 2], 6: [3, 3]}
    names = ["Ann", "Bob", "Cy", "Dee", "Eve", "Fay"]
    for count, row_sizes in expected.items():
        widget = registry.create_widget("Catan", names[:count], None, None)
        layout = widget.gameInput.widgetLayout
        rows: dict[int, int] = {}
        for i in range(layout.count()):
            row, _, _, _ = layout.getItemPosition(i)
            rows[row] = rows.get(row, 0) + 1
        assert [rows[r] for r in sorted(rows)] == row_sizes, count


# --- Round table ----------------------------------------------------------------


def test_city_upgrade_is_shown_as_the_city_alone():
    from games.catan.widget import shownChanges

    zero: dict[str, int] = dict.fromkeys(
        ("settlements", "cities", "longestroad", "largestarmy", "vpcards"), 0
    )
    assert shownChanges({**zero, "settlements": -1, "cities": 1}) == {"cities": 1}
    assert shownChanges({**zero, "settlements": 1}) == {"settlements": 1}
    assert shownChanges(zero) == {}


def test_round_cell_lists_gained_and_lost_pieces():
    from games.catan.widget import CatanChangesDelegate

    parts = CatanChangesDelegate._parts(-1, {"vpcards": 2, "longestroad": -1})
    assert parts == ["-1", "2", ("vpcards", True), ("longestroad", False)]
