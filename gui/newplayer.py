#!/usr/bin/env python
# -*- coding: utf-8 -*-

from PyQt5 import QtCore
from PyQt5.QtWidgets import (QApplication, QDialog, QGridLayout, QLabel,
                             QLineEdit, QPushButton, QVBoxLayout)

from controllers.db import db

i18n = QApplication.translate


class NewPlayerDialog(QDialog):

    addedNewPlayer = QtCore.pyqtSignal(str)

    def __init__(self, parent=None):
        super(NewPlayerDialog, self).__init__(parent)
        self.initUI()
        self.setWindowTitle(i18n(
            "NewPlayerDialog", "New Player"))
        self.existingplayers = [str(nick).lower()
                                for nick in db.getPlayerNicks()]

    def initUI(self):
        self.vlayout = QVBoxLayout(self)
        self.layout = QGridLayout()
        self.vlayout.addLayout(self.layout)
        self.nicklabel = QLabel(self)
        self.nicklabel.setText(
            i18n("NewPlayerDialog", "Nick"))
        self.layout.addWidget(self.nicklabel, 0, 0)
        self.nicklineedit = QLineEdit(self)
        self.nicklineedit.textChanged.connect(self.checkExisting)
        self.layout.addWidget(self.nicklineedit, 0, 1)
        self.namelabel = QLabel(self)
        self.namelabel.setText(
            i18n("NewPlayerDialog", "Name"))
        self.layout.addWidget(self.namelabel, 1, 0)
        self.namelineedit = QLineEdit(self)
        self.namelineedit.textChanged.connect(self.checkExisting)
        self.layout.addWidget(self.namelineedit, 1, 1)
        self.existinglabel = QLabel()
        self.existinglabel.setStyleSheet("QLabel {color: red; }")
        self.vlayout.addWidget(self.existinglabel)
        self.createbutton = QPushButton(self)
        self.createbutton.setText(
            i18n("NewPlayerDialog", "Create"))
        self.createbutton.setDisabled(True)
        self.createbutton.clicked.connect(self.createAction)
        self.vlayout.addWidget(self.createbutton)
        self.show()

    def checkExisting(self, discard):
        tempnick = str(self.nicklineedit.text())
        if len(tempnick) < 3:
            self.existinglabel.setText("")
            self.createbutton.setDisabled(True)
            return
        if tempnick.lower() in self.existingplayers:
            self.existinglabel.setText(i18n(
                "NewPlayerDialog", "Player already exists!"))
            self.createbutton.setDisabled(True)
        else:
            self.existinglabel.setText("")
            self.createbutton.setEnabled(len(self.namelineedit.text()) > 0)

    def createAction(self):
        nick = str(self.nicklineedit.text())
        db.addPlayer(nick, str(self.namelineedit.text()))
        self.existingplayers.append(nick)
        self.addedNewPlayer.emit(nick)
        self.accept()
