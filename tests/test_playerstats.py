"""Player statistics: the engine queries and the screen that shows them."""

import datetime
import itertools

import pytest
from PySide6.QtWidgets import QApplication

from core.engine.db import db
from core.engine.playerstats import (
    RIVAL_MIN_MATCHES,
    HeadToHead,
    favourite_victim,
    game_breakdown,
    games_played_by,
    head_to_head,
    nemesis,
    player_form,
    player_summary,
)
from core.model.match import GenericMatch

_BASE = datetime.datetime(2024, 1, 1, 20, 0, 0, tzinfo=datetime.UTC)
_clock = itertools.count()


def _stamp(minutes: int) -> str:
    moment = _BASE + datetime.timedelta(minutes=minutes)
    return moment.strftime("%Y-%m-%d %H:%M:%S")


def _match(
    game, results, finished=None, state=GenericMatch.FINISHED, elapsed=600
) -> int:
    """Seed a match; ``results`` maps nick -> (score, winner)."""
    when = next(_clock) * 100 if finished is None else finished
    cur = db.execute(
        "INSERT INTO Match (Game_name, state, started, finished, elapsed) "
        "VALUES (?,?,?,?,?)",
        (game, state, _stamp(when - 10), _stamp(when), elapsed),
    )
    idMatch = cur.lastrowid
    assert idMatch is not None
    for nick, (score, winner) in results.items():
        db.execute(
            "INSERT OR IGNORE INTO Player (nick, fullName) VALUES (?,?)", (nick, nick)
        )
        db.execute(
            "INSERT INTO MatchPlayer (idMatch, nick, totalScore, winner) "
            "VALUES (?,?,?,?)",
            (idMatch, nick, score, int(winner)),
        )
    return idMatch


def _duel(game, winner, loser="Bob", **kwargs):
    return _match(game, {winner: (10, True), loser: (5, False)}, **kwargs)


# --- Which matches count -----------------------------------------------------


def test_only_finished_matches_count(gamedb):
    _duel("Ratuki", "Ann")
    _duel("Ratuki", "Ann", state=GenericMatch.SAVED)
    _duel("Ratuki", "Ann", state=GenericMatch.CANCELLED)
    _duel("Ratuki", "Ann", state=GenericMatch.RUNNING)

    assert player_summary("Ann").played == 1
    assert [g.played for g in game_breakdown("Ann")] == [1]
    assert len(player_form("Ann").recent) == 1
    assert head_to_head("Ann")[0].together == 1


def test_unknown_player_gives_empty_results(gamedb):
    _duel("Ratuki", "Ann")

    summary = player_summary("Nobody")
    assert summary.played == 0
    assert summary.wins == 0
    assert summary.win_rate is None
    assert summary.performance is None
    assert summary.favourite_game is None
    assert summary.first_played is None
    assert summary.last_played is None
    assert game_breakdown("Nobody") == []
    assert player_form("Nobody") == player_form("Nobody", length=0)
    assert player_form("Nobody").current_streak == 0
    assert head_to_head("Nobody") == []
    assert games_played_by("Nobody") == []


def test_nicks_with_quotes_are_bound_safely(gamedb):
    _match("Ratuki", {"O'Brien": (10, True), "Bob": (5, False)})

    assert player_summary("O'Brien").wins == 1
    assert head_to_head("Bob")[0].opponent == "O'Brien"
    assert games_played_by("O'Brien") == ["Ratuki"]


# --- Summary and performance -------------------------------------------------


def test_performance_adjusts_for_the_number_of_players(gamedb):
    _duel("Ratuki", "Ann")
    _match(
        "Ratuki",
        {"Ann": (1, False), "Bob": (9, True), "Cy": (2, False), "Dan": (3, False)},
    )

    summary = player_summary("Ann")
    # expected 1/2 + 1/4 = 0.75, earned 1
    assert summary.performance == pytest.approx(1 / 0.75)
    assert summary.win_rate == pytest.approx(0.5)


def test_shared_win_counts_as_a_win_and_a_fraction(gamedb):
    _match("Ratuki", {"Ann": (5, True), "Bob": (5, True), "Cy": (1, False)})

    ann = player_summary("Ann")
    assert (ann.wins, ann.shared_wins) == (1, 1)
    # expected 1/3, earned 1/2
    assert ann.performance == pytest.approx(1.5)
    assert player_summary("Cy").performance == 0


