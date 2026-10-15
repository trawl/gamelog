"""MainWindow.ensureClose(): the save/discard/cancel prompt shown when quitting
with matches still open."""

from unittest.mock import MagicMock

import pytest
from PySide6.QtWidgets import QMessageBox

from core.engine.db import db
from core.ui.mainwindow import MainWindow


def _fake_game(name="Ratuki", finished=False):
    game = MagicMock()
    game.isFinished.return_value = finished
    game.getGameName.return_value = name
    return game


@pytest.fixture
def mainwindow(qapp, gamedb):
    return MainWindow()


def _answer_with(monkeypatch, button):
    monkeypatch.setattr(QMessageBox, "question", lambda *a, **k: button)


# --- No open matches: a plain exit confirmation -----------------------------


def test_no_open_matches_confirms_and_closes(mainwindow, monkeypatch):
    _answer_with(monkeypatch, QMessageBox.StandardButton.Yes)
    assert mainwindow.ensureClose() is True


def test_no_open_matches_cancel_aborts_the_close(mainwindow, monkeypatch):
    _answer_with(monkeypatch, QMessageBox.StandardButton.No)
    assert mainwindow.ensureClose() is False


def test_already_finished_matches_do_not_trigger_the_save_prompt(
    mainwindow, monkeypatch
):
    mainwindow.openedGames.append(_fake_game(finished=True))
    _answer_with(monkeypatch, QMessageBox.StandardButton.Yes)
    assert (
        mainwindow.ensureClose() is True
    )  # falls through to the "no open matches" prompt


# --- One open match: save / discard / cancel --------------------------------


def test_single_match_cancel_leaves_it_untouched(mainwindow, monkeypatch):
    game = _fake_game()
    mainwindow.openedGames.append(game)
    _answer_with(monkeypatch, QMessageBox.StandardButton.Cancel)

    assert mainwindow.ensureClose() is False
    game.toggleScreenLock.assert_not_called()
    game.saveMatch.assert_not_called()
    game.closeMatch.assert_not_called()


def test_single_match_yes_saves_it(mainwindow, monkeypatch):
    game = _fake_game()
    mainwindow.openedGames.append(game)
    _answer_with(monkeypatch, QMessageBox.StandardButton.Yes)

    assert mainwindow.ensureClose() is True
    game.toggleScreenLock.assert_called_once_with(True)
    game.saveMatch.assert_called_once()
    game.closeMatch.assert_not_called()


def test_single_match_no_discards_it(mainwindow, monkeypatch):
    game = _fake_game()
    mainwindow.openedGames.append(game)
    _answer_with(monkeypatch, QMessageBox.StandardButton.No)

    assert mainwindow.ensureClose() is True
    game.closeMatch.assert_called_once()
    game.saveMatch.assert_not_called()


# --- Several open matches ----------------------------------------------------


def test_multiple_matches_yes_saves_every_one(mainwindow, monkeypatch):
    games = [_fake_game(), _fake_game()]
    mainwindow.openedGames.extend(games)
    _answer_with(monkeypatch, QMessageBox.StandardButton.Yes)

    assert mainwindow.ensureClose() is True
    for game in games:
        game.saveMatch.assert_called_once()
        game.closeMatch.assert_not_called()


def test_multiple_matches_cancel_leaves_all_untouched(mainwindow, monkeypatch):
    games = [_fake_game(), _fake_game()]
    mainwindow.openedGames.extend(games)
    _answer_with(monkeypatch, QMessageBox.StandardButton.Cancel)

    assert mainwindow.ensureClose() is False
    for game in games:
        game.saveMatch.assert_not_called()
        game.closeMatch.assert_not_called()


# --- Successfully closing disconnects the database --------------------------


def test_closing_disconnects_the_database(mainwindow, monkeypatch):
    _answer_with(monkeypatch, QMessageBox.StandardButton.Yes)
    mainwindow.ensureClose()
    assert not db.isConnected()
    with pytest.raises(RuntimeError):
        db.execute("SELECT 1")


def test_the_main_window_survives_garbage_collection(qapp, gamedb, monkeypatch):
    """main() creates the window without a name of its own; the application
    must hold it, or the cyclic collector eventually destroys it mid-use."""
    import gc

    import core.__main__ as entry

    monkeypatch.setattr(entry, "GamelogApplication", lambda argv: qapp)
    monkeypatch.setattr(entry, "install_desktop_entry", lambda: None)
    monkeypatch.setattr(type(qapp), "exec", lambda self: 0)
    with pytest.raises(SystemExit):
        entry.main()

    gc.collect()

    window = qapp.mainWindow
    assert window.isVisible()
    assert window.explorerTab.table.model() is not None
    window.hide()
