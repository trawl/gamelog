"""Azul-specific rules: the game ends on a round with a complete row, bonuses
score 2/7/10 and only from round 5, scores never drop below zero, ties go to
more complete rows, and bonuses survive a save/resume."""

from core.registry import registry

PLAYERS = ["Ann", "Bob"]


def started_match(players=PLAYERS):
    match = registry.create_match("Azul")
    match.setPlayers(list(players))
    match.startMatch()
    return match


def add_round(match, scores, bonuses=None):
    bonuses = bonuses or {}
    rnd = match.createRound(len(match.getRounds()) + 1)
    for player in match.getPlayers():
        extra = bonuses.get(player, {})
        rnd.addInfo(player, scores[player] + match.bonusPoints(extra), extra)
    match.addRound(rnd)
    return rnd


# --- Rules ----------------------------------------------------------------------


def test_bonus_points():
    match = started_match()
    assert match.bonusPoints({"rows": 1, "columns": 2, "colours": 1}) == 2 + 14 + 10


def test_no_winner_without_a_complete_row(gamedb):
    match = started_match()
    for _ in range(6):
        add_round(match, {"Ann": 10, "Bob": 5})
    assert match.getWinner() is None


def test_complete_row_ends_the_game(gamedb):
    match = started_match()
    add_round(match, {"Ann": 20, "Bob": 30})
    add_round(
        match,
        {"Ann": 10, "Bob": 5},
        {"Ann": {"rows": 1, "colours": 1}, "Bob": {"columns": 1}},
    )  # Ann 20 + 10 + 12 = 42, Bob 30 + 5 + 7 = 42
    assert match.totalScores == {"Ann": 42, "Bob": 42}
    assert match.getWinner() == "Ann"  # tie broken by complete rows


def test_highest_score_wins_even_without_the_row(gamedb):
    match = started_match()
    add_round(match, {"Ann": 5, "Bob": 40})
    add_round(match, {"Ann": 5, "Bob": 5}, {"Ann": {"rows": 1}})
    assert match.getWinner() == "Bob"


def test_score_never_drops_below_zero():
    match = started_match()
    add_round(match, {"Ann": 3, "Bob": 0})
    rnd = add_round(match, {"Ann": -8, "Bob": -2})
    assert match.totalScores == {"Ann": 0, "Bob": 0}
    assert rnd.getPlayerScore("Ann") == -3


# --- Persistence --------------------------------------------------------------


def test_round_roundtrip(gamedb):
    engine = registry.create_engine("Azul")
    for player in PLAYERS:
        engine.addPlayer(player)
    engine.begin()
    engine.openRound(1)
    engine.addRoundInfo("Ann", 12, {})
    engine.addRoundInfo("Bob", 8, {})
    engine.commitRound()
    engine.openRound(2)
    engine.addRoundInfo("Ann", 7, {"columns": 1})
    engine.addRoundInfo("Bob", 3, {})
    engine.commitRound()
    engine.save()

    resumed = registry.create_engine("Azul")
    assert resumed.resume(engine.match.idMatch)
    assert len(resumed.getRounds()) == 2
    assert resumed.getScoreFromPlayer("Ann") == 19
    assert resumed.getScoreFromPlayer("Bob") == 11
    assert resumed.getRounds()[1].getBonuses("Ann") == {
        "rows": 0,
        "columns": 1,
        "colours": 0,
    }


# --- Widget ---------------------------------------------------------------------


def make_widget():
    return registry.create_widget("Azul", PLAYERS, None, None)


def enter_round(widget, scores):
    for player, score in scores.items():
        widget.gameInput.playerInputList[player].scoreSpinBox.setValue(score)
    widget.commitRound()


def test_every_score_is_needed_to_commit(gamedb, qapp):
    widget = make_widget()
    assert not widget.commitRoundSanityCheck()
    widget.gameInput.playerInputList["Ann"].scoreSpinBox.setValue(4)
    assert not widget.commitRoundSanityCheck()
    widget.gameInput.playerInputList["Bob"].scoreSpinBox.setValue(0)
    assert widget.commitRoundSanityCheck()


def test_bonuses_unlock_in_round_five(gamedb, qapp):
    widget = make_widget()
    ann = widget.gameInput.playerInputList["Ann"]
    for _ in range(4):
        assert not ann.bonusButtons["rows"].isEnabled()
        enter_round(widget, {"Ann": 5, "Bob": 5})
    assert widget.engine.getNumRound() == 5
    assert all(b.isEnabled() for b in ann.bonusButtons.values())


def test_column_bonus_needs_a_complete_row(gamedb, qapp):
    widget = make_widget()
    for _ in range(4):
        enter_round(widget, {"Ann": 5, "Bob": 5})
    ann = widget.gameInput.playerInputList["Ann"]
    bob = widget.gameInput.playerInputList["Bob"]
    ann.scoreSpinBox.setValue(6)
    bob.scoreSpinBox.setValue(4)
    ann.bonusButtons["columns"].plusone()
    assert not widget.commitRoundSanityCheck()
    bob.bonusButtons["rows"].plusone()
    assert widget.commitRoundSanityCheck()


