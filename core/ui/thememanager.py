"""Light/dark/system theme handling and stylesheet application."""

from __future__ import annotations

import logging
from enum import StrEnum
from typing import cast

from PySide6.QtCore import QFile, QObject, Qt, QTextStream, Signal
from PySide6.QtGui import QGuiApplication
from PySide6.QtWidgets import QApplication

from core.engine.settings import appsettings

logger = logging.getLogger(__name__)


class Theme(StrEnum):
    """The three selectable themes; SYSTEM follows the OS colour scheme."""

    SYSTEM = "system"
    LIGHT = "light"
    DARK = "dark"


class ThemeManager(QObject):
    """Applies the active theme's stylesheet and reacts to OS scheme changes."""

    themeChanged = Signal(str)

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)

        self._theme = Theme.SYSTEM
        saved_theme = appsettings["theme"]
        if saved_theme:
            self.set_theme(saved_theme)

        QGuiApplication.styleHints().colorSchemeChanged.connect(
            self._system_theme_changed
        )

    @property
    def theme(self) -> Theme:
        return self._theme

    def effective_theme(self) -> Theme:
        """Return the concrete theme in force, resolving SYSTEM to light/dark."""
        if self._theme != Theme.SYSTEM:
            return self._theme
        return self.system_theme

    @property
    def system_theme(self) -> Theme:
        scheme = QGuiApplication.styleHints().colorScheme()

        if scheme == Qt.ColorScheme.Dark:
            return Theme.DARK

        return Theme.LIGHT

    def set_theme(self, theme: Theme | str) -> None:
        """Switch to ``theme``, update the OS colour scheme and restyle."""
        logger.debug("Setting theme to %s", theme)
        theme = Theme(theme)

        if theme == self._theme:
            self._apply_stylesheet(theme)
            return

        self._theme = theme

        style_hints = QGuiApplication.styleHints()

        if theme == Theme.SYSTEM:
            style_hints.unsetColorScheme()
            effective_theme = self.system_theme
        elif theme == Theme.LIGHT:
            style_hints.setColorScheme(Qt.ColorScheme.Light)
            effective_theme = Theme.LIGHT
        else:
            style_hints.setColorScheme(Qt.ColorScheme.Dark)
            effective_theme = Theme.DARK

        self._apply_stylesheet(effective_theme)
        self.themeChanged.emit(theme)

    def _apply_stylesheet(self, theme: Theme) -> None:
        """Load and install the QSS stylesheet for the current system theme."""
        file = QFile(f":/styles/{self.system_theme}.qss")
        if file.open(QFile.OpenModeFlag.ReadOnly | QFile.OpenModeFlag.Text):
            stylesheet = QTextStream(file)
            cast(QApplication, QApplication.instance()).setStyleSheet(
                stylesheet.readAll()
            )
        else:
            logger.warning("Could not load :/styles/%s.qss", self.system_theme)

    def _system_theme_changed(
        self,
        scheme: Qt.ColorScheme,
    ) -> None:
        """Restyle when the OS scheme changes, but only in SYSTEM mode."""
        logger.debug("System theme changed")
        # Only propagate the change when following the system.
        if self._theme == Theme.SYSTEM:
            QGuiApplication.styleHints().unsetColorScheme()
            self._apply_stylesheet(Theme.SYSTEM)
            self.themeChanged.emit(self._theme)