def test_matches_without_a_winner_are_not_in_the_performance(gamedb):
    _duel("Ratuki", "Ann")
    _match("Ratuki", {"Ann": (0, False), "Bob": (0, False)})

    summary = player_summary("Ann")
    assert summary.played == 2
    assert summary.win_rate == pytest.approx(0.5)
    assert summary.performance == pytest.approx(2.0)  # 1 / (1/2)

    _match("Toma6", {"Zoe": (0, False), "Bob": (0, False)})
    only_nowinner = player_summary("Zoe")
    assert only_nowinner.played == 1
    assert only_nowinner.performance is None


def test_summary_times_and_favourite_game(gamedb):
    _duel("Ratuki", "Ann", finished=10, elapsed=60)
    _duel("Toma6", "Ann", finished=20, elapsed=120)
    _duel("Toma6", "Ann", finished=30, elapsed=120)
    _duel("Ratuki", "Ann", finished=40, elapsed=60)

    summary = player_summary("Ann")
    assert summary.time_played == 360
    assert summary.first_played == _BASE + datetime.timedelta(minutes=0)
    assert summary.last_played == _BASE + datetime.timedelta(minutes=40)
    # Both played twice; Ratuki was played most recently.
    assert summary.favourite_game == "Ratuki"

    _duel("Toma6", "Ann", finished=50)
    assert player_summary("Ann").favourite_game == "Toma6"


# --- Per game ----------------------------------------------------------------


def test_game_breakdown_rows_and_order(gamedb):
    _match("Ratuki", {"Ann": (10, True), "Bob": (1, False)})
    _match("Ratuki", {"Ann": (21, False), "Bob": (30, True)})
    _match("Toma6", {"Ann": (7, True), "Bob": (9, False)})
    _match("Chinchon", {"Ann": (3, False), "Bob": (0, True)})

    rows = game_breakdown("Ann")
    assert [r.game for r in rows] == ["Ratuki", "Chinchon", "Toma6"]
    ratuki = rows[0]
    assert (ratuki.played, ratuki.wins) == (2, 1)
    assert ratuki.win_rate == pytest.approx(0.5)
    assert ratuki.performance == pytest.approx(1.0)
    assert (ratuki.min_score, ratuki.avg_score, ratuki.max_score) == (10, 16, 21)


# --- Form --------------------------------------------------------------------


def _sequence(nick, results):
    for won in results:
        _match("Ratuki", {nick: (1, won), "Bob": (0, not won)})


def test_form_is_ordered_by_finish_time_not_insertion(gamedb):
    _match("Ratuki", {"Ann": (1, True), "Bob": (0, False)}, finished=300)
    _match("Ratuki", {"Ann": (0, False), "Bob": (1, True)}, finished=100)
    _match("Ratuki", {"Ann": (0, False), "Bob": (1, True)}, finished=200)

    form = player_form("Ann")
    assert form.recent == (False, False, True)
    assert form.current_streak == 1


def test_streaks(gamedb):
    _sequence("Ann", [True, True, True, False, False, True, False, False, False, False])

    form = player_form("Ann")
    assert form.longest_win_streak == 3
    assert form.longest_loss_streak == 4
    assert form.current_streak == -4


def test_current_winning_streak_is_positive(gamedb):
    _sequence("Ann", [False, True, True])

    assert player_form("Ann").current_streak == 2


def test_recent_results_are_capped(gamedb):
    _sequence("Ann", [True] + [False] * 12)

    form = player_form("Ann", length=10)
    assert form.recent == (False,) * 10
    assert form.longest_win_streak == 1
    assert len(player_form("Ann", length=3).recent) == 3


# --- Head to head ------------------------------------------------------------


def _record(**kwargs):
    base = {"together": 0, "me_only": 0, "them_only": 0, "both": 0, "neither": 0}
    return HeadToHead(**{"opponent": "X", **base, **kwargs})


def test_head_to_head_buckets(gamedb):
    _match("Ratuki", {"Ann": (9, True), "Bob": (1, False)})  # me only
    _match("Ratuki", {"Ann": (1, False), "Bob": (9, True)})  # them only
    _match("Ratuki", {"Ann": (5, True), "Bob": (5, True)})  # shared
    _match("Ratuki", {"Ann": (1, False), "Bob": (2, False), "Cy": (9, True)})
    _match("Ratuki", {"Ann": (1, False), "Bob": (2, False)})  # nobody won
    _match("Ratuki", {"Ann": (9, True), "Cy": (1, False)})

    rows = {r.opponent: r for r in head_to_head("Ann")}
    assert rows["Bob"] == HeadToHead("Bob", 5, 1, 1, 1, 2)
    assert rows["Cy"] == HeadToHead("Cy", 2, 1, 1, 0, 0)
    assert [r.opponent for r in head_to_head("Ann")] == ["Bob", "Cy"]


