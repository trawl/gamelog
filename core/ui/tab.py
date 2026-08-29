"""Base tab widget emitting close/restart requests to its host."""

from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QWidget


class Tab(QWidget):
    """Base widget for match tabs, signalling close/restart to the window."""

    closeRequested = Signal(QWidget)
    restartRequested = Signal(QWidget)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

    def requestClose(self) -> None:
        self.closeRequested.emit(self)

    def requestRestart(self) -> None:
        self.restartRequested.emit(self)
