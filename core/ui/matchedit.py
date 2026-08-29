"""Dialog for manually editing a match's start, finish and duration."""

from __future__ import annotations

import datetime
from typing import TYPE_CHECKING, cast

from PySide6.QtCore import QDateTime, QTime
from PySide6.QtWidgets import (
    QDateTimeEdit,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QTimeEdit,
    QVBoxLayout,
)

if TYPE_CHECKING:
    from PySide6.QtWidgets import QWidget

    from core.engine.base import GameEngine


class MatchTimesEditDialog(QDialog):
    """Modal editor for a match's start/finish times and elapsed duration."""

    def __init__(self, engine: GameEngine, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.engine = engine
        self.setWindowTitle(self.tr("Match Times Edit"))
        self.widgetlayout = QVBoxLayout(self)
        self.formlayout = QFormLayout()
        self.widgetlayout.addLayout(self.formlayout)
        self.starttime = QDateTimeEdit(self)
        self.starttime.setCalendarPopup(True)
        self.starttime.setDisplayFormat("yyyy-MM-dd HH:mm:ss")
        # PySide accepts a datetime at runtime; the bundled stub only lists QDateTime.
        start = self.engine.getStartTime()
        if start is not None:
            self.starttime.setDateTime(start.replace(microsecond=0).astimezone())  # pyright: ignore[reportArgumentType]
        self.formlayout.addRow(self.tr("Start"), self.starttime)
        self.finishtime = QDateTimeEdit(self)
        self.finishtime.setCalendarPopup(True)
        self.finishtime.setDisplayFormat("yyyy-MM-dd HH:mm:ss")
        finish = self.engine.getFinishTime()
        if finish is not None:
            self.finishtime.setDateTime(finish.replace(microsecond=0).astimezone())  # pyright: ignore[reportArgumentType]
        self.formlayout.addRow(self.tr("Finish"), self.finishtime)
        self.elapsed = QTimeEdit(self)
        self.elapsed.setDisplayFormat("HH:mm:ss")
        self.elapsed.setTime(QTime(0, 0, 0, 0).addSecs(self.engine.getGameSeconds()))
        self.formlayout.addRow(self.tr("Duration"), self.elapsed)
        self.buttonbox = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save
            | QDialogButtonBox.StandardButton.Cancel
        )
        self.widgetlayout.addWidget(self.buttonbox)
        self.buttonbox.accepted.connect(self._onsave)
        self.buttonbox.rejected.connect(self.reject)
        self.starttime.dateTimeChanged.connect(self._recompute_elapsed)
        self.finishtime.dateTimeChanged.connect(self._recompute_elapsed)
        self.starttime.dateTimeChanged.connect(self._sanitycheck)
        self.finishtime.dateTimeChanged.connect(self._sanitycheck)
        self.elapsed.timeChanged.connect(self._sanitycheck)

    def _elapsedseconds(self) -> int:
        t = self.elapsed.time()
        return t.hour() * 3600 + t.minute() * 60 + t.second()

    def _sanitycheck(self) -> None:
        """Enable Save only when start < finish < now and duration fits."""
        now = QDateTime.currentDateTime()
        start = self.starttime.dateTime()
        end = self.finishtime.dateTime()
        elapsed = self._elapsedseconds()
        valid = start < end < now and elapsed > 0 and elapsed <= start.secsTo(end)
        self.buttonbox.button(QDialogButtonBox.StandardButton.Save).setEnabled(valid)

    def _recompute_elapsed(self) -> None:
        """Set the duration field to the span between start and finish."""
        start = self.starttime.dateTime()
        end = self.finishtime.dateTime()
        delta = max(start.secsTo(end), 0)
        h = (delta // 3600) % 24  # QTimeEdit caps at 23:59:59
        m = (delta % 3600) // 60
        s = delta % 60
        self.elapsed.setTime(QTime(h, m, s))

    def _onsave(self) -> None:
        """Persist the edited times to the engine and accept the dialog."""
        start = self.starttime.dateTime().toPython()
        finish = self.finishtime.dateTime().toPython()
        self.engine.updateTimes(
            cast(datetime.datetime, start).astimezone(datetime.UTC),
            cast(datetime.datetime, finish).astimezone(datetime.UTC),
            self._elapsedseconds(),
        )
        self.accept()