def test_head_to_head_orders_ties_by_nick(gamedb):
    _match("Ratuki", {"Ann": (9, True), "Zed": (1, False), "Bob": (1, False)})

    assert [r.opponent for r in head_to_head("Ann")] == ["Bob", "Zed"]


def test_nemesis_and_favourite_victim_thresholds():
    rows = [
        _record(opponent="A", together=RIVAL_MIN_MATCHES - 1, them_only=2, me_only=0),
        _record(opponent="B", together=RIVAL_MIN_MATCHES, them_only=0, me_only=0),
    ]
    assert nemesis(rows) is None
    assert favourite_victim(rows) is None
    assert nemesis([]) is None


def test_nemesis_ties_break_on_balance_then_nick():
    rows = [
        _record(opponent="C", together=6, them_only=3, me_only=2),
        _record(opponent="B", together=6, them_only=3, me_only=1),
        _record(opponent="A", together=6, them_only=3, me_only=1),
        _record(opponent="D", together=6, them_only=2, me_only=0),
    ]
    best = nemesis(rows)
    assert best is not None
    assert best.opponent == "A"


def test_favourite_victim_mirrors_the_nemesis():
    rows = [
        _record(opponent="C", together=6, me_only=3, them_only=2),
        _record(opponent="B", together=6, me_only=3, them_only=1),
        _record(opponent="A", together=6, me_only=3, them_only=1),
        _record(opponent="D", together=6, me_only=2, them_only=0),
    ]
    victim = favourite_victim(rows)
    assert victim is not None
    assert victim.opponent == "A"


# --- Game filter -------------------------------------------------------------


def test_game_filter_restricts_every_section(gamedb):
    _match("Ratuki", {"Ann": (9, True), "Bob": (1, False)})
    _match("Toma6", {"Ann": (1, False), "Bob": (9, True), "Cy": (5, False)})
    _match("Toma6", {"Ann": (1, False), "Bob": (9, True), "Cy": (5, False)})

    only = ("Toma6",)
    assert player_summary("Ann", only).played == 2
    assert player_summary("Ann", only).wins == 0
    assert [g.game for g in game_breakdown("Ann", only)] == ["Toma6"]
    assert player_form("Ann", only).recent == (False, False)
    rows = {r.opponent: r for r in head_to_head("Ann", only)}
    assert rows["Bob"].together == 2
    assert rows["Cy"].together == 2
    assert player_summary("Ann", ("Ratuki", "Toma6")).played == 3
    assert player_summary("Ann", ("Chinchon",)).played == 0
    # The combo of games is not narrowed by the filter.
    assert games_played_by("Ann") == ["Ratuki", "Toma6"]


# --- A real match ------------------------------------------------------------


def test_a_match_played_through_the_engine_shows_up(gamedb):
    from tests.test_history import _finished_ratuki

    _finished_ratuki(("Ann", "Bob", "Cy"))

    ann = player_summary("Ann")
    assert (ann.played, ann.wins) == (1, 1)
    assert ann.performance == pytest.approx(3.0)
    assert [g.game for g in game_breakdown("Bob")] == ["Ratuki"]
    assert {r.opponent for r in head_to_head("Ann")} == {"Bob", "Cy"}
    assert games_played_by("Cy") == ["Ratuki"]


# --- The screen --------------------------------------------------------------


@pytest.fixture
def stats_screen(qapp, gamedb):
    from core.ui.playerstats import PlayerStatsWidget

    widget = PlayerStatsWidget()
    return widget


def _seed_screen_data():
    _match("Ratuki", {"Ann": (9, True), "Bob": (1, False)})
    _match("Ratuki", {"Ann": (1, False), "Bob": (9, True)})
    _match("Toma6", {"Ann": (9, True), "Bob": (1, False), "Cy": (3, False)})


def test_screen_says_so_when_there_is_nothing_to_show(stats_screen):
    stats_screen.show()

    assert stats_screen.playerCombo.count() == 0
    assert stats_screen.emptyLabel.isVisible()
    assert not stats_screen.content.isVisible()


def test_screen_fills_its_tables(stats_screen):
    _seed_screen_data()
    stats_screen.show()

    assert stats_screen.playerCombo.currentText() == "Ann"
    assert stats_screen.gameCombo.count() == 3  # all games + two
    assert stats_screen.gamesModel.rowCount() == 2
    assert stats_screen.rivalsModel.rowCount() == 2
    assert not stats_screen.emptyLabel.isVisible()
    assert stats_screen.formLayout.count() >= 3

    stats_screen.playerCombo.setCurrentText("Cy")
    assert stats_screen.gamesModel.rowCount() == 1
    assert stats_screen.rivalsModel.rowCount() == 2


