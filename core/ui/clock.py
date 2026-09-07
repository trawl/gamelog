"""LCD-style elapsed-time clock widget with pause blinking."""

from __future__ import annotations

import datetime

from PySide6 import QtCore
from PySide6.QtCore import QEasingCurve, QPropertyAnimation, QTimer
from PySide6.QtGui import QMouseEvent
from PySide6.QtWidgets import (
    QFrame,
    QGraphicsOpacityEffect,
    QLCDNumber,
    QWidget,
)


class GameClock(QLCDNumber):
    """LCD clock showing elapsed match time, blinking colons and pause state."""

    doubleClicked = QtCore.Signal()

    def __init__(self, elapsed: int = 0, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setSegmentStyle(QLCDNumber.SegmentStyle.Filled)
        self.startTime = datetime.datetime.now(tz=datetime.UTC)
        self.accumulated = elapsed
        self.paused = False
        self._paintenabled = True
        self.refreshinterval = 500
        self.showcolons = True
        self.timer = QTimer(self)
        self.timer.start(self.refreshinterval)
        self.setDigitCount(5)
        self.showTime()
        self.timer.timeout.connect(self.showTime)
        self.setFrameStyle(QFrame.Shape.NoFrame)

        self.opacityEffect = QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(self.opacityEffect)
        self.opacityEffect.setOpacity(1.0)

        self.blinkAnim = QPropertyAnimation(self.opacityEffect, b"opacity", self)
        self.blinkAnim.setDuration(1000)  # 1 second cycle
        self.blinkAnim.setLoopCount(-1)
        self.blinkAnim.setKeyValueAt(0.0, 1.0)  # fully visible
        self.blinkAnim.setKeyValueAt(0.5, 0.2)  # fade out midpoint
        self.blinkAnim.setKeyValueAt(1.0, 1.0)
        self.blinkAnim.setEasingCurve(QEasingCurve.Type.InOutSine)

    def showTime(self, elapsed: int | None = None) -> None:
        """Refresh the display, computing elapsed time when not given."""
        if not elapsed:
            now = datetime.datetime.now(tz=datetime.UTC)
            timediff = now - self.startTime
            elapsed = timediff.seconds + self.accumulated
        else:
            self.showcolons = True
        hours, remainder = divmod(elapsed, 3600)
        minutes, seconds = divmod(remainder, 60)
        if self.showcolons:
            text = f"{hours:02}:{minutes:02}:{seconds:02}"
        else:
            text = f"{hours:02} {minutes:02} {seconds:02}"
        if hours:
            self.setDigitCount(8)
        self.display(text)

        self.showcolons = not self.showcolons

    def pauseTimer(self) -> None:
        """Freeze the clock, bank the elapsed time and start blinking."""
        self.timer.stop()
        self.showcolons = True
        self.showTime()
        now = datetime.datetime.now(tz=datetime.UTC)
        timediff = now - self.startTime
        self.accumulated += timediff.seconds
        self.blinkAnim.start()

    def unpauseTimer(self) -> None:
        """Resume ticking from now and stop the pause blink animation."""
        self.blinkAnim.stop()
        self.opacityEffect.setOpacity(1.0)
        self._paintenabled = True
        self.startTime = datetime.datetime.now(tz=datetime.UTC)
        self.timer.start(self.refreshinterval)
        self.showcolons = True
        self.showTime()

    def stopTimer(self) -> None:
        """Stop the clock and reset the accumulated time to zero."""
        self.timer.stop()
        self.showcolons = True
        self.showTime()
        self.starTime = None
        self.accumulated = 0

    def mouseDoubleClickEvent(self, event: QMouseEvent) -> None:
        self.doubleClicked.emit()
        super().mouseDoubleClickEvent(event)
