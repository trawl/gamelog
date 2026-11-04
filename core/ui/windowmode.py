"""Window mode of the main window: full screen, or the platform's other mode."""

from __future__ import annotations

from PySide6.QtWidgets import QWidget

from core.engine.settings import appsettings
from core.platform_info import is_android


def apply_window_mode(window: QWidget) -> None:
    """Show ``window`` full screen or not, per the ``fullscreen`` setting.

    Not full screen means maximised on Android, where the system sizes the
    window, and a normal window on desktop, which keeps the size the user gave
    it. On Android full screen hides the system bars, but they come back
    whenever the on-screen keyboard opens, so maximised may suit better there.
    """
    if appsettings["fullscreen"]:
        window.showFullScreen()
    elif is_android():
        window.showMaximized()
    else:
        window.showNormal()


def toggle_fullscreen(window: QWidget) -> None:
    """Flip the ``fullscreen`` setting (keeping it for next time) and apply it."""
    appsettings.set("fullscreen", not appsettings["fullscreen"])
    apply_window_mode(window)
