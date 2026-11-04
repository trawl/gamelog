"""Reusable dialog widgets."""

from __future__ import annotations

import subprocess
import sys

from PySide6 import QtCore, QtGui
from PySide6.QtWidgets import (
    QBoxLayout,
    QDialog,
    QDialogButtonBox,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QVBoxLayout,
    QWidget,
)

from core._version import __version__
from core.platform_info import is_android


def add_dismiss_button(
    dialog: QDialog,
    layout: QBoxLayout,
    button: QDialogButtonBox.StandardButton = QDialogButtonBox.StandardButton.Close,
) -> QDialogButtonBox | None:
    """Append a Close/Cancel button that rejects ``dialog``, on Android only.

    Android has no window close button, so a popup without its own way out
    would trap the user. Desktop windows already have one, so nothing is added.
    """
    if not is_android():
        return None
    box = QDialogButtonBox(button, dialog)
    box.rejected.connect(dialog.reject)
    layout.addWidget(box)
    return box


def _git_short_hash() -> str | None:
    if is_android():
        return None
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"],
            stderr=subprocess.DEVNULL,
            text=True,
        ).strip()
    except Exception:
        return None


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
        commit = _git_short_hash()
        version_str = f"Gamelog {__version__}" + (f" ({commit})" if commit else "")
        self.title = QLabel(version_str)
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
        add_dismiss_button(self, self.contentlayout)


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