def test_screen_game_filter_hides_the_game_table(stats_screen):
    _seed_screen_data()
    stats_screen.show()

    stats_screen.gameCombo.setCurrentIndex(stats_screen.gameCombo.findData("Toma6"))
    assert not stats_screen.gamesTable.isVisible()
    assert not stats_screen.favouriteValue.isVisible()
    assert stats_screen.rivalsModel.rowCount() == 2

    stats_screen.gameCombo.setCurrentIndex(0)
    assert stats_screen.gamesTable.isVisible()
    assert stats_screen.gamesModel.rowCount() == 2


def test_screen_keeps_the_selected_player_when_shown_again(stats_screen):
    _seed_screen_data()
    stats_screen.show()
    stats_screen.playerCombo.setCurrentText("Bob")

    stats_screen.hide()
    _match("Ratuki", {"Ann": (9, True), "Dan": (1, False)})
    stats_screen.show()

    assert stats_screen.playerCombo.currentText() == "Bob"
    assert stats_screen.playerCombo.count() == 4


def test_screen_retranslates(stats_screen):
    _seed_screen_data()
    stats_screen.show()
    stats_screen.retranslateUI()

    assert stats_screen.gamesModel.rowCount() == 2
    assert stats_screen.titleLabel.text()


# --- Opening from the main window -------------------------------------------


def test_main_window_swaps_between_new_game_and_player_stats(qapp, gamedb):
    from core.ui.mainwindow import MainWindow

    window = MainWindow()
    window.newGameTab.showPlayerStats()
    assert window.playerStatsTab.isVisible()
    assert not window.newGameTab.isVisible()

    window.playerStatsTab.backRequested.emit()
    assert window.newGameTab.isVisible()
    assert not window.playerStatsTab.isVisible()
    window.hide()


# --- The summary tiles -------------------------------------------------------


def _tile_grid(screen):
    grid = screen.summaryGrid
    return {
        key: grid.getItemPosition(grid.indexOf(tile))[:2]
        for key, tile in screen.summaryTiles.items()
        if grid.indexOf(tile) >= 0
    }


def test_summary_tiles_show_value_and_full_caption(stats_screen):
    _seed_screen_data()
    stats_screen.show()

    tiles = stats_screen.summaryTiles
    assert tiles["played"].value.fullText() == "3"
    assert tiles["played"].caption.fullText() == "Played"
    assert tiles["favourite"].value.fullText() == "Ratuki"
    positions = _tile_grid(stats_screen)
    assert positions["played"] == (0, 0)
    assert positions["performance"] == (0, 3)
    assert positions["time"] == (0, 4)
    assert positions["favourite"] == (1, 0)
    assert positions["last"] == (1, 2)
    assert positions["victim"] == (1, 4)
    assert all(t.isVisible() for t in tiles.values())


def test_summary_reflows_without_the_favourite_game(stats_screen):
    _seed_screen_data()
    stats_screen.show()

    stats_screen.gameCombo.setCurrentIndex(stats_screen.gameCombo.findData("Toma6"))
    positions = _tile_grid(stats_screen)
    assert "favourite" not in positions
    assert not stats_screen.summaryTiles["favourite"].isVisible()
    # Nine tiles in reading order, with no hole: 5 on the first row, 4 below.
    assert sorted(positions.values()) == [(0, c) for c in range(5)] + [
        (1, c) for c in range(4)
    ]
    assert positions["time"] == (0, 4)
    assert positions["first"] == (1, 0)
    assert positions["victim"] == (1, 3)

    stats_screen.gameCombo.setCurrentIndex(0)
    assert _tile_grid(stats_screen)["favourite"] == (1, 0)
    assert stats_screen.summaryTiles["favourite"].isVisible()


def test_summary_tiles_share_the_width_and_keep_the_performance_tooltip(stats_screen):
    _seed_screen_data()
    stats_screen.resize(900, 600)
    stats_screen.show()

    tiles = list(stats_screen.summaryTiles.values())
    assert len({tile.width() for tile in tiles}) <= 2  # rounding only
    perf = stats_screen.summaryTiles["performance"]
    assert "chance" in perf.toolTip()
    assert "chance" in perf.value.toolTip()
    assert "chance" in perf.caption.toolTip()


