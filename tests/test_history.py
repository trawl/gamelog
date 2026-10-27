"""The match archive: filtering stored matches, loading them in any state and
the explorer screen that lists them."""

import datetime
from typing import cast

import pytest
from PySide6.QtCore import Qt

from core.engine.db import db
from core.engine.engine import RoundGameEngine
from core.engine.history import (
    STATUS_CANCELLED,
    STATUS_FINISHED,
    STATUS_INTERRUPTED,
    STATUS_SAVED,
    MatchFilter,
    find_matches,
    games_with_matches,
    players_with_matches,
)
from core.engine.resume import open_match
from core.model.match import GenericMatch
from core.registry import registry


def _engine(game, players):
    engine = registry.create_engine(game)
    for player in players:
        engine.addPlayer(player)
    engine.begin()
    return engine


def _play_round(engine, scores, winner):
    engine.openRound(engine.getNumRound())
    engine.setRoundWinner(winner)
    for player, score in scores.items():
        engine.addRoundInfo(player, score, {})
    engine.commitRound()


def _finished_ratuki(players=("Ann", "Bob", "Cy")):
    engine = _engine("Ratuki", list(players))
    engine.setDealingPolicy(engine.RRDealer)
    engine.setDealer(players[0])
    _play_round(engine, {players[0]: 60, players[1]: 5, players[2]: 0}, players[0])
    _play_round(engine, {players[0]: 50, players[1]: 5, players[2]: 0}, players[0])
    assert engine.getWinner() == players[0]
    return engine


def _saved(game="Ratuki", players=("Ann", "Bob")):
    engine = _engine(game, list(players))
    engine.save()
    return engine


def _cancelled(game="Ratuki", players=("Cy", "Dan")):
    engine = _engine(game, list(players))
    engine.cancelMatch()
    return engine


def _restamp(engine, started=None, elapsed=None):
    if started is not None:
        db.execute(
            "UPDATE Match SET started=? WHERE idMatch=?",
            (started, engine.match.idMatch),
        )
    if elapsed is not None:
        db.execute(
            "UPDATE Match SET elapsed=? WHERE idMatch=?",
            (elapsed, engine.match.idMatch),
        )


def _ids(flt=None):
    return {m.idMatch for m in find_matches(flt)}


# --- find_matches ------------------------------------------------------------


def test_summaries_describe_each_match(gamedb):
    engine = _finished_ratuki()

    (summary,) = find_matches()

    assert summary.idMatch == engine.match.idMatch
    assert summary.game == "Ratuki"
    assert summary.status == STATUS_FINISHED
    assert summary.rounds == 2
    assert [p.nick for p in summary.players] == ["Ann", "Bob", "Cy"]
    assert [p.nick for p in summary.winners] == ["Ann"]
    assert {p.nick: p.score for p in summary.players} == {
        "Ann": 110,
        "Bob": 10,
        "Cy": 0,
    }
    assert summary.started is not None


def test_no_filter_returns_everything_most_recent_first(gamedb):
    first = _finished_ratuki()
    second = _saved()
    _restamp(first, started="2026-01-01 10:00:00.000000+00:00")
    _restamp(second, started="2026-02-01 10:00:00.000000+00:00")

    assert [m.idMatch for m in find_matches()] == [
        second.match.idMatch,
        first.match.idMatch,
    ]


def test_filter_by_status(gamedb):
    finished = _finished_ratuki()
    saved = _saved()
    cancelled = _cancelled()
    # A match the app left running when it stopped.
    interrupted = _saved(players=("Ann", "Cy"))
    db.execute(
        "UPDATE Match SET state=? WHERE idMatch=?",
        (GenericMatch.RUNNING, interrupted.match.idMatch),
    )

    def only(*statuses):
        return _ids(MatchFilter(statuses=statuses))

    assert only(STATUS_FINISHED) == {finished.match.idMatch}
    assert only(STATUS_SAVED) == {saved.match.idMatch}
    assert only(STATUS_CANCELLED) == {cancelled.match.idMatch}
    assert only(STATUS_INTERRUPTED) == {interrupted.match.idMatch}
    assert only(STATUS_SAVED, STATUS_CANCELLED) == {
        saved.match.idMatch,
        cancelled.match.idMatch,
    }


def test_filter_by_game(gamedb):
    ratuki = _finished_ratuki()
    toma6 = _saved("Toma6")
    skull = _saved("Skull King")

    assert _ids(MatchFilter(games=("Toma6",))) == {toma6.match.idMatch}
    assert _ids(MatchFilter(games=("Ratuki", "Skull King"))) == {
        ratuki.match.idMatch,
        skull.match.idMatch,
    }


