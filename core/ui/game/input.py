"""Score input widgets: spinboxes, clickable counters and bonus buttons."""

from __future__ import annotations

import logging

from PySide6 import QtCore, QtGui
from PySide6.QtCore import (
    QEasingCurve,
    QFile,
    QObject,
    QPropertyAnimation,
    QRectF,
    QSize,
)
from PySide6.QtGui import (
    QColor,
    QFont,
    QImage,
    QKeyEvent,
    QMouseEvent,
    QPainter,
    QPainterPath,
    QPaintEvent,
    QWheelEvent,
)
from PySide6.QtSvg import QSvgRenderer
from PySide6.QtWidgets import (
    QGraphicsColorizeEffect,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QSizePolicy,
    QWidget,
)

from core.engine.engine import RoundGameEngine
from core.ui.game.colours import PlayerColours

logger = logging.getLogger(__name__)


class SpaceFilter(QtCore.QObject):
    """Event filter that turns a Space key press into a ``spacePressed`` signal."""

    spacePressed = QtCore.Signal()

    def eventFilter(self, obj: QObject, event) -> bool:
        if (
            event.type() == QtCore.QEvent.Type.KeyPress
            and event.key() == QtCore.Qt.Key.Key_Space
        ):
            self.spacePressed.emit()
            return True  # swallow the event
        return False


