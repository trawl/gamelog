"""Theme stylesheets, as far as they can be checked off the target platform."""

from contextlib import contextmanager

from PySide6.QtWidgets import QGroupBox, QLabel, QVBoxLayout

from core.ui.tab import Tab
from core.ui.theme import WINDOWS_GROUPBOX_CSS


@contextmanager
def windows_groupbox_rule(qapp):
    """Add the Windows-only rule to the application stylesheet, as ThemeManager
    does on Windows; set on a widget instead it would not move the contents."""
    original = qapp.styleSheet()
    qapp.setStyleSheet(original + WINDOWS_GROUPBOX_CSS)
    try:
        yield
    finally:
        qapp.setStyleSheet(original)


def _content_top(qapp, title: str) -> int:
    """Where a group box's content starts, inside a screen that is then shown."""
    with windows_groupbox_rule(qapp):
        tab = Tab()
        box = QGroupBox()
        label = QLabel("content")
        QVBoxLayout(box).addWidget(label)
        QVBoxLayout(tab).addWidget(box)
        box.setTitle(title)  # set after construction, as the screens do
        tab.resize(240, 160)
        tab.show()
        for _ in range(3):
            qapp.processEvents()
        top = label.y()
        tab.close()
        return top


def test_titled_group_box_reserves_room_for_its_title(qapp):
    assert _content_top(qapp, "Players") >= 40


def test_untitled_group_box_does_not_reserve_title_room(qapp):
    """The new-game screen's two big boxes have no title; they must not leave a
    gap of 36px at the top of the window."""
    assert _content_top(qapp, "") < 25


def test_new_game_screen_starts_at_the_top_edge(qapp, gamedb):
    from core.ui.mainwindow import MainWindow

    with windows_groupbox_rule(qapp):
        window = MainWindow()
        window.resize(1024, 600)
        for _ in range(3):
            qapp.processEvents()
        screen = window.newGameTab
        game_box = screen.gameGroupBox
        # The box's first content sits near its top, not a title's height down.
        layout = game_box.layout()
        assert layout is not None
        item = layout.itemAt(0)
        assert item is not None
        assert item.geometry().top() < 25
        window.hide()
