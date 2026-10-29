"""Player statistics: the engine queries and the screen that shows them."""

import datetime
import itertools

import pytest

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