def test_row_bonus_round_finishes_the_match(gamedb, qapp):
    widget = make_widget()
    for _ in range(4):
        enter_round(widget, {"Ann": 5, "Bob": 6})
    ann = widget.gameInput.playerInputList["Ann"]
    ann.bonusButtons["rows"].plusone()
    ann.bonusButtons["colours"].plusone()
    assert ann.bonusLabel.text() == "+12"
    enter_round(widget, {"Ann": 3, "Bob": 3})  # Ann 20 + 3 + 12 = 35, Bob 27
    assert widget.engine.getScoreFromPlayer("Ann") == 35
    assert widget.engine.getWinner() == "Ann"
    assert widget.isFinished()


def test_bonus_buttons_count_up_and_down(gamedb, qapp):
    from PySide6.QtCore import Qt
    from PySide6.QtTest import QTest

    widget = make_widget()
    for _ in range(4):
        enter_round(widget, {"Ann": 5, "Bob": 6})
    button = widget.gameInput.playerInputList["Ann"].bonusButtons["columns"]
    QTest.mouseClick(button, Qt.MouseButton.LeftButton)
    QTest.mouseClick(button, Qt.MouseButton.LeftButton)
    assert button.getValue() == 2
    QTest.mouseClick(button, Qt.MouseButton.RightButton)
    assert button.getValue() == 1
    assert widget.gameInput.playerInputList["Ann"].bonusLabel.text() == "+7"


# --- Statistics -------------------------------------------------------------------


def play_finished_match(players, bonuses):
    """Play two rounds; the second carries ``bonuses`` and ends the match."""
    engine = registry.create_engine("Azul")
    for player in players:
        engine.addPlayer(player)
    engine.begin()
    for numround, extras in ((1, {}), (2, bonuses)):
        engine.openRound(numround)
        for player in players:
            extra = extras.get(player, {})
            engine.addRoundInfo(player, 10 + engine.bonusPoints(extra), extra)
        engine.commitRound()
    assert engine.getWinner()
    return engine


def test_stats_show_the_best_bonus_per_match_size_and_player(gamedb):
    play_finished_match(["Ann", "Bob"], {"Ann": {"rows": 1, "columns": 1}})  # 9
    play_finished_match(["Ann", "Bob"], {"Bob": {"rows": 2, "colours": 1}})  # Bob 14
    play_finished_match(
        ["Ann", "Bob", "Cy"], {"Cy": {"rows": 1, "colours": 2}}
    )  # Cy 22

    stats = registry.create_stats_engine("Azul")
    stats.update()
    bymatch = {
        row["nplayers"]: row["maxbonus"] for row in stats.getMatchGameStats("Azul")
    }
    assert bymatch == {2: 14, 3: 22}
    byplayer = {
        row["nick"]: row["maxbonus"] for row in stats.getPlayerGameStats("Azul")
    }
    assert byplayer == {"Ann": 9, "Bob": 14, "Cy": 22}

    particular = registry.create_particular_stats_engine("Azul")
    particular.update(["Ann", "Bob"])
    byplayer = {
        row["nick"]: row["maxbonus"] for row in particular.getPlayerGameStats("Azul")
    }
    assert byplayer == {"Ann": 9, "Bob": 14}


def test_quick_stats_columns(gamedb, qapp):
    from games.azul.widget import AzulQSBox

    box = AzulQSBox("Azul")
    assert "minscore" not in box.playerStatsKeys
    assert "sumscore" not in box.playerStatsKeys
    assert box.playerStatsKeys[-1] == "maxbonus"
    assert box.matchStatsKeys[-1] == "maxbonus"
    assert len(box.playerStatsKeys) == len(box.playerStatsHeaders)


def test_board_opens_on_the_plot(gamedb, qapp):
    widget = make_widget()
    assert widget.detailGroup.currentWidget() is widget.detailGroup.plot


def test_bonus_totals_show_once_the_game_is_over(gamedb, qapp):
    widget = make_widget()
    detail = widget.detailGroup
    for _ in range(4):
        enter_round(widget, {"Ann": 5, "Bob": 6})
    assert detail.totals.isHidden()
    ann = widget.gameInput.playerInputList["Ann"]
    ann.bonusButtons["rows"].plusone()
    ann.bonusButtons["columns"].plusone()
    ann.bonusButtons["columns"].plusone()
    enter_round(widget, {"Ann": 3, "Bob": 3})
    assert not detail.totals.isHidden()
    assert detail.totals.item(0, 0).text() == "1 (+2)"
    assert detail.totals.item(1, 0).text() == "2 (+14)"
    assert detail.totals.item(2, 0).text() == "0"
    assert detail.totals.item(0, 1).text() == "0"


# --- Summer Pavilion ------------------------------------------------------------

SP = "Azul Summer Pavilion"


def started_sp_match(players=PLAYERS):
    match = registry.create_match(SP)
    match.setPlayers(list(players))
    match.startMatch()
    return match


def test_sp_players_start_on_five():
    match = started_sp_match()
    assert match.totalScores == {"Ann": 5, "Bob": 5}