def test_filter_by_players_all_or_any(gamedb):
    ann_bob = _saved(players=("Ann", "Bob"))
    ann_cy = _saved(players=("Ann", "Cy"))
    dan_eve = _saved(players=("Dan", "Eve"))

    both = MatchFilter(players=("Ann", "Bob"), all_players=True)
    either = MatchFilter(players=("Ann", "Bob"), all_players=False)
    one = MatchFilter(players=("Ann",))

    assert _ids(both) == {ann_bob.match.idMatch}
    assert _ids(either) == {ann_bob.match.idMatch, ann_cy.match.idMatch}
    assert _ids(one) == {ann_bob.match.idMatch, ann_cy.match.idMatch}
    assert dan_eve.match.idMatch not in _ids(either)


def test_filter_by_winner(gamedb):
    ann_wins = _finished_ratuki(("Ann", "Bob", "Cy"))
    bob_wins = _finished_ratuki(("Bob", "Ann", "Cy"))
    _saved()  # nobody has won it

    assert _ids(MatchFilter(winner="Ann")) == {ann_wins.match.idMatch}
    assert _ids(MatchFilter(winner="Bob")) == {bob_wins.match.idMatch}


def test_filter_by_date_range_uses_inclusive_local_days(gamedb):
    early = _saved()
    middle = _saved()
    late = _saved()
    # Noon UTC lands on the same local calendar day in any timezone.
    _restamp(early, started="2026-03-01 12:00:00.000000+00:00")
    _restamp(middle, started="2026-03-10 12:00:00.000000+00:00")
    _restamp(late, started="2026-03-20 12:00:00.000000+00:00")

    d = datetime.date

    within = MatchFilter(date_from=d(2026, 3, 10), date_to=d(2026, 3, 10))
    assert _ids(within) == {middle.match.idMatch}

    since = MatchFilter(date_from=d(2026, 3, 10))
    assert _ids(since) == {middle.match.idMatch, late.match.idMatch}

    until = MatchFilter(date_to=d(2026, 3, 10))
    assert _ids(until) == {early.match.idMatch, middle.match.idMatch}


def test_legacy_timestamps_without_an_offset_are_still_listed(gamedb):
    legacy = _saved()
    _restamp(legacy, started="2026-03-10 12:00:00.000000")

    (summary,) = find_matches(
        MatchFilter(
            date_from=datetime.date(2026, 3, 10), date_to=datetime.date(2026, 3, 10)
        )
    )

    assert summary.idMatch == legacy.match.idMatch
    assert summary.started == datetime.datetime(2026, 3, 10, 12, tzinfo=datetime.UTC)


def test_filter_by_minimum_duration(gamedb):
    short = _saved()
    long = _saved()
    _restamp(short, elapsed=5 * 60)
    _restamp(long, elapsed=90 * 60)

    assert _ids(MatchFilter(min_minutes=30)) == {long.match.idMatch}
    assert _ids(MatchFilter(min_minutes=5)) == {
        short.match.idMatch,
        long.match.idMatch,
    }


def test_filters_combine(gamedb):
    _finished_ratuki()
    _saved("Toma6")
    target = _saved("Ratuki", ("Ann", "Zoe"))

    flt = MatchFilter(
        games=("Ratuki",), statuses=(STATUS_SAVED,), players=("Ann", "Zoe")
    )

    assert _ids(flt) == {target.match.idMatch}


def test_choices_for_the_filters(gamedb):
    _finished_ratuki()
    _saved("Toma6", ("Dan", "Eve"))

    assert games_with_matches() == ["Ratuki", "Toma6"]
    assert players_with_matches() == ["Ann", "Bob", "Cy", "Dan", "Eve"]


# --- Loading a stored match --------------------------------------------------


def test_opening_a_finished_match_restores_its_outcome(gamedb):
    finished = _finished_ratuki()
    id_match = finished.match.idMatch
    elapsed = finished.getGameSeconds()

    engine = open_match("Ratuki", id_match)

    assert engine is not None
    assert engine.match.loadedState == GenericMatch.FINISHED
    assert engine.getWinners() == ["Ann"]
    assert engine.match.state == GenericMatch.FINISHED
    assert engine.getListPlayers() == ["Ann", "Bob", "Cy"]
    assert engine.getScoreFromPlayer("Ann") == 110
    assert len(cast(RoundGameEngine, engine).getRounds()) == 2
    assert engine.getGameSeconds() == elapsed
    assert engine.getFinishTime() is not None


