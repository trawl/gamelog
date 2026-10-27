"""Rolling back the entry that ended a match: the match reopens, its result
is taken out of the statistics and its clock resumes from where it stopped."""

import pytest
from PySide6.QtCore import QEvent, Qt
from PySide6.QtGui import QKeyEvent, QKeySequence
from PySide6.QtWidgets import QApplication, QLineEdit, QMessageBox

from core.engine.db import db
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


def _stored_state(engine):
    row = db.execute(
        "SELECT state FROM Match WHERE idMatch=?;", (engine.match.idMatch,)
    ).fetchone()
    return row["state"]


def _stored_winners(engine):
    cur = db.execute(
        "SELECT nick FROM MatchPlayer WHERE idMatch=? AND winner=1;",
        (engine.match.idMatch,),
    )
    return [row["nick"] for row in cur]


def _finished_ratuki():
    """A Ratuki match that Ann has just won in its second round."""
    engine = _engine("Ratuki", ["Ann", "Bob", "Cy"])
    engine.setDealingPolicy(engine.RRDealer)
    engine.setDealer("Ann")
    _play_round(engine, {"Ann": 60, "Bob": 5, "Cy": 0}, "Ann")
    _play_round(engine, {"Ann": 50, "Bob": 5, "Cy": 0}, "Ann")
    assert engine.getWinner() == "Ann"
    return engine


# --- Engine ----------------------------------------------------------------


def test_rollback_of_the_final_round_reopens_the_match(gamedb):
    engine = _finished_ratuki()
    assert _stored_state(engine) == GenericMatch.FINISHED
    assert _stored_winners(engine) == ["Ann"]

    engine.rollback()

    assert engine.getWinner() is None
    assert engine.match.isRunning()
    assert engine.getNumRound() == 2
    assert engine.getScoreFromPlayer("Ann") == 60
    # The stored result no longer counts towards the statistics.
    assert _stored_state(engine) == GenericMatch.RUNNING
    assert _stored_winners(engine) == []


def test_rollback_keeps_the_elapsed_time_frozen_at_the_end(gamedb):
    engine = _finished_ratuki()
    elapsed_at_end = engine.getGameSeconds()

    engine.rollback()

    assert engine.getGameSeconds() == elapsed_at_end


def test_rollback_of_the_final_round_keeps_the_dealer(gamedb):
    engine = _finished_ratuki()
    dealer = engine.getDealer()  # rotation froze when the match was decided

    engine.rollback()

    assert engine.getDealer() == dealer


def test_reopened_match_can_be_finished_again(gamedb):
    engine = _finished_ratuki()
    engine.rollback()

    _play_round(engine, {"Ann": 0, "Bob": 50, "Cy": 0}, "Bob")
    assert engine.getWinner() is None
    _play_round(engine, {"Ann": 45, "Bob": 0, "Cy": 0}, "Ann")

    assert engine.getWinner() == "Ann"
    assert _stored_state(engine) == GenericMatch.FINISHED
    assert _stored_winners(engine) == ["Ann"]
    count = db.execute("SELECT COUNT(*) AS n FROM Match;").fetchone()["n"]
    assert count == 1


def test_rollback_of_an_explicit_finish_only_reopens(gamedb):
    engine = _engine("Scrabble", ["Ann", "Bob"])
    engine.addEntry("Ann", 20, {})
    engine.addEntry("Bob", 10, {})
    engine.finishGame()
    assert engine.getWinner() == "Ann"

    engine.rollback()

    assert engine.getWinner() is None
    assert len(engine.getRounds()) == 2  # the entries themselves stay


def test_reopen_is_a_noop_on_an_undecided_match(gamedb):
    engine = _engine("Ratuki", ["Ann", "Bob"])
    _play_round(engine, {"Ann": 10, "Bob": 5}, "Ann")
    resumed = engine.match.resumed

    engine.reopen()

    assert engine.match.resumed == resumed
    assert engine.match.isRunning()


# --- Widget ----------------------------------------------------------------


@pytest.fixture
def answer_yes(monkeypatch):
    monkeypatch.setattr(
        QMessageBox, "question", lambda *a, **k: QMessageBox.StandardButton.Yes
    )


def test_undo_button_reopens_a_finished_board(qapp, gamedb, answer_yes):
    widget = registry.create_widget("Ratuki", ["Ann", "Bob"], None, None)
    engine = widget.engine
    _play_round(engine, {"Ann": 60, "Bob": 5}, "Ann")
    _play_round(engine, {"Ann": 50, "Bob": 5}, "Ann")
    widget.updatePanel()
    assert widget.isFinished()
    assert widget.undoButton.isEnabled()
    assert widget.gameInput.isHidden()

    widget.undoCommit()

    assert not widget.isFinished()
    assert engine.getNumRound() == 2
    assert not widget.gameInput.isHidden()
    assert widget.gameInput.isEnabled()
    assert widget.pauseMatchButton.isEnabled()
    assert widget.playerOrderButton.isEnabled()
    assert widget.clock.timer.isActive()
    assert widget.gameStatusLabel.text() == ""
    assert widget.playerGroupBox["Ann"].background is not (
        widget.playerGroupBox["Ann"].winnerPixmap
    )


