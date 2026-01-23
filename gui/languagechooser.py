#!/usr/bin/env python
# -*- coding: utf-8 -*-
from PySide6 import QtCore
from PySide6.QtCore import (
    QCoreApplication,
    QLocale,
    QObject,
    QSize,
    QTranslator,
    Signal,
)
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import (
    QApplication,
    QDialog,
    QDialogButtonBox,
    QGroupBox,
    QListWidget,
    QListWidgetItem,
    QToolButton,
    QVBoxLayout,
)


class LanguageManager(QObject):
    languageChanged = Signal(QLocale)

    def __init__(self, parent=None):
        super(LanguageManager, self).__init__(parent)
        # Default to system language, fallback to English if not available
        self.translator = None
        self.qt_translator = None
        self.current_locale = QLocale.system().name()
        self.loadTranslator(self.current_locale)

    def loadTranslator(self, lang):
        translator = QTranslator()
        ret = translator.load(lang, "i18n/")
        qt_translator = QTranslator()
        qt_qm = "qtbase_" + lang.split("_")[0]
        qt_translator.load(qt_qm, "i18n/")
        if ret:
            if self.translator:
                QCoreApplication.removeTranslator(self.translator)
            if self.qt_translator:
                QCoreApplication.removeTranslator(self.qt_translator)
            self.qt_translator = qt_translator
            self.translator = translator
            self.current_locale = lang
            QCoreApplication.installTranslator(self.qt_translator)
            QCoreApplication.installTranslator(self.translator)
            self.languageChanged.emit(QLocale(lang))

    def getCurrentLocale(self):
        return self.current_locale


class LanguageButton(QToolButton):
    def __init__(self, parent=None):
        super(LanguageButton, self).__init__(parent)
        # self.setToolTip(self.tr("Change Language"))
        # self.setPopupMode(QToolButton.ToolButtonPopupMode.MenuButtonPopup)
        self.languageChooser = LanguageChooser(self)
        self.languageChooser.newQM.connect(self.changeLanguage)
        # self.clicked.connect(self.showLanguageChooser)
        self.clicked.connect(self.nextLanguage)
        self.setMinimumSize(32, 32)
        self.setStyleSheet("""
            QToolButton {
                background: transparent;
                border: none;
                padding: 0px;
            }
        """)
        self.changeLanguage(QLocale.system().name())

    def showLanguageChooser(self):
        self.languageChooser.exec()

    def nextLanguage(self):
        app = QApplication.instance()
        if not app:
            return
        lm = app.languageManager  # pyright: ignore[reportAttributeAccessIssue]
        locales = [
            data["locale"] for data in LanguageChooser.supportedLanguages.values()
        ]
        try:
            current_index = locales.index(lm.getCurrentLocale())
            next_index = (current_index + 1) % len(locales)
        except ValueError:
            next_index = 0
        next_locale = locales[next_index]
        self.changeLanguage(next_locale)

    def changeLanguage(self, locale):
        if locale == "C":
            locale = "en_GB"
        print(f"Changing language to: {locale}")
        app = QApplication.instance()
        if not app:
            return
        lm = app.languageManager  # pyright: ignore[reportAttributeAccessIssue]
        lm.loadTranslator(locale)
        icon = next(
            (
                data["icon"]
                for data in LanguageChooser.supportedLanguages.values()
                if data["locale"] == locale
            ),
            None,
        )
        if not icon:
            icon = "english.svg"
        self.setIcon(QIcon(f"icons/{icon}"))

    def resizeEvent(self, event):
        super().resizeEvent(event)
        size = int(min(self.width(), self.height()) * 0.9)
        self.setIconSize(QSize(size, size))


class LanguageChooser(QDialog):
    newQM = QtCore.Signal(str)
    supportedLanguages = {
        "English": {"locale": "en_GB", "icon": "english.svg"},
        "Español": {"locale": "es_ES", "icon": "spanish.svg"},
        "Català": {"locale": "ca_ES", "icon": "catalan.svg"},
    }

    def __init__(self, parent=None):
        super(LanguageChooser, self).__init__(parent)
        self.initUI()

    def initUI(self):
        self.setWindowTitle(self.tr("Language"))
        self.widgetLayout = QVBoxLayout(self)
        self.langGroupBox = QGroupBox(self)
        self.langGroupBox.setTitle(self.tr("Select the desired language:"))
        self.widgetLayout.addWidget(self.langGroupBox)
        self.langGroupBoxLayout = QVBoxLayout(self.langGroupBox)
        self.languageListWidget = QListWidget(self.langGroupBox)
        self.langGroupBoxLayout.addWidget(self.languageListWidget)
        for language in self.supportedLanguages.keys():
            item = QListWidgetItem(
                QIcon(f"icons/{self.supportedLanguages[language]['icon']}"), language
            )
            self.languageListWidget.addItem(item)

        self.buttonBox = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel,
            QtCore.Qt.Orientation.Horizontal,
            self,
        )
        self.buttonBox.accepted.connect(self.changeLanguage)
        self.buttonBox.rejected.connect(self.close)
        self.widgetLayout.addWidget(self.buttonBox)
        self.adjustSize()
        self.setFixedSize(self.size())

    def changeLanguage(self):
        ci = self.languageListWidget.currentItem()
        if ci:
            selected = ci.text()
            fname = self.supportedLanguages[selected]["locale"]
            self.newQM.emit(fname)
        self.close()
