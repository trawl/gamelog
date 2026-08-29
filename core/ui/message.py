"""Reusable error message box."""

from __future__ import annotations

from PySide6.QtWidgets import QMessageBox, QWidget


class ErrorMessage(QMessageBox):
    """Pre-configured modal error dialog with a single OK button."""

    def __init__(
        self, message: str, title: str = "Error", parent: QWidget | None = None
    ) -> None:
        super().__init__(parent)
        self.setText(message)
        self.setWindowTitle(title)
        self.setStandardButtons(QMessageBox.StandardButton.Ok)
        self.setDefaultButton(QMessageBox.StandardButton.Ok)
