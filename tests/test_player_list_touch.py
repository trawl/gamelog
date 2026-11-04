"""Long-press gestures on the player lists, which stand in for right-click and
drag-and-drop on touch screens (Android)."""

import pytest
from PySide6.QtCore import QPoint, Qt
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QHBoxLayout, QWidget

from core.engine.db import db
from core.ui.player.list import PlayerList


@pytest.fixture
def lists(qapp, gamedb, monkeypatch):
    """An 'available' and an 'in game' list, twinned, with three players."""
    monkeypatch.setattr(PlayerList, "_isTouch", staticmethod(lambda _event: True))
    for nick in ("ann", "bob", "cid"):
        db.addPlayer(nick, nick.title())
    window = QWidget()
    layout = QHBoxLayout(window)
    available = PlayerList(None, window)
    in_game = PlayerList(None, window)
    layout.addWidget(available)
    layout.addWidget(in_game)
    available.setTwinList(in_game)
    in_game.setTwinList(available)
    for nick in ("ann", "bob", "cid"):
        available.addItem(nick)
    window.resize(500, 300)
    window.show()
    for _ in range(2):
        qapp.processEvents()
    yield available, in_game
    window.close()


def _centre(view: PlayerList, row: int) -> QPoint:
    return view.visualRect(view.model().index(row, 0)).center()


def _long_press(view: PlayerList, row: int) -> QPoint:
    pos = _centre(view, row)
    QTest.mousePress(view.viewport(), Qt.MouseButton.LeftButton, pos=pos)
    view._onHold()  # as the timer would after LONG_PRESS_MS
    return pos


def test_long_press_without_moving_toggles_favourite(lists):
    available, _ = lists
    assert not db.isPlayerFavourite("ann")
    pos = _long_press(available, 0)
    QTest.mouseRelease(available.viewport(), Qt.MouseButton.LeftButton, pos=pos)
    assert db.isPlayerFavourite("ann")
    assert available.property("holding") is False


def test_a_short_tap_does_nothing(lists):
    available, _ = lists
    pos = _centre(available, 0)
    QTest.mouseClick(available.viewport(), Qt.MouseButton.LeftButton, pos=pos)
    assert not db.isPlayerFavourite("ann")


def test_moving_before_the_long_press_cancels_it(lists):
    available, _ = lists
    pos = _centre(available, 0)
    QTest.mousePress(available.viewport(), Qt.MouseButton.LeftButton, pos=pos)
    QTest.mouseMove(available.viewport(), pos + QPoint(0, 60))
    assert not available._hold_timer.isActive()


def test_long_press_then_drag_reorders_within_the_list(lists):
    available, _ = lists
    _long_press(available, 0)
    target = _centre(available, 2)
    QTest.mouseMove(available.viewport(), target)
    QTest.mouseRelease(available.viewport(), Qt.MouseButton.LeftButton, pos=target)
    assert available._model.retrievePlayers() == ["bob", "cid", "ann"]
    # Dragging is not a right-click.
    assert not db.isPlayerFavourite("ann")


def test_dragging_past_the_end_sends_the_player_to_the_end(lists):
    available, _ = lists
    _long_press(available, 0)
    below = QPoint(10, available.viewport().height() - 2)
    QTest.mouseMove(available.viewport(), below)
    QTest.mouseRelease(available.viewport(), Qt.MouseButton.LeftButton, pos=below)
    assert available._model.retrievePlayers() == ["bob", "cid", "ann"]


def test_long_press_then_release_over_the_other_list_moves_the_player(lists):
    available, in_game = lists
    _long_press(available, 1)
    other = in_game.viewport()
    pos = available.viewport().mapFromGlobal(
        other.mapToGlobal(QPoint(other.width() // 2, 20))
    )
    QTest.mouseMove(available.viewport(), pos)
    QTest.mouseRelease(available.viewport(), Qt.MouseButton.LeftButton, pos=pos)
    assert in_game._model.retrievePlayers() == ["bob"]
    assert available._model.retrievePlayers() == ["ann", "cid"]


def test_dragging_toward_the_other_list_does_not_reorder_this_one(lists):
    available, in_game = lists
    _long_press(available, 0)
    other = in_game.viewport()
    # Level with the bottom of this list but outside it, on the other list.
    pos = available.viewport().mapFromGlobal(
        other.mapToGlobal(QPoint(other.width() // 2, other.height() - 2))
    )
    QTest.mouseMove(available.viewport(), pos)
    assert available._model.retrievePlayers() == ["ann", "bob", "cid"]
    QTest.mouseRelease(available.viewport(), Qt.MouseButton.LeftButton, pos=pos)


def test_a_full_list_refuses_the_dragged_player(lists):
    available, in_game = lists
    in_game.setMaxPlayers(0)
    _long_press(available, 1)
    other = in_game.viewport()
    pos = available.viewport().mapFromGlobal(
        other.mapToGlobal(QPoint(other.width() // 2, 20))
    )
    QTest.mouseMove(available.viewport(), pos)
    QTest.mouseRelease(available.viewport(), Qt.MouseButton.LeftButton, pos=pos)
    assert available._model.retrievePlayers() == ["ann", "bob", "cid"]
    assert in_game._model.retrievePlayers() == []


def test_a_real_mouse_is_left_alone(qapp, gamedb, monkeypatch):
    """Only touch-synthesised presses start the long-press timer."""
    monkeypatch.undo()
    db.addPlayer("ann", "Ann")
    view = PlayerList()
    view.addItem("ann")
    view.resize(200, 100)
    view.show()
    for _ in range(2):
        qapp.processEvents()
    QTest.mousePress(view.viewport(), Qt.MouseButton.LeftButton, pos=_centre(view, 0))
    assert not view._hold_timer.isActive()
    QTest.mouseRelease(view.viewport(), Qt.MouseButton.LeftButton, pos=_centre(view, 0))
    view.close()
