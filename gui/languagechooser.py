#!/usr/bin/env python
# -*- coding: utf-8 -*-
from PySide6 import QtCore
from PySide6.QtWidgets import (
    QApplication,
    QDialog,
    QDialogButtonBox,
    QLabel,
    QListWidget,
    QVBoxLayout,
)

i18n = QApplication.translate


class LanguageChooser(QDialog):
    newQM = QtCore.Signal(str)
    supportedLanguages = {"Español": "es_ES", "English": "en_GB", "Català": "ca_ES"}

    def __init__(self, parent=None):
        super(LanguageChooser, self).__init__(parent)
        self.initUI()

    def initUI(self):
        self.setWindowTitle(i18n("LanguageChooser", "Language"))
        self.widgetLayout = QVBoxLayout(self)
        self.infoLabel = QLabel(self)
        self.infoLabel.setText(i18n("LanguageChooser", "Select the desired language:"))
        self.widgetLayout.addWidget(self.infoLabel)
        self.languageListWidget = QListWidget(self)
        self.widgetLayout.addWidget(self.languageListWidget)
        for language in self.supportedLanguages.keys():
            self.languageListWidget.addItem(language)

        self.buttonBox = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel,
            QtCore.Qt.Orientation.Horizontal,
            self,
        )
        self.buttonBox.accepted.connect(self.changeLanguage)
        self.buttonBox.rejected.connect(self.close)
        self.widgetLayout.addWidget(self.buttonBox)

    def changeLanguage(self):
        ci = self.languageListWidget.currentItem()
        if ci:
            selected = ci.text()
            fname = self.supportedLanguages[selected]
            self.newQM.emit(fname)
        self.close()
