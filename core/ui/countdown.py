"""Circular countdown timer widget with animated arc and configurable colour."""

from __future__ import annotations

import datetime
from typing import TYPE_CHECKING

from PySide6.QtCore import (
    Property,
    QEasingCurve,
    QPropertyAnimation,
    Qt,
    QTimer,
    Signal,
)
from PySide6.QtGui import QColor, QFont, QPainter, QPaintEvent, QPen
from PySide6.QtWidgets import QGraphicsOpacityEffect, QWidget

if TYPE_CHECKING:
    from core.ui.clock import GameClock


class CountdownTimer(QWidget):
    """Round countdown timer: arc border depletes clockwise, seconds shown inside.

    Parameters
    ----------
    seconds:
        Total countdown duration in seconds.
    color:
        Arc and text colour (defaults to a neutral blue).
    parent:
        Optional Qt parent widget.
    """

    finished = Signal()

    def __init__(
        self,
        seconds: int = 30,
        color: QColor | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)

        self._total = seconds
        self._remaining = seconds
        self._color = color or QColor(70, 140, 220)

        # Arc fraction driven by animation (1.0 = full circle, 0.0 = empty)
        self._arc_fraction: float = 1.0
        # Text seconds driven by animation
        self._display_seconds: int = seconds

        self._paused = False
        self._finished = False
        self._flash_pending = False

        # Game-clock reference for shared time origin (set via driveWith)
        self._clock: GameClock | None = None
        # Game-clock elapsed seconds at the moment this turn started
        self._turn_start_elapsed: int = 0
        # Fallback wall-clock origin used when no game clock is attached
        self._standalone_start: datetime.datetime = datetime.datetime.now(
            tz=datetime.UTC
        )

        # Fallback standalone timer (500 ms, same rate as GameClock)
        self._tick_timer = QTimer(self)
        self._tick_timer.setInterval(500)
        self._tick_timer.timeout.connect(self._poll)
        self._external_timer: QTimer | None = None

        # Smooth arc animation between ticks
        self._arc_anim = QPropertyAnimation(self, b"arcFraction", self)
        self._arc_anim.setDuration(950)
        self._arc_anim.setEasingCurve(QEasingCurve.Type.Linear)
        self._arc_anim.finished.connect(self._start_flash)

        # Text fade animation between number changes
        self._text_anim = QPropertyAnimation(self, b"displaySeconds", self)
        self._text_anim.setDuration(200)
        self._text_anim.setEasingCurve(QEasingCurve.Type.OutCubic)

        # Flash animation played on loop when finished
        self._opacity_effect = QGraphicsOpacityEffect(self)
        self._opacity_effect.setOpacity(1.0)
        self.setGraphicsEffect(self._opacity_effect)
        self._flash_anim = QPropertyAnimation(self._opacity_effect, b"opacity", self)
        self._flash_anim.setDuration(600)
        self._flash_anim.setLoopCount(-1)
        self._flash_anim.setKeyValueAt(0.0, 1.0)
        self._flash_anim.setKeyValueAt(0.5, 0.15)
        self._flash_anim.setKeyValueAt(1.0, 1.0)
        self._flash_anim.setEasingCurve(QEasingCurve.Type.InOutSine)

    # ------------------------------------------------------------------
    # Qt properties for animation
    # ------------------------------------------------------------------
    def getArcFraction(self) -> float:
        return self._arc_fraction

    def setArcFraction(self, value: float) -> None:
        self._arc_fraction = max(0.0, min(1.0, value))
        self.update()

    arcFraction = Property(float, getArcFraction, setArcFraction)

    def getDisplaySeconds(self) -> int:
        return self._display_seconds

    def setDisplaySeconds(self, value: int) -> None:
        self._display_seconds = int(value)
        self.update()

    displaySeconds = Property(int, getDisplaySeconds, setDisplaySeconds)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def driveWith(self, clock: GameClock) -> None:
        """Share the game clock's timer and time origin for perfect sync."""
        self._tick_timer.stop()
        self._clock = clock
        self._external_timer = clock.timer
        clock.timer.timeout.connect(self._poll)

    def start(self) -> None:
        """Begin the countdown from the current remaining time."""
        if self._finished:
            return
        self._paused = False
        # Snapshot the clock's current elapsed seconds as turn-start reference.
        # The countdown will compute turn_elapsed = game_elapsed - this value,
        # so both widgets cross second boundaries at the exact same instant.
        if self._clock is not None:
            self._turn_start_elapsed = self._game_elapsed()
        else:
            self._turn_start_elapsed = 0
            self._standalone_start = datetime.datetime.now(tz=datetime.UTC)
            self._tick_timer.start()
        self._animate_arc_to(self._arc_fraction, self._remaining / self._total, 950)

    def pause(self) -> None:
        """Freeze the countdown."""
        if self._paused or self._finished:
            return
        self._paused = True
        if self._external_timer is None:
            self._tick_timer.stop()
        self._arc_anim.stop()

    def resume(self) -> None:
        """Continue from where it was paused."""
        if not self._paused or self._finished:
            return
        self._paused = False
        # Re-anchor: we want to continue from _remaining seconds left, so set
        # the turn-start reference so that game_elapsed - ref == total - remaining.
        if self._clock is not None:
            self._turn_start_elapsed = self._game_elapsed() - (
                self._total - self._remaining
            )
        else:
            self._tick_timer.start()
        self._animate_arc_to(self._arc_fraction, self._remaining / self._total, 950)

    def reset(self, seconds: int | None = None) -> None:
        """Reset to full countdown, optionally changing the duration."""
        if self._external_timer is None:
            self._tick_timer.stop()
        self._flash_pending = False
        self._arc_anim.stop()
        self._text_anim.stop()
        self._flash_anim.stop()
        self._opacity_effect.setOpacity(1.0)
        self._finished = False
        self._paused = False
        self._turn_start_elapsed = 0
        if seconds is not None:
            self._total = seconds
        self._remaining = self._total
        self._arc_fraction = 1.0
        self._display_seconds = self._remaining
        self.update()

    def setColor(self, color: QColor) -> None:
        """Change the arc and text colour at runtime."""
        self._color = color
        self.update()

    def isRunning(self) -> bool:
        if self._external_timer is not None:
            return not self._paused and not self._finished
        return self._tick_timer.isActive()

    def isPaused(self) -> bool:
        return self._paused

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------
    def _game_elapsed(self) -> int:
        """Total game seconds elapsed — mirrors GameClock.showTime's computation."""
        assert self._clock is not None
        now = datetime.datetime.now(tz=datetime.UTC)
        return (now - self._clock.startTime).seconds + self._clock.accumulated

    def _poll(self) -> None:
        """Called every 500 ms; acts only when a new second boundary is crossed."""
        if self._paused or self._finished:
            return

        if self._clock is not None:
            turn_elapsed = self._game_elapsed() - self._turn_start_elapsed
        else:
            turn_elapsed = int(
                (
                    datetime.datetime.now(tz=datetime.UTC) - self._standalone_start
                ).total_seconds()
            )

        remaining = max(0, self._total - turn_elapsed)

        if remaining == self._remaining:
            return  # still the same second — nothing to update

        self._remaining = remaining

        self._text_anim.stop()
        self._text_anim.setStartValue(self._display_seconds)
        self._text_anim.setEndValue(remaining)
        self._text_anim.start()

        if remaining <= 0:
            if self._external_timer is None:
                self._tick_timer.stop()
            self._animate_arc_to(self._arc_fraction, 0.0, 950)
            self._flash_pending = True
            self._finished = True
            self.finished.emit()
        else:
            self._animate_arc_to(self._arc_fraction, remaining / self._total, 950)

    def _start_flash(self) -> None:
        if self._flash_pending:
            self._flash_pending = False
            self._flash_anim.start()

    def _animate_arc_to(self, start: float, end: float, ms: int) -> None:
        self._arc_anim.stop()
        self._arc_anim.setDuration(ms)
        self._arc_anim.setStartValue(start)
        self._arc_anim.setEndValue(end)
        self._arc_anim.start()

    # ------------------------------------------------------------------
    # Painting
    # ------------------------------------------------------------------
    def changeEvent(self, event) -> None:
        super().changeEvent(event)
        self.update()

    def paintEvent(self, event: QPaintEvent) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        color = (
            self.palette().color(
                self.palette().ColorGroup.Disabled, self.palette().ColorRole.Text
            )
            if not self.isEnabled()
            else self._color
        )

        side = min(self.width(), self.height())
        pen_width = max(4, side // 12)

        # Centre the drawing area
        x = (self.width() - side) // 2
        y = (self.height() - side) // 2
        margin = pen_width // 2 + 2

        rect_size = side - margin * 2

        # Background track (dim arc)
        track_color = QColor(color)
        track_color.setAlpha(40)
        pen = QPen(
            track_color, pen_width, Qt.PenStyle.SolidLine, Qt.PenCapStyle.FlatCap
        )
        painter.setPen(pen)
        painter.drawArc(
            x + margin,
            y + margin,
            rect_size,
            rect_size,
            90 * 16,  # start at top (Qt uses 1/16 degree units)
            -360 * 16,
        )

        # Foreground arc (depletes clockwise)
        if self._arc_fraction > 0.0:
            pen = QPen(color, pen_width, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap)
            painter.setPen(pen)
            span = int(-self._arc_fraction * 360 * 16)
            painter.drawArc(
                x + margin,
                y + margin,
                rect_size,
                rect_size,
                90 * 16,
                span,
            )

        # Seconds text
        painter.setPen(color)
        font = QFont(self.font())
        font.setBold(True)
        font.setPixelSize(max(12, rect_size // 2 - 2))
        painter.setFont(font)
        painter.drawText(
            x,
            y,
            side,
            side,
            Qt.AlignmentFlag.AlignCenter,
            str(self._display_seconds),
        )
