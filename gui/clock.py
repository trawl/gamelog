#!/usr/bin/python
# -*- coding: utf-8 -*-

import datetime
try:
    from PySide6.QtCore import QTimer
    from PySide6.QtWidgets import QLCDNumber
except ImportError:
    from PyQt5.QtCore import QTimer
    from PyQt5.QtWidgets import QLCDNumber


class GameClock(QLCDNumber):

    def __init__(self, elapsed=0, parent=None):
        super(GameClock, self).__init__(parent)
        self.setSegmentStyle(QLCDNumber.Filled)
        self.startTime = datetime.datetime.now()
        self.accumulated = elapsed
        self.paused = False
        self.refreshinterval = 50
        self.timer = QTimer(self)
        self.timer.start(self.refreshinterval)
        try:
            self.setDigitCount(5)
        except TypeError:
            self.setNumDigits(5)
        self.showTime()
        self.timer.timeout.connect(self.showTime)

    def showTime(self):

        now = datetime.datetime.now()
        timediff = now - self.startTime
        elapsed = timediff.seconds + self.accumulated
        hours, remainder = divmod(elapsed, 3600)
        minutes, seconds = divmod(remainder, 60)
        text = "{0:02}:{1:02}:{2:02}".format(hours, minutes, seconds)
        if hours:
            self.setDigitCount(8)
        self.display(text)

    def pauseTimer(self):
        self.timer.stop()
        now = datetime.datetime.now()
        timediff = now - self.startTime
        self.accumulated += timediff.seconds

    def unpauseTimer(self):
        self.startTime = datetime.datetime.now()
        self.timer.start(self.refreshinterval)
        self.showTime()

    def stopTimer(self):
        self.timer.stop()
        self.starTime = None
        self.accumulated = None