def test_a_long_favourite_game_is_elided_and_has_a_tooltip(stats_screen):
    name = "Azul Summer Pavilion"
    _match(name, {"Ann": (9, True), "Bob": (1, False)})
    stats_screen.show()
    QApplication.processEvents()  # lay the tiles out

    tile = stats_screen.summaryTiles["favourite"]
    assert tile.value.fullText() == name
    assert tile.value.text().endswith("…")
    assert len(tile.value.text()) < len(name)
    assert tile.value.toolTip() == name
    # It does not push the tiles out of line.
    assert tile.width() == stats_screen.summaryTiles["played"].width()


def test_nemesis_and_favourite_victim_tiles(stats_screen):
    _seed_screen_data()
    stats_screen.show()

    nemesis, victim = (stats_screen.summaryTiles[k] for k in ("nemesis", "victim"))
    assert nemesis.caption.fullText() == "Nemesis"
    assert victim.caption.fullText() == "Favourite victim"
    # Ann met Bob three times: she won two and lost one.
    assert nemesis.value.fullText() == "Bob"
    assert "Lost 1 of 3" in nemesis.toolTip()
    assert victim.value.fullText() == "Bob"
    assert "Won 2 of 3" in victim.toolTip()
    assert "Won 2 of 3" in victim.value.toolTip()


def test_rival_tiles_explain_when_nobody_qualifies(stats_screen):
    from core.engine.playerstats import RIVAL_MIN_MATCHES

    _match("Ratuki", {"Ann": (9, True), "Bob": (1, False)})
    stats_screen.show()

    for key in ("nemesis", "victim"):
        tile = stats_screen.summaryTiles[key]
        assert tile.value.fullText() == "—"
        assert str(RIVAL_MIN_MATCHES) in tile.toolTip()
        assert "at least" in tile.toolTip()


def test_rival_tiles_stay_when_a_single_game_is_selected(
    stats_screen,
):
    _seed_screen_data()
    stats_screen.show()
    stats_screen.gameCombo.setCurrentIndex(stats_screen.gameCombo.findData("Ratuki"))

    assert stats_screen.summaryTiles["nemesis"].isVisible()
    assert stats_screen.summaryTiles["victim"].isVisible()


# --- Table heights -----------------------------------------------------------


def _many_opponents(count, games=("Ratuki",)):
    for game in games:
        for i in range(count):
            _match(game, {"Ann": (9, True), f"Rival{i:02}": (1, False)})


def test_tables_are_no_taller_than_their_content(stats_screen):
    _seed_screen_data()
    stats_screen.resize(1000, 900)
    stats_screen.show()
    QApplication.processEvents()

    stack = stats_screen.tableStack
    for table in (stats_screen.gamesTable, stats_screen.rivalsTable):
        assert table.height() == stack.contentHeight(table)
    # Whatever is left stays below the tables.
    bottom = stats_screen.rivalsTable.geometry().bottom()
    assert bottom < stack.height() - 20


def test_a_long_table_leaves_the_other_its_minimum(stats_screen):
    _many_opponents(40)
    stats_screen.resize(1000, 700)
    stats_screen.show()
    QApplication.processEvents()

    stack = stats_screen.tableStack
    games, rivals = stats_screen.gamesTable, stats_screen.rivalsTable
    assert stats_screen.gamesModel.rowCount() == 1
    assert games.height() == stack.contentHeight(games)  # one row: all of it
    assert rivals.height() >= stack.minimumHeightOf(rivals)
    assert games.height() + rivals.height() + stack.SPACING <= stack.height()


def test_space_is_shared_by_row_count_when_neither_fits(stats_screen):
    stack = stats_screen.tableStack
    _many_opponents(30, games=("Ratuki", "Toma6", "Phase10", "Pocha", "Azul"))
    stats_screen.resize(1000, 600)
    stats_screen.show()
    QApplication.processEvents()

    games, rivals = stats_screen.gamesTable, stats_screen.rivalsTable
    assert games.height() >= stack.minimumHeightOf(games)
    assert rivals.height() >= stack.minimumHeightOf(rivals)
    assert games.height() + rivals.height() + stack.SPACING <= stack.height() + 1
    # The head-to-head table has far more rows, so it gets the larger share.
    assert rivals.height() > games.height()


def test_table_heights_follow_the_content(stats_screen):
    _seed_screen_data()
    stats_screen.resize(1000, 900)
    stats_screen.show()
    QApplication.processEvents()
    stack = stats_screen.tableStack

    stats_screen.gameCombo.setCurrentIndex(stats_screen.gameCombo.findData("Toma6"))
    QApplication.processEvents()
    assert not stats_screen.gamesTable.isVisible()
    rivals = stats_screen.rivalsTable
    assert rivals.geometry().top() == 0  # closes up where the other was
    assert rivals.height() == stack.contentHeight(rivals)