class ScoreSpinBox(QWidget):
    """A digits-only score field with up/down steppers and space handling."""

    valueChanged = QtCore.Signal(object)
    spacePressed = QtCore.Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._value: int | None = 0
        self._minimum = 0
        self._maximum = 200
        self._start = 0
        self._step = 1
        self._hideMinimum = True
        self.pcolour: QColor | None = None
        self.initUI()

    def initUI(self) -> None:
        """Build the line edit, stepper buttons, validator and styling."""
        self.line_edit = QLineEdit()
        self.line_edit.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.line_edit.setInputMethodHints(QtCore.Qt.InputMethodHint.ImhDigitsOnly)
        self.line_edit.setMinimumWidth(40)
        self.line_edit.setSizePolicy(
            QSizePolicy.Policy.MinimumExpanding, QSizePolicy.Policy.Preferred
        )

        self._validator = QtGui.QIntValidator(self._minimum, self._maximum, self)
        self.line_edit.setValidator(self._validator)

        self.space_filter = SpaceFilter()
        self.line_edit.installEventFilter(self.space_filter)
        self.space_filter.spacePressed.connect(self.onSpacePressed)

        self.up_button = QPushButton()
        self.down_button = QPushButton()
        self.up_button.setSizePolicy(
            QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred
        )
        self.down_button.setSizePolicy(
            QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred
        )

        self.up_button.setText("▲")
        self.down_button.setText("▼")

        self.up_button.setAutoRepeat(True)
        self.down_button.setAutoRepeat(True)

        group = QHBoxLayout()
        group.setSpacing(4)
        group.setContentsMargins(0, 0, 0, 0)
        group.addWidget(self.down_button, stretch=1)
        group.addWidget(self.line_edit, stretch=2)
        group.addWidget(self.up_button, stretch=1)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.addLayout(group)

        self._text_css = """
            QLineEdit {{
                font-size: 24px;
                font-weight: bold;
                padding: 2px;
                color:rgb({0},{1},{2});
            }}
            QLineEdit:focus {{
                border: 2px solid rgb({0},{1},{2}) ;   /* highlight color */
            }}
            QLineEdit:focus:hover {{
                border: 2px solid rgb({0},{1},{2}) ;   /* highlight color */
            }}
            QLineEdit:hover {{
                border: 1px solid rgba({0},{1},{2},150) ;   /* highlight color */
            }}
        """
        self._text_css_colourless = ""
        self._updateStyle()

        self.up_button.clicked.connect(self.step_up)
        self.down_button.clicked.connect(self.step_down)
        self.line_edit.textChanged.connect(self._commit_text)
        self.line_edit.editingFinished.connect(self._snap_to_step)

        if self._value is not None:
            self.setValue(self._value)

    def _button_style(self) -> str:
        return """
        QToolButton {
            font-size: 18px;
            font-weight: bold;
            border: 1px solid #555555;
            border-radius: 6px;
        }
        """

    def setHideMinimum(self, hidemin: bool) -> None:
        self._hideMinimum = hidemin

    def setColour(self, colour: QColor) -> None:
        self.pcolour = colour
        self._updateStyle()

    def _updateStyle(self) -> None:
        """Apply the coloured or colourless line-edit stylesheet."""
        if not self.isEnabled():
            self.line_edit.setStyleSheet(self._text_css.format(128, 128, 128))
        elif self.pcolour:
            self.line_edit.setStyleSheet(
                self._text_css.format(
                    self.pcolour.red(), self.pcolour.green(), self.pcolour.blue()
                )
            )
        else:
            self.line_edit.setStyleSheet(self._text_css_colourless)

    def changeEvent(self, event: QtCore.QEvent) -> None:
        super().changeEvent(event)
        if event.type() == QtCore.QEvent.Type.EnabledChange:
            self._updateStyle()

    def value(self) -> int | None:
        return self._value

    def setValue(self, value: int | None) -> None:
        """Clamp and store ``value`` (``None`` clears the field)."""
        if value is None:
            old = self._value
            self._value = None
            self.line_edit.setText("")
            if old is not None:
                self.valueChanged.emit(None)
        else:
            value = max(self._minimum, min(self._maximum, value))
            old = self._value
            self._value = (
                value  # set before setText to prevent _commit_text re-entrancy
            )
            if self._hideMinimum and value == self._minimum:
                self.line_edit.setText("")
            else:
                self.line_edit.setText(str(value))
            if value != old:
                self.valueChanged.emit(value)
        self._update_buttons()

    def setStep(self, step: int) -> None:
        self._step = step

    def setFocus(
        self, reason: QtCore.Qt.FocusReason = QtCore.Qt.FocusReason.OtherFocusReason
    ) -> None:
        self.line_edit.setFocus(reason)

    def _snap_to_step(self) -> None:
        """Round the value down to the nearest multiple of the step size."""
        if self._value is not None and self._step > 1:
            offset = self._value - self._minimum
            new_value = self._minimum + (offset // self._step) * self._step
            if self._value != new_value:
                self.setValue(new_value)

    def step_up(self) -> None:
        self.line_edit.setFocus()
        if self._value is None:
            self.setValue(self._start)
        else:
            self.setValue(self._value + self._step)

    def step_down(self) -> None:
        self.line_edit.setFocus()
        if self._value is None:
            self.setValue(self._start)
        else:
            self.setValue(self._value - self._step)

    def _commit_text(self) -> None:
        """Parse the line-edit text into the current value."""
        try:
            value = int(self.line_edit.text())
        except ValueError:
            value = self._value
        self.setValue(value)

    def setRange(self, minimum: int, maximum: int, start: int | None = None) -> None:
        """Set the allowed value range and the default start value."""
        self._minimum = minimum
        self._maximum = maximum
        self._start = minimum if start is None else start
        self._validator = QtGui.QIntValidator(self._minimum, self._maximum, self)
        self.line_edit.setValidator(self._validator)
        self.setValue(self._value)

    def setMinimum(self, minimum: int) -> None:
        self.setRange(minimum, self._maximum)

    def setMaximum(self, maximum: int) -> None:
        self.setRange(self._minimum, maximum)

    def setSingleStep(self, step: int) -> None:
        self._step = max(1, step)

    def clear(self) -> None:
        self.line_edit.clear()

    def reset(self) -> None:
        self.setValue(None)

    def setReadOnly(self, ro: bool) -> None:
        self.line_edit.setReadOnly(ro)
        self.up_button.setDisabled(ro)
        self.down_button.setDisabled(ro)

    def lineEdit(self) -> QLineEdit:
        return self.line_edit

    def _update_buttons(self) -> None:
        """Enable/disable the steppers based on the value and bounds."""
        if not self.line_edit.isReadOnly():
            self.up_button.setEnabled(
                self._value is None or self._value < self._maximum
            )
            self.down_button.setEnabled(
                self._value is None or self._value > self._minimum
            )

    def wheelEvent(self, event: QWheelEvent) -> None:
        if self.line_edit.isReadOnly():
            return
        if event.angleDelta().y() > 0:
            self.step_up()
        else:
            self.step_down()
        event.accept()

    def textChangedAction(self, text: str) -> None:
        try:
            self.valueChanged.emit(int(text))
        except ValueError:
            pass

    def onSpacePressed(self) -> None:
        self.spacePressed.emit()

    def setDisabled(self, o: bool) -> None:
        super().setDisabled(o)
        if o:
            self.setValue(self._start)


class ClickableCounter(QLabel):
    """Circular click-to-cycle counter with player colour styling.

    Left-click / right-click cycle the value. Keyboard: digit keys set the
    value and advance focus; Up/Down step without moving focus; Tab/Backtab
    move focus. Gains a pulsing candidate animation while focused.
    """

    valueChanged = QtCore.Signal(int)
    focusAdvance = QtCore.Signal()
    focusBack = QtCore.Signal()

    _NUMBER_KEYS = {
        QtCore.Qt.Key.Key_0: 0,
        QtCore.Qt.Key.Key_1: 1,
        QtCore.Qt.Key.Key_2: 2,
        QtCore.Qt.Key.Key_3: 3,
        QtCore.Qt.Key.Key_4: 4,
        QtCore.Qt.Key.Key_5: 5,
        QtCore.Qt.Key.Key_6: 6,
        QtCore.Qt.Key.Key_7: 7,
        QtCore.Qt.Key.Key_8: 8,
        QtCore.Qt.Key.Key_9: 9,
    }

    def __init__(
        self,
        minimum: int = 0,
        maximum: int = 4,
        size: int = 60,
        colour: QColor | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(str(minimum), parent)
        self._minimum = minimum
        self._maximum = maximum
        self._value = minimum
        self._enabled = True
        self._candidate = False
        self.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.setFixedSize(size, size)
        self.setFocusPolicy(QtCore.Qt.FocusPolicy.StrongFocus)
        self._colour = colour if colour is not None else QColor(180, 180, 180)

        self._effect = QGraphicsColorizeEffect(self)
        self._effect.setColor(self._colour)
        self._effect.setStrength(0.0)
        self.setGraphicsEffect(self._effect)

        self._anim = QPropertyAnimation(self._effect, b"strength")
        self._anim.setDuration(1400)
        self._anim.setStartValue(0.0)
        self._anim.setKeyValueAt(0.6, 0.6)
        self._anim.setEndValue(0.0)
        self._anim.setLoopCount(-1)

        self._apply_style()

    def value(self) -> int:
        return self._value

    def setValue(self, v: int) -> None:
        v = max(self._minimum, min(self._maximum, v))
        if v != self._value:
            self._value = v
            self.setText(str(self._value))
            self.valueChanged.emit(self._value)

    def setRange(self, minimum: int, maximum: int, default: int | None = None) -> None:
        self._minimum = minimum
        self._maximum = maximum
        # Clamp current value; never reset it unless it falls out of range.
        self._value = max(self._minimum, min(self._maximum, self._value))
        self.setText(str(self._value))

    def setColour(self, colour: QColor) -> None:
        self._colour = colour
        self._effect.setColor(colour)
        self._apply_style()

    def setEnabled(self, enabled: bool) -> None:  # type: ignore[override]
        self._enabled = enabled
        super().setEnabled(enabled)
        self._apply_style()

    def isCandidate(self) -> bool:
        return self._candidate

    def setCandidate(self, value: bool) -> None:
        value = bool(value)
        if self._candidate == value:
            return
        self._candidate = value
        if value:
            self._anim.start()
        else:
            self._anim.stop()
            self._effect.setStrength(0.0)

    def _apply_style(self) -> None:
        c = self._colour
        r, g, b = c.red(), c.green(), c.blue()
        alpha = 255 if self._enabled else 80
        self.setStyleSheet(
            f"""
            ClickableCounter {{
                font-size: 22px;
                font-weight: bold;
                color: rgba({r},{g},{b},{alpha});
                border: 2px solid rgba({r},{g},{b},{alpha});
                border-radius: {self.width() // 2}px;
            }}
            ClickableCounter:disabled {{
                color: rgba({r},{g},{b},60);
                border: 2px solid rgba({r},{g},{b},40);
            }}
            ClickableCounter:focus {{
                border: 3px solid rgba({r},{g},{b},{alpha});
            }}
            """
        )

    def focusInEvent(self, event) -> None:
        self.setCandidate(True)
        super().focusInEvent(event)

    def focusOutEvent(self, event) -> None:
        self.setCandidate(False)
        super().focusOutEvent(event)

    def keyPressEvent(self, event: QKeyEvent) -> None:
        key = QtCore.Qt.Key(event.key())
        digit = self._NUMBER_KEYS.get(key)
        if digit is not None:
            if self._minimum <= digit <= self._maximum:
                self.setValue(digit)
            self.focusAdvance.emit()
            return
        if key == QtCore.Qt.Key.Key_Up:
            new = self._value + 1
            self.setValue(new if new <= self._maximum else self._minimum)
            return
        if key == QtCore.Qt.Key.Key_Down:
            new = self._value - 1
            self.setValue(new if new >= self._minimum else self._maximum)
            return
        if key == QtCore.Qt.Key.Key_Tab:
            self.focusAdvance.emit()
            return
        if key == QtCore.Qt.Key.Key_Backtab:
            self.focusBack.emit()
            return
        if key == QtCore.Qt.Key.Key_Backspace:
            self.setValue(self._minimum)
            self.focusBack.emit()
            return
        event.ignore()

    def mousePressEvent(self, event: QMouseEvent) -> None:
        if not self._enabled:
            return
        self.setFocus()
        if event.button() == QtCore.Qt.MouseButton.LeftButton:
            new = self._value + 1
            self.setValue(new if new <= self._maximum else self._minimum)
        elif event.button() == QtCore.Qt.MouseButton.RightButton:
            new = self._value - 1
            self.setValue(new if new >= self._minimum else self._maximum)
        else:
            super().mousePressEvent(event)
            return
        super().mousePressEvent(event)


class BonusButton(QPushButton):
    """Circular toggle button counting a per-round bonus, with SVG/PNG icon."""

    bonusChanged = QtCore.Signal(str, object)

    def __init__(
        self,
        bonus_name: str,
        maximum: int = 1,
        colour: QColor | None = None,
        size: int = 32,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)

        self.bonus_name = bonus_name
        self.maximum = maximum
        self.count = 0
        self.button_size = size
        self.highlight_colour = colour if colour else QColor(200, 0, 0)

        self.svg_renderer: QSvgRenderer | None = None
        self._disabled_svg_cache: dict = {}

        svg_path = f":/icons/{bonus_name}.svg"
        png_path = f":/icons/{bonus_name}.png"

        if QFile.exists(svg_path):
            self.svg_renderer = QSvgRenderer(svg_path)
            if not self.svg_renderer.isValid():
                self.svg_renderer = None

        if self.svg_renderer is None and QFile.exists(png_path):
            original_image = QImage(png_path)
            self.image = original_image.scaled(
                self.button_size,
                self.button_size,
                QtCore.Qt.AspectRatioMode.KeepAspectRatio,
                QtCore.Qt.TransformationMode.SmoothTransformation,
            )
            self.grey_image = self.image.convertToFormat(
                QImage.Format.Format_Grayscale8
            )
        elif self.svg_renderer is None:
            original_image = QImage(
                self.button_size,
                self.button_size,
                QImage.Format.Format_ARGB32_Premultiplied,
            )
            original_image.fill(QtCore.Qt.GlobalColor.transparent)
            painter = QPainter(original_image)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            painter.setBrush(QColor("#D3D3D3"))
            painter.setPen(QtCore.Qt.PenStyle.NoPen)
            painter.drawEllipse(2, 2, self.button_size - 4, self.button_size - 4)
            painter.setPen(QColor("#333333"))
            painter.setFont(
                QFont("Arial", int(self.button_size * 0.4), QFont.Weight.Bold)
            )
            painter.drawText(
                original_image.rect(),
                QtCore.Qt.AlignmentFlag.AlignCenter,
                bonus_name.upper(),
            )
            painter.end()
            self.image = original_image
            self.grey_image = original_image.convertToFormat(
                QImage.Format.Format_Grayscale8
            )

        self.setCheckable(True)
        self.setFlat(True)
        self.setStyleSheet("border: none;")
        self.setFixedSize(self.button_size, self.button_size)

        self._fade_alpha = 0.0
        self.fade_anim = QPropertyAnimation(self, b"fade_alpha")
        self.fade_anim.setDuration(400)
        self.fade_anim.setEasingCurve(QEasingCurve.Type.OutCubic)

        self.clicked.connect(self.plusone)

    def setColour(self, colour: QColor) -> None:
        self.highlight_colour = colour

    def plusone(self) -> None:
        """Advance the bonus count by one (wrapping past the maximum)."""
        old_value = self.count
        self.count = (self.count + 1) % (self.maximum + 1)
        self.setChecked(self.count > 0)

        if old_value == 0 and self.count > 0:
            self.fade_anim.stop()
            self.fade_anim.setStartValue(0.0)
            self.fade_anim.setEndValue(1.0)
            self.fade_anim.start()
        elif old_value > 0 and self.count == 0:
            self.fade_anim.stop()
            self.fade_anim.setStartValue(1.0)
            self.fade_anim.setEndValue(0.0)
            self.fade_anim.start()

        self.bonusChanged.emit(self.bonus_name, self)
        self.update()

    def get_fade_alpha(self) -> float:
        return self._fade_alpha

    def set_fade_alpha(self, value: float) -> None:
        self._fade_alpha = float(value)
        self.update()

    fade_alpha = QtCore.Property(float, get_fade_alpha, set_fade_alpha)

    def getValue(self) -> int:
        return self.count if self.isEnabled() else 0

    def setChecked(self, checked: bool) -> None:
        if not checked:
            self.count = 0
        super().setChecked(checked)

    def sizeHint(self) -> QSize:
        return QtCore.QSize(self.button_size, self.button_size)

    def setMaximum(self, maximum: int) -> None:
        """Set the count ceiling, clamping the current count to fit."""
        self.maximum = maximum
        if self.count > self.maximum:
            self.count = self.maximum
            if self.count == 0:
                self.setChecked(False)
            self.update()

    def _disabled_svg_image(self, dpr: float) -> QImage:
        """Return a cached greyed-out rasterisation of the SVG icon."""
        key = (self.width(), self.height(), dpr)
        if key not in self._disabled_svg_cache:
            image = QImage(
                round(self.width() * dpr),
                round(self.height() * dpr),
                QImage.Format.Format_ARGB32_Premultiplied,
            )
            image.fill(QtCore.Qt.GlobalColor.transparent)
            image_painter = QPainter(image)
            image_painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            if self.svg_renderer:
                self.svg_renderer.render(image_painter, QRectF(image.rect()))
            image_painter.end()
            for y in range(image.height()):
                for x in range(image.width()):
                    colour = image.pixelColor(x, y)
                    grey = round(
                        0.299 * colour.red()
                        + 0.587 * colour.green()
                        + 0.114 * colour.blue()
                    )
                    colour.setRgb(grey, grey, grey, colour.alpha())
                    image.setPixelColor(x, y, colour)
            self._disabled_svg_cache[key] = image
        return self._disabled_svg_cache[key]

    def paintEvent(self, event: QPaintEvent) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)

        path = QPainterPath()
        radius = min(self.width(), self.height()) / 2
        center = self.rect().center()
        path.addEllipse(center, radius, radius)

        if self.svg_renderer is not None:
            if self.isEnabled():
                self.svg_renderer.render(painter, QRectF(self.rect()))
            else:
                painter.drawImage(
                    self.rect(),
                    self._disabled_svg_image(painter.device().devicePixelRatioF()),
                )
                self.setChecked(False)
        else:
            if self.isEnabled():
                img_to_draw = self.image
            else:
                img_to_draw = self.grey_image
                self.setChecked(False)
            painter.drawImage(self.rect(), img_to_draw)

        if self.count > 0:
            alpha = int(255 * self._fade_alpha)
            ring_radius = radius - 2
            colour = QColor(self.highlight_colour)
            colour.setAlpha(alpha)
            pen = painter.pen()
            pen.setColor(colour)
            pen.setWidth(4)
            painter.setPen(pen)
            painter.setBrush(QtCore.Qt.BrushStyle.NoBrush)
            center.setX(center.x() + 1)
            center.setY(center.y() + 1)
            painter.drawEllipse(center, ring_radius, ring_radius)

        if self.count >= 1 and self.maximum > 1:
            overlay_color = QColor(0, 0, 0, 120)
            painter.setBrush(overlay_color)
            painter.setPen(QtCore.Qt.PenStyle.NoPen)
            circle_diameter = min(self.width(), self.height()) * 0.45
            circle_rect = QRectF(
                (self.width() - circle_diameter) / 2,
                (self.height() - circle_diameter) / 2,
                circle_diameter,
                circle_diameter,
            )
            painter.drawEllipse(circle_rect)
            painter.setPen(self.highlight_colour)
            font = QFont("Arial", int(circle_diameter * 0.9), QFont.Weight.Bold)
            painter.setFont(font)
            painter.drawText(
                self.rect(), QtCore.Qt.AlignmentFlag.AlignCenter, str(self.count)
            )

        painter.end()


class GameInputWidget(QWidget):
    """Base score-input widget; games subclass it for their own controls."""

    enterPressed = QtCore.Signal()
    changed = QtCore.Signal()
    player_colours: list[QColor] = PlayerColours

    def playerColour(self, player: str) -> QColor:
        """Walk up the widget tree to find the GameWidget's colour mapping."""
        widget = self.parent()
        while widget is not None:
            if hasattr(widget, "colour_map"):
                return widget.playerColour(player)  # type: ignore[union-attr]
            widget = widget.parent()
        idx = self.engine.getListPlayers().index(player)
        return self.player_colours[idx % len(self.player_colours)]

    def __init__(self, engine: RoundGameEngine, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.engine = engine
        self.winnerSelected = ""
        self.playerInputList: dict = {}
        self.initUI()

    def initUI(self) -> None:
        """Build the input controls; overridden by concrete games."""

    def retranslateUI(self) -> None:
        """Refresh input labels for the current language; overridden."""

    def getWinner(self) -> str:
        """Return the player with the highest current input score."""
        maxScore = -1000000
        for player, score in self.getScores().items():
            if score > maxScore:
                maxScore = score
                self.winnerSelected = player
        return self.winnerSelected

    def getScores(self) -> dict[str, int]:
        """Return the current per-player score map from the input widgets."""
        scores = {}
        for player, piw in self.playerInputList.items():
            scores[player] = piw.getScore()
        return scores

    def reset(self) -> None:
        """Clear the selected winner and reset every player's input."""
        self.winnerSelected = ""
        for piw in self.playerInputList.values():
            piw.reset()

    def changedWinner(self, winner: str) -> None:
        """Record a newly selected winner, resetting the previous one."""
        logger.debug("Changing winner to %s", winner)
        winner = str(winner)
        if self.winnerSelected != "":
            self.playerInputList[self.winnerSelected].reset()
        self.winnerSelected = winner

    def keyPressEvent(self, event: QKeyEvent) -> None:
        if event.key() in (QtCore.Qt.Key.Key_Return, QtCore.Qt.Key.Key_Enter):
            self.enterPressed.emit()
            event.accept()
        return super().keyPressEvent(event)

    def mousePressEvent(self, event: QMouseEvent) -> None:
        self.setFocus()
        return super().mousePressEvent(event)

    def updatePlayerOrder(self) -> None:
        """Recolour player input widgets; override to also reorder layout."""
        for player, piw in self.playerInputList.items():
            if hasattr(piw, "setColour"):
                piw.setColour(self.playerColour(player))


__all__ = [
    "SpaceFilter",
    "ScoreSpinBox",
    "ClickableCounter",
    "BonusButton",
    "GameInputWidget",
]
