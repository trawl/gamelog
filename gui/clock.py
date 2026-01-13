#!/usr/bin/python
# -*- coding: utf-8 -*-

import datetime

from PySide6.QtCore import QEasingCurve, QPropertyAnimation, QTimer
from PySide6.QtWidgets import QFrame, QGraphicsOpacityEffect, QLCDNumber


class GameClock(QLCDNumber):
    def __init__(self, elapsed=0, parent=None):
        super(GameClock, self).__init__(parent)
        self.setSegmentStyle(QLCDNumber.SegmentStyle.Filled)
        self.startTime = datetime.datetime.now()
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

    def showTime(self):
        now = datetime.datetime.now()
        timediff = now - self.startTime
        elapsed = timediff.seconds + self.accumulated
        hours, remainder = divmod(elapsed, 3600)
        minutes, seconds = divmod(remainder, 60)
        if self.showcolons:
            text = "{0:02}:{1:02}:{2:02}".format(hours, minutes, seconds)
        else:
            text = "{0:02} {1:02} {2:02}".format(hours, minutes, seconds)
        if hours:
            self.setDigitCount(8)
        self.display(text)
        self.showcolons = not self.showcolons

    def pauseTimer(self):
        self.timer.stop()
        self.showcolons = True
        self.showTime()
        now = datetime.datetime.now()
        timediff = now - self.startTime
        self.accumulated += timediff.seconds
        self.blinkAnim.start()

    def unpauseTimer(self):
        self.blinkAnim.stop()
        self.opacityEffect.setOpacity(1.0)
        self._paintenabled = True
        self.startTime = datetime.datetime.now()
        self.timer.start(self.refreshinterval)
        self.showcolons = True
        self.showTime()

    def stopTimer(self):
        self.timer.stop()
        self.starTime = None
        self.accumulated = 0
