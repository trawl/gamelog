"""Dialog for creating a new player record."""

from __future__ import annotations

from PySide6 import QtCore
from PySide6.QtWidgets import (
    QDialog,
    QGridLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from core.engine.db import db


class NewPlayerDialog(QDialog):
    """Modal dialog to register a new player, guarding against duplicates."""

    addedNewPlayer = QtCore.Signal(str)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.initUI()
        self.setWindowTitle(self.tr("New Player"))
        self.existingplayers = [str(nick).lower() for nick in db.getPlayerNicks()]

    def initUI(self) -> None:
        """Build the nick/name fields, warning label and Create button."""
        self.vlayout = QVBoxLayout(self)
        self.glayout = QGridLayout()
        self.vlayout.addLayout(self.glayout)
        self.nicklabel = QLabel(self)
        self.nicklabel.setText(self.tr("Nick"))
        self.glayout.addWidget(self.nicklabel, 0, 0)
        self.nicklineedit = QLineEdit(self)
        self.nicklineedit.textChanged.connect(self.checkExisting)
        self.glayout.addWidget(self.nicklineedit, 0, 1)
        self.namelabel = QLabel(self)
        self.namelabel.setText(self.tr("Name"))
        self.glayout.addWidget(self.namelabel, 1, 0)
        self.namelineedit = QLineEdit(self)
        self.namelineedit.textChanged.connect(self.checkExisting)
        self.glayout.addWidget(self.namelineedit, 1, 1)
        self.existinglabel = QLabel()
        self.existinglabel.setStyleSheet("QLabel {color: red; }")
        self.vlayout.addWidget(self.existinglabel)
        self.createbutton = QPushButton(self)
        self.createbutton.setText(self.tr("Create"))
        self.createbutton.setDisabled(True)
        self.createbutton.clicked.connect(self.createAction)
        self.vlayout.addWidget(self.createbutton)
        self.show()

    def checkExisting(self, _discard: str) -> None:
        """Validate the nick and toggle the Create button accordingly."""
        tempnick = str(self.nicklineedit.text())
        if len(tempnick) < 3:
            self.existinglabel.setText("")
            self.createbutton.setDisabled(True)
            return
        if tempnick.lower() in self.existingplayers:
            self.existinglabel.setText(self.tr("Player already exists!"))
            self.createbutton.setDisabled(True)
        else:
            self.existinglabel.setText("")
            self.createbutton.setEnabled(len(self.namelineedit.text()) > 0)

    def createAction(self) -> None:
        """Persist the new player, emit the signal and accept the dialog."""
        nick = str(self.nicklineedit.text())
        db.addPlayer(nick, str(self.namelineedit.text()))
        self.existingplayers.append(nick)
        self.addedNewPlayer.emit(nick)
        self.accept()
