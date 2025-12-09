#!/usr/bin/env python
# -*- coding: utf-8 -*-
from PySide6.QtCore import Property, QEasingCurve, QPropertyAnimation, QRectF, Qt
from PySide6.QtGui import QColor, QFont, QLinearGradient, QPainter
from PySide6.QtWidgets import QWidget


class StepProgressBar(QWidget):
    def __init__(self, steps, parent=None):
        super().__init__(parent)
        self.steps = steps
        self.current_step = 0

        # Animation state
        self._highlight_pos = 0.0  # float representing the "center" of highlight
        self._highlight_target = 0.0

        self.highlight_anim = QPropertyAnimation(self, b"highlightPos")
        self.highlight_anim.setDuration(350)
        self.highlight_anim.setEasingCurve(QEasingCurve.Type.OutCubic)

        self.setMinimumHeight(36)

        # COLORS ----------------------------------------
        self.color_done_top = QColor(110, 220, 120)
        self.color_done_bottom = QColor(70, 160, 80)

        # self.color_active_top = QColor(255, 230, 130)
        # self.color_active_bottom = QColor(230, 180, 40)

        self.color_active_top = QColor(50, 90, 200)  # lighter blue
        self.color_active_bottom = QColor(30, 60, 150)  # deeper blue

        self.color_pending_top = QColor(120, 120, 120)
        self.color_pending_bottom = QColor(70, 70, 70)

        self.separator_color = QColor(40, 40, 40)

        # Highlight glow band
        # self.highlight_color = QColor(255, 255, 180, 90)
        self.highlight_color = QColor(120, 160, 255, 110)

        # Gloss overlay (subtle)
        self.gloss_alpha = 80

    # ---------------------------------------------
    # PROPERTIES FOR ANIMATION
    # ---------------------------------------------
    def getHighlightPos(self):
        return self._highlight_pos

    def setHighlightPos(self, value):
        self._highlight_pos = value
        self.update()

    highlightPos = Property(float, getHighlightPos, setHighlightPos)

    # ---------------------------------------------
    # PUBLIC API
    # ---------------------------------------------
    def setSteps(self, steps, keep_current=False):
        self.steps = [str(s) for s in steps]  # guarantee strings
        if keep_current:
            self.current_step = min(self.current_step, len(self.steps) - 1)
        else:
            self.current_step = 0

        self.update()

    def setCurrentStep(self, step):
        step = int(step)
        if step == self.current_step or step < 0 or step >= len(self.steps):
            return

        old_step = self.current_step
        self.current_step = step

        # Trigger highlight slide animation
        self._highlight_target = float(step)
        self.highlight_anim.stop()
        self.highlight_anim.setStartValue(float(old_step))
        self.highlight_anim.setEndValue(self._highlight_target)
        self.highlight_anim.start()

        self.update()

    # ---------------------------------------------
    # PAINTING
    # ---------------------------------------------
    def paintEvent(self, event):
        if not self.steps:
            return super().paintEvent(event)

        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        total = len(self.steps)
        W = self.width()
        H = self.height()
        segW = W / total

        # ---------------------------
        # Draw each segment (with gradient)
        # ---------------------------
        for i, label in enumerate(self.steps):
            left = i * segW
            rect = QRectF(left, 0, segW, H)

            # Determine state
            if i < self.current_step:
                top_color = self.color_done_top
                bottom_color = self.color_done_bottom
            elif i == self.current_step:
                top_color = self.color_active_top
                bottom_color = self.color_active_bottom
            else:
                top_color = self.color_pending_top
                bottom_color = self.color_pending_bottom

            # Gradient Fill
            grad = QLinearGradient(rect.topLeft(), rect.bottomLeft())
            grad.setColorAt(0, top_color)
            grad.setColorAt(1, bottom_color)
            painter.fillRect(rect, grad)

            # Subtle Gloss (top 40%)
            gloss_rect = QRectF(left, 0, segW, H * 0.4)
            gloss_grad = QLinearGradient(gloss_rect.topLeft(), gloss_rect.bottomLeft())
            c1 = QColor(255, 255, 255, self.gloss_alpha)
            c2 = QColor(255, 255, 255, 0)
            gloss_grad.setColorAt(0, c1)
            gloss_grad.setColorAt(1, c2)
            painter.fillRect(gloss_rect, gloss_grad)

            # Separator (except last)
            # if i < total - 1:
            #     painter.setPen(QPen(self.separator_color, 2))
            #     painter.drawLine(
            #         int(left + segW), int(H * 0.15), int(left + segW), int(H * 0.85)
            #     )

        # ---------------------------
        # DRAW SLIDING HIGHLIGHT
        # ---------------------------
        highlight_x = (self._highlight_pos + 0.5) * segW
        highlight_rect = QRectF(highlight_x - segW * 0.5, 0, segW, H)

        glow_grad = QLinearGradient(
            highlight_rect.topLeft(), highlight_rect.bottomLeft()
        )
        glow_top = QColor(self.highlight_color)
        glow_bottom = QColor(self.highlight_color)
        glow_bottom.setAlpha(40)

        glow_grad.setColorAt(0, glow_top)
        glow_grad.setColorAt(1, glow_bottom)

        painter.fillRect(highlight_rect, glow_grad)

        # ---------------------------
        # DRAW LABELS
        # ---------------------------
        painter.setPen(Qt.GlobalColor.white)
        font = QFont(self.font())
        font.setBold(True)
        painter.setFont(font)

        for i, label in enumerate(self.steps):
            left = i * segW
            rect = QRectF(left, 0, segW, H)
            painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, str(label))