def test_undo_button_reopens_an_explicitly_finished_board(qapp, gamedb, answer_yes):
    widget = registry.create_widget("Scrabble", ["Ann", "Bob"], None, None)
    engine = widget.engine
    engine.addEntry("Ann", 20, {})
    widget.updatePanel()
    widget.finish()
    assert widget.isFinished()
    assert not widget.finishButton.isEnabled()

    widget.undoCommit()

    assert not widget.isFinished()
    assert widget.finishButton.isEnabled()
    assert len(engine.getRounds()) == 1


def test_undo_button_reopens_a_finished_phase10_board(qapp, gamedb, answer_yes):
    widget = registry.create_widget("Phase10", ["Ann", "Bob"], None, None)
    engine = widget.engine
    for phase in range(1, 11):  # Ann clears every phase in a row
        engine.openRound(engine.getNumRound())
        engine.setRoundWinner("Ann")
        engine.addRoundInfo("Ann", 0, {"aimedPhase": phase, "isCompleted": True})
        engine.addRoundInfo("Bob", 50, {"aimedPhase": 1, "isCompleted": False})
        engine.commitRound()
    widget.updatePanel()
    assert widget.isFinished()

    widget.undoCommit()

    assert not widget.isFinished()
    assert engine.getNumRound() == 10
    for pi in widget.gameInput.playerInputList.values():
        assert pi.roundScore.isEnabled()


# --- Undo docked in the input widget ----------------------------------------


@pytest.mark.parametrize("game", ["Scrabble", "Qwirkle", "Carcassonne"])
def test_docked_undo_takes_the_finish_slot_while_finished(
    qapp, gamedb, answer_yes, game
):
    widget = registry.create_widget(game, ["Ann", "Bob"], None, None)
    widget.show()
    engine = widget.engine
    kind = engine.getEntryKinds()[0] if game == "Carcassonne" else None
    engine.addEntry("Ann", 20, {"kind": kind} if kind else {})
    widget.updatePanel()
    assert widget.gameInput.isAncestorOf(widget.undoButton)

    widget.finish()

    assert widget.gameInput.isHidden()
    assert widget.undoButton.isVisible()
    assert widget.undoButton.isEnabled()
    assert widget.finishButton.isHidden()
    assert widget.buttonGroupLayout.indexOf(widget.undoButton) >= 0

    widget.undoCommit()

    assert not widget.isFinished()
    assert widget.gameInput.isAncestorOf(widget.undoButton)
    assert widget.undoButton.isVisible()
    assert widget.finishButton.isVisible()
    widget.close()


# --- Keyboard shortcut ----------------------------------------------------------


def _undo_override_accepted(field):
    """Whether ``field`` claims the undo key sequence for its own text undo."""
    # Qt's ControlModifier is the Cmd key on macOS, so this is the platform undo.
    event = QKeyEvent(
        QEvent.Type.ShortcutOverride, Qt.Key.Key_Z, Qt.KeyboardModifier.ControlModifier
    )
    event.ignore()
    QApplication.sendEvent(field, event)
    return event.isAccepted()


def test_score_fields_leave_the_undo_shortcut_to_the_board(qapp, gamedb):
    widget = registry.create_widget("Scrabble", ["Ann", "Bob"], None, None)
    field = widget.gameInput.scoreSpinBox.lineEdit()

    assert not _undo_override_accepted(field)
    # A field outside any board keeps its own text undo.
    assert _undo_override_accepted(QLineEdit())


def test_undo_shortcut_matches_the_platform_undo_keys(qapp, gamedb):
    widget = registry.create_widget("Ratuki", ["Ann", "Bob"], None, None)
    assert widget.undosc.key() == QKeySequence(QKeySequence.StandardKey.Undo)


def test_undo_shortcut_reopens_a_finished_match(qapp, gamedb, answer_yes):
    widget = registry.create_widget("Ratuki", ["Ann", "Bob"], None, None)
    _play_round(widget.engine, {"Ann": 110, "Bob": 5}, "Ann")
    widget.updatePanel()
    assert widget.isFinished()

    widget.undosc.activated.emit()

    assert not widget.isFinished()
    assert widget.engine.getRounds() == []


def test_undo_shortcut_does_nothing_without_anything_to_undo(qapp, gamedb, monkeypatch):
    widget = registry.create_widget("Ratuki", ["Ann", "Bob"], None, None)
    asked = []
    monkeypatch.setattr(QMessageBox, "question", lambda *a, **k: asked.append(a))

    widget.undosc.activated.emit()

    assert asked == []


def test_carcassonne_undo_is_enabled_before_the_next_entry_is_chosen(qapp, gamedb):
    widget = registry.create_widget("Carcassonne", ["Ann", "Bob"], None, None)
    widget.show()
    engine = widget.engine
    assert not widget.undoButton.isEnabled()

    engine.addEntry("Ann", 4, {"kind": engine.getEntryKinds()[0]})
    widget.updatePanel()  # resets the input: no player or kind selected

    assert widget.gameInput.getPlayer() == ""
    assert widget.undoButton.isEnabled()
    assert not widget.commitRoundButton.isEnabled()
    assert not widget.gameInput.scoreSpinBox.isEnabled()
    widget.close()
