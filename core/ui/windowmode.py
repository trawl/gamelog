"""Window mode (maximised or full screen) of the main window, on Android."""

from __future__ import annotations

from PySide6.QtWidgets import QWidget

from core.engine.settings import appsettings
from core.platform_info import is_android


def apply_window_mode(window: QWidget) -> None:
    """Show ``window`` full screen or maximised, per the ``fullscreen`` setting.

    Android only: desktop windows keep whatever size the user gave them.
    Full screen hides the system bars, but they come back whenever the
    on-screen keyboard opens, which is why maximised is the default.
    """
    if not is_android():
        return
    if appsettings["fullscreen"]:
        window.showFullScreen()
    else:
        window.showMaximized()
