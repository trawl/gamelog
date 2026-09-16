"""Reusable dialog widgets."""

from __future__ import annotations

import sys

from PySide6 import QtCore, QtGui
from PySide6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QVBoxLayout,
    QWidget,
)

from core._version import __version__


class AboutDialog(QDialog):
    """Simple 'About Gamelog' dialog showing the app icon and credits."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle(self.tr("About Gamelog"))
        self.widgetlayout = QHBoxLayout(self)
        self.iconlabel = QLabel(self)
        self.iconlabel.setMaximumSize(75, 75)
        self.iconlabel.setScaledContents(True)
        self.iconlabel.setPixmap(QtGui.QPixmap(":/icons/cards.png"))
        self.widgetlayout.addWidget(self.iconlabel)
        self.contentlayout = QVBoxLayout()
        self.widgetlayout.addLayout(self.contentlayout)
        self.title = QLabel(f"Gamelog {__version__}")
        self.title.setStyleSheet("QLabel{font-size:18px; font-weight:bold}")
        self.title.setAlignment(QtCore.Qt.AlignmentFlag.AlignLeft)
        self.contentlayout.addWidget(self.title)
        self.content = QLabel(
            self.tr("Gamelog is a utility to keep track of the score in board games.")
        )
        self.content.setWordWrap(True)
        self.content.setAlignment(QtCore.Qt.AlignmentFlag.AlignTop)
        self.contentlayout.addWidget(self.content)
        py_version = sys.version.split()[0]
        self.content = QLabel(f"Qt {QtCore.qVersion()}  •  Python {py_version}")
        self.content.setWordWrap(True)
        self.content.setAlignment(QtCore.Qt.AlignmentFlag.AlignLeft)
        self.contentlayout.addWidget(self.content)
        self.content = QLabel("Xavi Abellan 2012")
        self.content.setWordWrap(True)
        self.content.setAlignment(QtCore.Qt.AlignmentFlag.AlignLeft)
        self.contentlayout.addWidget(self.content)


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
