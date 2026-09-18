"""Match lifecycle: pause/unpause elapsed-time accounting, cancellation rules,
and the legacy timestamp fallback in ``resumeMatch``."""

import datetime

from core.engine.db import db
from core.model.match import GenericMatch


def _running_match(seconds_played=0):
    """A started match that has (apparently) been running for ``seconds_played``."""
    match = GenericMatch(["Ann", "Bob"])
    match.startMatch()
    match.resumed -= datetime.timedelta(seconds=seconds_played)
    return match


# --- Pause / unpause -----------------------------------------------------


def test_pause_and_unpause_toggle_running_state():
    match = _running_match()
    assert match.isRunning()

    match.pause()
    assert match.isPaused()
    assert not match.isRunning()

    match.unpause()
    assert match.isRunning()
    assert not match.isPaused()


def test_pause_folds_elapsed_time_into_the_running_total():
    match = _running_match(seconds_played=5)
    match.pause()
    assert match.elapsed >= 5
    # Time is frozen while paused: it must not keep accruing.
    assert match.getGameSeconds() == match.elapsed


def test_pause_is_a_noop_when_already_paused():
    match = _running_match(seconds_played=5)
    match.pause()
    elapsed_after_first_pause = match.elapsed

    match.resumed -= datetime.timedelta(
        seconds=100
    )  # would inflate elapsed if re-applied
    match.pause()
    assert match.elapsed == elapsed_after_first_pause


def test_unpause_is_a_noop_when_not_paused():
    match = _running_match(seconds_played=5)
    resumed_before = match.resumed
    match.unpause()  # never paused
    assert match.resumed == resumed_before
    assert match.isRunning()


def test_unpause_resets_the_clock_so_time_paused_is_not_counted():
    match = _running_match(seconds_played=5)
    match.pause()
    elapsed_while_paused = match.elapsed

    match.unpause()
    assert match.getGameSeconds() == elapsed_while_paused


# --- Cancellation ----------------------------------------------------------


def test_cancel_marks_an_unfinished_match_as_cancelled(gamedb):
    match = _running_match()
    match.cancel()
    assert match.isCancelled()


def test_cancel_is_a_noop_once_a_winner_is_set(gamedb):
    match = _running_match()
    match.winner = "Ann"
    match.cancel()
    assert not match.isCancelled()  # a decided match can't be retroactively cancelled


def test_cancel_is_idempotent(gamedb):
    match = _running_match()
    match.cancel()
    match.elapsed = 999  # would be re-flushed if cancel() ran its logic again
    match.cancel()
    assert match.elapsed == 999


# --- resumeMatch: legacy (timezone-less) timestamp fallback ---------------


def _save_match_row(started: str) -> int:
    cur = db.execute(
        "INSERT INTO Match (Game_name, state, started, finished, elapsed) "
        "VALUES (?,?,?,?,?);",
        ("Generic", GenericMatch.SAVED, started, started, 0),
    )
    assert cur.lastrowid is not None
    return cur.lastrowid


def test_resume_parses_timezone_aware_timestamps(gamedb):
    id_match = _save_match_row("2024-01-01 12:00:00.000000+00:00")
    match = GenericMatch()
    assert match.resumeMatch(id_match) is True
    assert match.start == datetime.datetime(2024, 1, 1, 12, 0, tzinfo=datetime.UTC)


def test_resume_falls_back_to_naive_timestamps(gamedb):
    """Older rows persisted before timezone-aware timestamps were adopted."""
    id_match = _save_match_row("2024-01-01 12:00:00.000000")
    match = GenericMatch()
    assert match.resumeMatch(id_match) is True
    assert match.start == datetime.datetime(2024, 1, 1, 12, 0, tzinfo=datetime.UTC)
