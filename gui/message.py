#!/usr/bin/env python
# -*- coding: utf-8 -*-

from PySide6.QtWidgets import QMessageBox


class ErrorMessage(QMessageBox):
    def __init__(self, message: str, title: str = "Error", parent=None) -> None:
        super().__init__(parent)
        self.setText(message)
        self.setWindowTitle(title)
        self.setStandardButtons(QMessageBox.StandardButton.Ok)
        self.setDefaultButton(QMessageBox.StandardButton.Ok)
