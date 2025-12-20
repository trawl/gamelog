#!/usr/bin/python
# -*- coding: utf-8 -*-

import datetime

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QFrame, QLCDNumber


class GameClock(QLCDNumber):
    def __init__(self, elapsed=0, parent=None):
        super(GameClock, self).__init__(parent)
        self.setSegmentStyle(QLCDNumber.SegmentStyle.Filled)
        self.startTime = datetime.datetime.now()
        self.accumulated = elapsed
        self.paused = False
        self._paintenabled = True
        self.refreshinterval = 50
        self.timer = QTimer(self)
        self.blinkTimer = QTimer(self)
        self.blinkTimer.setInterval(500)  # toggle twice per second = 1 Hz blink
        self.blinkTimer.timeout.connect(self.blink)
        self.timer.start(self.refreshinterval)
        self.setDigitCount(5)
        self.showTime()
        self.timer.timeout.connect(self.showTime)
        self.setFrameStyle(QFrame.Shape.NoFrame)

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
        self.blinkTimer.start()

    def unpauseTimer(self):
        self.blinkTimer.stop()
        self._paintenabled = True
        self.startTime = datetime.datetime.now()
        self.timer.start(self.refreshinterval)
        self.showTime()
        self.update()

    def stopTimer(self):
        self.timer.stop()
        self.blinkTimer.stop()
        self.starTime = None
        self.accumulated = 0

    def blink(self):
        self._paintenabled = not self._paintenabled
        self.update()

    def paintEvent(self, event):
        if not self._paintenabled:
            return
        super().paintEvent(event)
