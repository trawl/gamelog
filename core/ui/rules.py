"""Non-modal viewer for a game's bundled quick-reference rules."""

from __future__ import annotations

import logging

from PySide6.QtCore import QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import (
    QApplication,
    QDialog,
    QHBoxLayout,
    QLineEdit,
    QPushButton,
    QTextBrowser,
    QVBoxLayout,
    QWidget,
)

from core.registry import GameDefinition
from core.rules import load_rules

logger = logging.getLogger(__name__)


def current_locale() -> str | None:
    """Locale of the running app's language manager, if there is one."""
    app = QApplication.instance()
    manager = getattr(app, "languageManager", None)
    return manager.getCurrentLocale() if manager is not None else None


class RulesDialog(QDialog):
    """Searchable rules sheet with a link to the official rule book."""

    def __init__(self, definition: GameDefinition, parent: QWidget | None = None):
        super().__init__(parent)
        self.definition = definition
        self.resize(800, 600)

        layout = QVBoxLayout(self)
        bar = QHBoxLayout()
        layout.addLayout(bar)
        self.searchEdit = QLineEdit(self)
        self.searchEdit.setClearButtonEnabled(True)
        self.searchEdit.textChanged.connect(self.search)
        self.searchEdit.returnPressed.connect(self.findNext)
        bar.addWidget(self.searchEdit)
        self.officialButton = QPushButton(self)
        self.officialButton.clicked.connect(self.openOfficial)
        self.officialButton.setVisible(bool(definition.rules_url))
        bar.addWidget(self.officialButton)

        self.browser = QTextBrowser(self)
        # Links in the sheets open in the system browser.
        self.browser.setOpenExternalLinks(True)
        layout.addWidget(self.browser)
        self.retranslateUI()

    def retranslateUI(self) -> None:
        """Reload the sheet for the current language and refresh the labels."""
        self.setWindowTitle(self.tr("{} — Rules").format(self.definition.name))
        self.searchEdit.setPlaceholderText(self.tr("Search..."))
        self.officialButton.setText(self.tr("Official rule book"))
        text = (
            load_rules(self.definition.rules_doc, current_locale())
            if self.definition.rules_doc
            else None
        )
        if text is None:
            text = self.tr("No rules available for this game.")
            self.browser.setPlainText(text)
        else:
            self.browser.setMarkdown(text)

    def search(self, text: str) -> None:
        """Highlight the first match from the top of the document."""
        self.browser.moveCursor(self.browser.textCursor().MoveOperation.Start)
        if text:
            self.browser.find(text)

    def findNext(self) -> None:
        """Jump to the next match, wrapping to the start at the end."""
        text = self.searchEdit.text()
        if text and not self.browser.find(text):
            self.search(text)

    def openOfficial(self) -> None:
        if self.definition.rules_url:
            QDesktopServices.openUrl(QUrl(self.definition.rules_url))