def test_opening_a_finished_match_leaves_the_stored_row_alone(gamedb):
    finished = _finished_ratuki()
    id_match = finished.match.idMatch
    before = db.queryDict("SELECT * FROM Match WHERE idMatch=?", (id_match,))

    open_match("Ratuki", id_match)

    assert db.queryDict("SELECT * FROM Match WHERE idMatch=?", (id_match,)) == before


def test_opening_a_saved_match_resumes_it(gamedb):
    saved = _saved()

    engine = open_match("Ratuki", saved.match.idMatch)

    assert engine is not None
    assert engine.match.loadedState is None
    assert engine.match.isRunning()


def test_opening_a_cancelled_match_keeps_its_clock_still(gamedb):
    cancelled = _cancelled()
    _restamp(cancelled, elapsed=125)

    engine = open_match("Ratuki", cancelled.match.idMatch)

    assert engine is not None
    assert engine.match.loadedState == GenericMatch.CANCELLED
    assert engine.match.isCancelled()
    assert engine.getWinner() is None
    assert engine.getGameSeconds() == 125


def test_opening_an_interrupted_match_is_frozen(gamedb):
    saved = _saved()
    db.execute(
        "UPDATE Match SET state=? WHERE idMatch=?",
        (GenericMatch.RUNNING, saved.match.idMatch),
    )

    engine = open_match("Ratuki", saved.match.idMatch)

    assert engine is not None
    assert engine.match.loadedState == GenericMatch.RUNNING
    assert engine.isPaused()


def test_opening_an_unknown_or_mismatched_match_gives_nothing(gamedb):
    saved = _saved()

    assert open_match("Ratuki", 999999) is None
    assert open_match("Toma6", saved.match.idMatch) is None


def test_a_finished_match_can_still_be_resumed_as_before_only_when_saved(gamedb):
    finished = _finished_ratuki()
    engine = registry.create_engine("Ratuki")

    assert engine.resume(finished.match.idMatch) is False


# --- The explorer screen -----------------------------------------------------


@pytest.fixture
def explorer(qapp, gamedb):
    from core.ui.explorer import MatchExplorerWidget

    widget = MatchExplorerWidget()
    widget.show()
    return widget


def _rows(explorer):
    return explorer.proxy.rowCount()


def test_explorer_lists_the_stored_matches(explorer):
    _finished_ratuki()
    _saved()
    _cancelled()

    explorer.hide()
    explorer.show()  # the list is rebuilt whenever the screen is shown

    assert _rows(explorer) == 2
    assert explorer.countLabel.text().startswith("2")


def test_explorer_shows_finished_and_saved_matches_by_default(explorer):
    _finished_ratuki()
    _saved()
    _cancelled()
    explorer.hide()
    explorer.show()

    assert _rows(explorer) == 2
    assert STATUS_INTERRUPTED not in explorer.statusButtons


def test_explorer_status_buttons_filter_the_list(explorer):
    _finished_ratuki()
    _saved()
    _cancelled()
    interrupted = _saved(players=("Ann", "Cy"))
    db.execute(
        "UPDATE Match SET state=? WHERE idMatch=?",
        (GenericMatch.RUNNING, interrupted.match.idMatch),
    )
    explorer.hide()
    explorer.show()

    # Cancelled also brings in the matches that were never completed.
    explorer.statusButtons[STATUS_CANCELLED].setChecked(True)
    assert _rows(explorer) == 4

    explorer.statusButtons[STATUS_FINISHED].setChecked(False)
    assert _rows(explorer) == 3

    explorer.resetFilters()
    assert _rows(explorer) == 2


def _check(button, text):
    """Tick ``text`` in a multi-choice filter button, as a click would."""
    (item,) = button.list.findItems(text, Qt.MatchFlag.MatchExactly)
    button.list.itemClicked.emit(item)


def test_explorer_game_and_player_choices_filter_the_list(explorer):
    _finished_ratuki()
    _saved("Toma6", ("Dan", "Eve"))
    explorer.hide()
    explorer.show()
    assert _rows(explorer) == 2

    _check(explorer.gamesButton, "Toma6")
    assert explorer.currentFilter().games == ("Toma6",)
    assert _rows(explorer) == 1

    _check(explorer.playersButton, "Ann")  # Ann never played Toma6 here
    assert _rows(explorer) == 0

    explorer.resetFilters()
    assert _rows(explorer) == 2
    assert explorer.currentFilter() == MatchFilter(
        statuses=(STATUS_FINISHED, STATUS_SAVED)
    )


