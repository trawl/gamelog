"""Base tab widget emitting close/restart requests to its host."""

from __future__ import annotations

from PySide6.QtCore import QEvent, QObject, Signal
from PySide6.QtWidgets import QWidget

from core.ui.groupbox import mark_untitled_group_boxes


class Tab(QWidget):
    """Base widget for match tabs, signalling close/restart to the window."""

    closeRequested = Signal(QWidget)
    restartRequested = Signal(QWidget)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._groupBoxesMarked = False
        # An event filter rather than showEvent, which subclasses override.
        self.installEventFilter(self)

    def eventFilter(self, watched: QObject, event: QEvent) -> bool:
        """On the first show, when every title is set, flag untitled boxes."""
        if (
            watched is self
            and event.type() == QEvent.Type.Show
            and not self._groupBoxesMarked
        ):
            self._groupBoxesMarked = True
            mark_untitled_group_boxes(self)
        return super().eventFilter(watched, event)

    def requestClose(self) -> None:
        self.closeRequested.emit(self)

    def requestRestart(self) -> None:
        self.restartRequested.emit(self)
