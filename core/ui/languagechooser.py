"""Runtime language switching: translator management and locale pickers."""

from __future__ import annotations

import logging
from typing import ClassVar

from PySide6 import QtCore
from PySide6.QtCore import (
    QCoreApplication,
    QDir,
    QLocale,
    QObject,
    QSize,
    QTranslator,
    Signal,
)
from PySide6.QtGui import QIcon, QResizeEvent
from PySide6.QtWidgets import (
    QApplication,
    QDialog,
    QDialogButtonBox,
    QGroupBox,
    QListWidget,
    QListWidgetItem,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from core.engine.settings import appsettings

logger = logging.getLogger(__name__)


class LanguageManager(QObject):
    """Loads Qt/app translation catalogues and tracks the current locale."""

    languageChanged = Signal(QLocale)

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)
        # Default to system language, fallback to English if not available
        self.translators: list[QTranslator] = []
        default_locale = appsettings["language"]
        self.current_locale = (
            default_locale
            if default_locale and default_locale != "system"
            else QLocale.system().name()
        )

        self.loadTranslator(self.current_locale)

    def loadTranslator(self, lang: str) -> None:
        """Install Qt and application catalogues for ``lang`` if available."""
        if lang.lower() == "system":
            lang = QLocale.system().name()
        if lang == "C":
            lang = "en_GB"

        new_translators: list[QTranslator] = []

        # Qt's own base catalogue is keyed by language root (e.g. "en").
        qt_translator = QTranslator()
        if qt_translator.load("qtbase_" + lang.split("_")[0], ":i18n/"):
            new_translators.append(qt_translator)

        # Application catalogues: core + one per game, auto-discovered from the
        # bundle. A game contributes its translations simply by shipping a
        # ``<game>_<locale>.qm`` — no change needed here.
        loaded_app = False
        for name in QDir(":/i18n").entryList([f"*_{lang}.qm"], QDir.Filter.Files):
            translator = QTranslator()
            if translator.load(name, ":i18n/"):
                new_translators.append(translator)
                loaded_app = True

        if not loaded_app:
            # Unknown/unavailable locale: keep the current language.
            return

        for translator in self.translators:
            QCoreApplication.removeTranslator(translator)
        self.translators = new_translators
        for translator in self.translators:
            QCoreApplication.installTranslator(translator)
        self.current_locale = lang
        self.languageChanged.emit(QLocale(lang))

    def getCurrentLocale(self) -> str:
        return self.current_locale


class LanguageButton(QToolButton):
    """Toolbar button that cycles through the supported languages on click."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        # self.setToolTip(self.tr("Change Language"))
        # self.setPopupMode(QToolButton.ToolButtonPopupMode.MenuButtonPopup)
        app = QApplication.instance()
        if app:
            self.lm = app.languageManager  # pyright: ignore[reportAttributeAccessIssue]
        else:
            self.lm = LanguageManager()
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
        self.changeLanguage()

    def showLanguageChooser(self) -> None:
        """Open the modal language-selection dialog."""
        self.languageChooser.exec()

    def nextLanguage(self) -> None:
        """Switch to the next supported locale, wrapping around."""
        locales = [
            data["locale"] for data in LanguageChooser.supportedLanguages.values()
        ]
        try:
            current_index = locales.index(self.lm.getCurrentLocale())
            next_index = (current_index + 1) % len(locales)
        except ValueError:
            next_index = 0
        next_locale = locales[next_index]
        self.changeLanguage(next_locale)

    def refresh(self) -> None:
        """Update the button icon to match the current locale."""
        locale = self.lm.getCurrentLocale()
        logger.debug("Refreshing language button for %s", locale)
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
        self.setIcon(QIcon(f":/icons/{icon}"))

    def changeLanguage(self, locale: str | None = None) -> None:
        """Load ``locale`` (or the current one) and refresh the button icon."""
        if not locale:
            locale = self.lm.getCurrentLocale()
        if locale == "C":
            locale = "en_GB"
        if locale != self.lm.getCurrentLocale():
            logger.debug(
                "Changing language from %s to %s",
                self.lm.getCurrentLocale(),
                locale,
            )
            self.lm.loadTranslator(locale)
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
        self.setIcon(QIcon(f":/icons/{icon}"))

    def resizeEvent(self, event: QResizeEvent) -> None:
        super().resizeEvent(event)
        size = int(min(self.width(), self.height()) * 0.9)
        self.setIconSize(QSize(size, size))


class LanguageChooser(QDialog):
    """Modal dialog listing the supported languages for the user to pick."""

    newQM = QtCore.Signal(str)
    supportedLanguages: ClassVar[dict] = {
        "English": {"locale": "en_GB", "icon": "english.svg"},
        "Español": {"locale": "es_ES", "icon": "spanish.svg"},
        "Català": {"locale": "ca_ES", "icon": "catalan.svg"},
    }

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.initUI()

    def initUI(self) -> None:
        """Build the language list and OK/Cancel button box."""
        self.setWindowTitle(self.tr("Language"))
        self.widgetLayout = QVBoxLayout(self)
        self.langGroupBox = QGroupBox(self)
        self.langGroupBox.setTitle(self.tr("Select the desired language:"))
        self.widgetLayout.addWidget(self.langGroupBox)
        self.langGroupBoxLayout = QVBoxLayout(self.langGroupBox)
        self.languageListWidget = QListWidget(self.langGroupBox)
        self.langGroupBoxLayout.addWidget(self.languageListWidget)
        for language in self.supportedLanguages:
            item = QListWidgetItem(
                QIcon(f":/icons/{self.supportedLanguages[language]['icon']}"), language
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

    def changeLanguage(self) -> None:
        """Emit the selected locale's catalogue name and close the dialog."""
        ci = self.languageListWidget.currentItem()
        if ci:
            selected = ci.text()
            fname = self.supportedLanguages[selected]["locale"]
            self.newQM.emit(fname)
        self.close()
