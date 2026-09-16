"""Colour-picker popup for reassigning player colours."""

from __future__ import annotations

from PySide6 import QtCore, QtGui
from PySide6.QtWidgets import QDialog, QHBoxLayout, QPushButton, QWidget


class _ColourPickerDialog(QDialog):
    """Small popup showing all available colours as clickable swatches."""

    def __init__(
        self,
        colours: list[QtGui.QColor],
        colour_map: dict[str, int],
        player: str,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle(self.tr("Choose colour"))
        self._chosen: int | None = None
        layout = QHBoxLayout(self)
        current_idx = colour_map.get(player, 0)
        taken = {idx for p, idx in colour_map.items() if p != player}
        for i, colour in enumerate(colours):
            btn = QPushButton(self)
            btn.setFixedSize(36, 36)
            pixmap = QtGui.QPixmap(28, 28)
            pixmap.fill(colour)
            btn.setIcon(QtGui.QIcon(pixmap))
            btn.setIconSize(QtCore.QSize(28, 28))
            if i == current_idx:
                btn.setStyleSheet("border: 3px solid white;")
            elif i in taken:
                btn.setStyleSheet("border: 1px solid gray;")
            btn.clicked.connect(lambda checked=False, idx=i: self._select(idx))
            layout.addWidget(btn)

    def _select(self, idx: int) -> None:
        self._chosen = idx
        self.accept()

    def chosenIndex(self) -> int:
        return self._chosen if self._chosen is not None else 0


__all__ = ["_ColourPickerDialog"]