def test_sp_bonus_points():
    match = started_sp_match()
    stars = {"star_multi": 1, "star_purple": 1}
    numbers = {"ones": 1, "fours": 1}
    assert match.bonusPoints({**stars, **numbers}) == 12 + 20 + 4 + 16


def test_sp_ends_after_six_rounds(gamedb):
    match = started_sp_match()
    for _ in range(5):
        add_round(match, {"Ann": 10, "Bob": 12})
    assert match.getWinner() is None
    add_round(match, {"Ann": 10, "Bob": 3}, {"Ann": {"star_red": 1}})
    # Ann 5 + 6 x 10 + 14 = 79, Bob 5 + 5 x 12 + 3 = 68
    assert match.totalScores == {"Ann": 79, "Bob": 68}
    assert match.getWinner() == "Ann"


def test_sp_tie_goes_to_the_first_player(gamedb):
    match = started_sp_match()
    for _ in range(6):
        add_round(match, {"Ann": 10, "Bob": 10})
    assert match.getWinner() == "Ann"


def test_sp_round_roundtrip(gamedb):
    engine = registry.create_engine(SP)
    for player in PLAYERS:
        engine.addPlayer(player)
    engine.begin()
    engine.openRound(1)
    engine.addRoundInfo("Ann", 12, {})
    engine.addRoundInfo("Bob", 8, {})
    engine.commitRound()
    engine.save()

    resumed = registry.create_engine(SP)
    assert resumed.resume(engine.match.idMatch)
    assert resumed.getScoreFromPlayer("Ann") == 17
    assert resumed.getScoreFromPlayer("Bob") == 13
    assert resumed.getRounds()[0].getBonuses("Ann")["star_red"] == 0


def make_sp_widget():
    return registry.create_widget(SP, PLAYERS, None, None)


def test_sp_bonuses_unlock_in_the_last_round_and_end_the_game(gamedb, qapp):
    widget = make_sp_widget()
    ann = widget.gameInput.playerInputList["Ann"]
    for _ in range(5):
        assert not ann.bonusButtons["star_red"].isEnabled()
        enter_round(widget, {"Ann": 10, "Bob": 10})
    assert all(b.isEnabled() for b in ann.bonusButtons.values())
    ann.bonusButtons["star_green"].plusone()
    ann.bonusButtons["threes"].plusone()
    assert ann.bonusLabel.text() == "+30"
    # Star and number bonuses need no row, unlike Azul's column bonus.
    ann.scoreSpinBox.setValue(4)
    widget.gameInput.playerInputList["Bob"].scoreSpinBox.setValue(4)
    assert widget.commitRoundSanityCheck()
    widget.commitRound()
    assert widget.engine.getScoreFromPlayer("Ann") == 5 + 50 + 4 + 30
    assert widget.engine.getWinner() == "Ann"
    totals = widget.detailGroup.totals
    keys = list(widget.engine.getBonuses())
    assert totals.item(keys.index("star_green"), 0).text() == "+18"
    assert totals.item(keys.index("threes"), 0).text() == "+12"
    assert totals.item(keys.index("star_red"), 0).text() == ""


def test_sp_star_buttons_keep_their_own_colour(gamedb, qapp):
    widget = make_sp_widget()
    ann = widget.gameInput.playerInputList["Ann"]
    assert ann.bonusButtons["star_purple"].highlight_colour.name() == "#8a4fc6"
    assert ann.bonusButtons["ones"].highlight_colour == ann.pcolour


def test_stats_keep_the_editions_apart(gamedb):
    play_finished_match(["Ann", "Bob"], {"Ann": {"rows": 1, "columns": 1}})  # 9
    engine = registry.create_engine(SP)
    for player in PLAYERS:
        engine.addPlayer(player)
    engine.begin()
    for numround in range(1, 7):
        engine.openRound(numround)
        extras = {"star_purple": 1} if numround == 6 else {}
        engine.addRoundInfo("Ann", 10 + engine.bonusPoints(extras), extras)
        engine.addRoundInfo("Bob", 10, {})
        engine.commitRound()
    assert engine.getWinner() == "Ann"

    azul = registry.create_stats_engine("Azul")
    azul.update()
    assert {r["nick"]: r["maxbonus"] for r in azul.getPlayerGameStats("Azul")} == {
        "Ann": 9,
        "Bob": 0,
    }
    sp = registry.create_stats_engine(SP)
    sp.update()
    assert {r["nick"]: r["maxbonus"] for r in sp.getPlayerGameStats(SP)} == {
        "Ann": 20,
        "Bob": 0,
    }


def _maxSaturation(widget) -> int:
    image = widget.grab().toImage()
    return max(
        image.pixelColor(x, y).hsvSaturation()
        for x in range(image.width())
        for y in range(image.height())
        if image.pixelColor(x, y).alpha()
    )


def test_sp_disabled_multicoloured_star_is_grey(gamedb, qapp):
    widget = make_sp_widget()
    button = widget.gameInput.playerInputList["Ann"].bonusButtons["star_multi"]
    assert not button.isEnabled()
    assert _maxSaturation(button) < 30
    button.setEnabled(True)
    assert _maxSaturation(button) > 100
