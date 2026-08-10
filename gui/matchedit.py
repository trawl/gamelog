#!/usr/bin/env python
# -*- coding: utf-8 -*-
from PySide6.QtCore import QTime, QDateTime
from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QFormLayout,
    QDateTimeEdit,
    QTimeEdit,
    QDialogButtonBox
)


class MatchTimesEditDialog(QDialog):
    def __init__(self, engine, parent=None):
        super(MatchTimesEditDialog, self).__init__(parent)
        self.engine = engine
        self.setWindowTitle(self.tr("Match Times Edit"))
        self.widgetlayout = QVBoxLayout(self)
        self.formlayout = QFormLayout()
        self.widgetlayout.addLayout(self.formlayout)
        self.starttime = QDateTimeEdit(self)
        self.starttime.setCalendarPopup(True)
        self.starttime.setDisplayFormat("yyyy-MM-dd HH:mm:ss")
        self.starttime.setDateTime(self.engine.getStartTime())
        self.starttime.setMaximumDateTime(QDateTime.currentDateTime())
        self.formlayout.addRow(self.tr("Start"),self.starttime)
        self.finishtime = QDateTimeEdit(self)
        self.finishtime.setCalendarPopup(True)
        self.finishtime.setDisplayFormat("yyyy-MM-dd HH:mm:ss")
        self.finishtime.setDateTime(self.engine.getFinishTime())
        self.finishtime.setMaximumDateTime(QDateTime.currentDateTime())
        self.formlayout.addRow(self.tr("Finish"),self.finishtime)
        self.elapsed = QTimeEdit(self)
        self.elapsed.setDisplayFormat("HH:mm:ss")
        self.elapsed.setTime(QTime(0,0,0,0).addSecs(self.engine.getGameSeconds()))
        self.formlayout.addRow(self.tr("Duration"),self.elapsed)
        self.buttonbox = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel
        )
        self.widgetlayout.addWidget(self.buttonbox)
        self.buttonbox.accepted.connect(self._onsave)
        self.buttonbox.rejected.connect(self.reject)
        self.starttime.dateTimeChanged.connect(self._recompute_elapsed)
        self.finishtime.dateTimeChanged.connect(self._recompute_elapsed)

    def _elapsedseconds(self):
        t = self.elapsed.time()
        return t.hour() * 3600 + t.minute() * 60 + t.second()

    def _recompute_elapsed(self):
        start = self.starttime.dateTime()
        end = self.finishtime.dateTime()

        seconds = start.secsTo(end)
        if seconds < 0:
            seconds = 0
        h = (seconds // 3600) % 24  # QTimeEdit caps at 23:59:59
        m = (seconds % 3600) // 60
        s = seconds % 60
        self.elapsed.blockSignals(True)
        self.elapsed.setTime(QTime(h, m, s))
        self.elapsed.setMaximumTime(QTime(0,0,0).addSecs(seconds))
        self.starttime.setMaximumDateTime(end)
        self.finishtime.setMinimumDateTime(start)
        self.elapsed.blockSignals(False)

    def _onsave(self):
        self.engine.updateTimes(self.starttime.dateTime().toPython(), self.finishtime.dateTime().toPython(), self._elapsedseconds())
        self.accept()
