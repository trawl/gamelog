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


# --- F11 toggles full screen ---------------------------------------------------


def test_f11_toggles_full_screen_and_remembers_it(mainwindow, settings):
    from PySide6.QtGui import QKeySequence, QShortcut

    from core.engine.settings import appsettings

    # The offscreen platform has no active window to deliver key presses to, so
    # fire the F11 shortcut itself.
    [f11] = [
        shortcut
        for shortcut in mainwindow.findChildren(QShortcut)
        if shortcut.key() == QKeySequence("F11")
    ]
    assert not appsettings["fullscreen"]
    mainwindow.show()
    f11.activated.emit()
    assert mainwindow.isFullScreen()
    assert appsettings["fullscreen"] is True

    f11.activated.emit()
    assert not mainwindow.isFullScreen()
    assert appsettings["fullscreen"] is False


# --- No menu bar off macOS ----------------------------------------------------


def test_no_menu_bar_outside_macos(qapp, gamedb, monkeypatch):
    import sys

    from PySide6.QtWidgets import QMenuBar

    monkeypatch.setattr(sys, "platform", "linux")
    window = MainWindow()
    assert window.findChild(QMenuBar) is None


def test_menu_bar_remains_on_macos(qapp, gamedb, monkeypatch):
    import sys

    from PySide6.QtWidgets import QMenuBar

    monkeypatch.setattr(sys, "platform", "darwin")
    window = MainWindow()
    assert window.findChild(QMenuBar) is not None


def test_quit_shortcut_works_without_a_menu_bar(qapp, gamedb, monkeypatch):
    import sys

    from PySide6.QtGui import QKeySequence

    monkeypatch.setattr(sys, "platform", "linux")
    window = MainWindow()
    assert window.exitAction in window.actions()
    assert window.exitAction.shortcut() == QKeySequence("Ctrl+Q")