def test_explorer_presets_set_the_date_range(explorer):
    from core.ui.explorer import PRESET_TODAY

    explorer.periodCombo.setCurrentIndex(PRESET_TODAY)

    flt = explorer.currentFilter()
    assert flt.date_from == flt.date_to == datetime.date.today()


def test_explorer_button_says_resume_for_saved_matches_only(explorer):
    _finished_ratuki()
    saved = _saved()
    explorer.hide()
    explorer.show()
    explorer.openButton.setToolTip("")

    explorer.selectMatch(saved.match.idMatch)
    assert explorer.openButton.toolTip() == "Resume"

    other = next(m for m in explorer.matches if m.idMatch != saved.match.idMatch)
    explorer.selectMatch(other.idMatch)
    assert explorer.openButton.toolTip() == "Open"


def test_explorer_opens_the_selected_match(explorer):
    finished = _finished_ratuki()
    explorer.hide()
    explorer.show()
    opened = []
    explorer.openRequested.connect(lambda i, g: opened.append((i, g)))

    explorer.selectMatch(finished.match.idMatch)
    explorer.openSelected()

    assert opened == [(finished.match.idMatch, "Ratuki")]


def test_explorer_open_is_disabled_without_a_selection(explorer):
    _saved()
    explorer.hide()
    explorer.show()
    explorer.table.clearSelection()

    assert not explorer.openButton.isEnabled()


# --- Opening from the main window -------------------------------------------


@pytest.fixture
def mainwindow(qapp, gamedb):
    from core.ui.mainwindow import MainWindow

    return MainWindow()


def test_main_window_swaps_between_new_game_and_explorer(mainwindow):
    mainwindow.newGameTab.showHistory()
    assert mainwindow.explorerTab.isVisible()
    assert not mainwindow.newGameTab.isVisible()

    mainwindow.explorerTab.backRequested.emit()
    assert mainwindow.newGameTab.isVisible()
    assert not mainwindow.explorerTab.isVisible()


def test_finished_match_opens_locked_and_returns_to_the_explorer(mainwindow):
    finished = _finished_ratuki()
    mainwindow.showExplorer()

    mainwindow.openStoredMatch(finished.match.idMatch, "Ratuki")

    (board,) = mainwindow.openedGames
    assert board.isFinished()
    assert board.engine.getWinners() == ["Ann"]
    assert "Ann" in board.gameStatusLabel.text()
    assert not board.commitRoundButton.isEnabled()
    assert not board.undoButton.isEnabled()  # the result cannot be rewritten
    assert not board.canUndo()
    assert not mainwindow.explorerTab.isVisible()

    board.cancelMatch()  # leave: nothing to save, so no prompt

    assert mainwindow.openedGames == []
    assert mainwindow.explorerTab.isVisible()
    row = db.execute(
        "SELECT state FROM Match WHERE idMatch=?", (finished.match.idMatch,)
    ).fetchone()
    assert row["state"] == GenericMatch.FINISHED


def test_cancelled_match_opens_for_review_only(mainwindow):
    cancelled = _cancelled()
    before = db.queryDict(
        "SELECT * FROM Match WHERE idMatch=?", (cancelled.match.idMatch,)
    )
    mainwindow.showExplorer()

    mainwindow.openStoredMatch(cancelled.match.idMatch, "Ratuki")

    (board,) = mainwindow.openedGames
    assert board.reviewOnly
    assert not board.commitRoundButton.isEnabled()
    assert not board.undoButton.isEnabled()
    assert board.gameStatusLabel.text()

    board.cancelMatch()

    assert (
        db.queryDict("SELECT * FROM Match WHERE idMatch=?", (cancelled.match.idMatch,))
        == before
    )


def test_saved_match_resumes_from_the_explorer(mainwindow):
    saved = _saved()
    mainwindow.showExplorer()

    mainwindow.openStoredMatch(saved.match.idMatch, "Ratuki")

    (board,) = mainwindow.openedGames
    assert not board.isFinished()
    assert not board.reviewOnly
    assert board.engine.match.idMatch == saved.match.idMatch


def test_opening_the_same_match_twice_opens_one_board(mainwindow):
    finished = _finished_ratuki()
    mainwindow.showExplorer()

    mainwindow.openStoredMatch(finished.match.idMatch, "Ratuki")
    mainwindow.openStoredMatch(finished.match.idMatch, "Ratuki")

    assert len(mainwindow.openedGames) == 1
