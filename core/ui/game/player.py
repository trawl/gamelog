"""Per-player score display widgets."""

from __future__ import annotations

from PySide6 import QtCore, QtGui
from PySide6.QtCore import QSize
from PySide6.QtGui import QColor, QPainter, QPaintEvent
from PySide6.QtWidgets import (
    QFrame,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLCDNumber,
    QWidget,
)

from core.ui.game.colours import PlayerColours


class GamePlayerWidget(QGroupBox):
    """Per-player score box with an LCD readout and dealer/winner overlay."""

    def __init__(
        self, nick: str, colour: QColor | None = None, parent: QWidget | None = None
    ) -> None:
        if not colour:
            colour = QtGui.QColor()
        super().__init__(parent)
        self.player = nick
        self.pcolour = colour
        self.initUI()

    def initUI(self) -> None:
        """Build the LCD score display and load the overlay pixmaps."""
        self.setTitle(self.player)
        self.mainLayout = QHBoxLayout(self)
        self.scoreLCD = QLCDNumber(self)
        self.scoreLCD.setSegmentStyle(QLCDNumber.SegmentStyle.Flat)
        self.scoreLCD.setFrameStyle(QFrame.Shape.NoFrame)
        self.mainLayout.addWidget(self.scoreLCD)
        self.scoreLCD.setDigitCount(3)
        self.scoreLCD.setMinimumWidth(50)
        self.scoreLCD.display(0)
        self.title_size = 28
        self.css = """
            QGroupBox {{ font-size: {3}px; font-weight: bold; color:rgb({0},{1},{2});}}

            QGroupBox[ko="true"] {{
                color: rgba({0},{1},{2},70);   /* lower alpha */
            }}

            QGroupBox::title {{
                subcontrol-origin: margin;
                subcontrol-position: top center;
                padding: 0 {4}px;
                background-color: transparent;
            }}
            QGroupBox QLCDNumber {{ color:rgb({0},{1},{2});}}
        """
        self.setColour(self.pcolour)

        self.dealerPixmap = QtGui.QPixmap(":/icons/cards.png")
        self.nonDealerPixmap = QtGui.QPixmap()
        self.winnerPixmap = QtGui.QPixmap(":/icons/winner.png")

        self.background = None
        self.bg_opacity = 1
        self.bg_size = 40
        self.unsetDealer()

    def updateDisplay(self, points: int) -> None:
        """Display ``points``, widening the LCD for 4-digit values."""
        if points >= 1000 or points <= -100:
            self.scoreLCD.setDigitCount(4)
        else:
            self.scoreLCD.setDigitCount(3)
        self.scoreLCD.display(points)

    def setDealer(self) -> None:
        self.background = self.dealerPixmap
        self.update()

    def unsetDealer(self) -> None:
        self.background = None
        self.update()

    def setWinner(self) -> None:
        self.background = self.winnerPixmap
        self.update()

    def setColour(self, colour: QColor | None = None) -> None:
        """Recolour the box (title, LCD and dimmed-out state)."""
        if colour:
            self.pcolour = colour
        self.setStyleSheet(
            self.css.format(
                self.pcolour.red(),
                self.pcolour.green(),
                self.pcolour.blue(),
                self.title_size,
                self.title_size,
            )
        )

    def paintEvent(self, event: QPaintEvent) -> None:
        super().paintEvent(event)
        if not self.background:
            return
        painter = QPainter(self)
        painter.setOpacity(self.bg_opacity)

        scaled = self.background.scaled(
            max(self.bg_size, min(self.height() // 4, self.width() // 4)),
            max(self.bg_size, min(self.height() // 4, self.width() // 4)),
            QtCore.Qt.AspectRatioMode.KeepAspectRatio,
            QtCore.Qt.TransformationMode.SmoothTransformation,
        )

        painter.drawPixmap(0, 0, scaled)


class CardWidget(QWidget):
    """A small aspect-ratio-preserving playing-card widget."""

    ASPECT_RATIO = 2.5 / 3.5
    MAX_WIDTH = 20
    MAX_HEIGHT = int(MAX_WIDTH / ASPECT_RATIO)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setMaximumSize(self.MAX_WIDTH, self.MAX_HEIGHT)
        self.reset()

    def sizeHint(self) -> QSize:
        return QSize(self.MAX_WIDTH, self.MAX_HEIGHT)

    def minimumSizeHint(self) -> QSize:
        return QSize(20, int(20 / self.ASPECT_RATIO))

    def hasHeightForWidth(self) -> bool:
        return True

    def heightForWidth(self, width: int) -> int:
        return int(width / self.ASPECT_RATIO)

    def paintEvent(self, event: QPaintEvent) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Scale everything according to the current card width.
        corner_radius = self.width() * 0.20
        font_size = self.width() * 0.90

        # Card
        painter.setBrush(self._colour)
        painter.setPen(QtCore.Qt.GlobalColor.black)
        painter.drawRoundedRect(self.rect(), corner_radius, corner_radius)

        # Character
        if self._character:
            from PySide6.QtGui import QFont

            font = QFont("Arial")
            font.setPixelSize(int(font_size))
            font.setBold(True)
            painter.setFont(font)
            painter.setPen(QtCore.Qt.GlobalColor.black)

            painter.drawText(
                self.rect(), QtCore.Qt.AlignmentFlag.AlignCenter, self._character
            )

    def getColour(self) -> QColor:
        return self._colour

    def setColour(self, colour: QColor | str) -> None:
        if isinstance(colour, str):
            self._colour = QColor(colour)
        else:
            self._colour = colour
        self.update()

    def getChar(self) -> str:
        return self._character

    def setChar(self, character: str) -> None:
        self._character = character
        self.update()

    def reset(self, colour: QColor | None = None, char: str | None = None) -> None:
        """Reset the card's colour and character (both default to blank)."""
        self._colour = colour if colour else QColor("grey")
        self._character = str(char) if char else ""
        self.update()


class IconLabel(QLabel):
    """A label whose enabled/disabled state is fixed (ignores toggling)."""

    def setDisabled(self, b: bool) -> None:
        pass

    def setEnabled(self, b: bool) -> None:
        pass


__all__ = ["GamePlayerWidget", "CardWidget", "IconLabel", "PlayerColours"]
