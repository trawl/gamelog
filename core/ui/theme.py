"""Light/dark/system theme handling and stylesheet application."""

from __future__ import annotations

import logging
import sys
from enum import StrEnum
from typing import cast

from PySide6.QtCore import QFile, QObject, Qt, QTextStream, Signal
from PySide6.QtGui import QColor, QGuiApplication, QPalette
from PySide6.QtWidgets import QApplication

from core.engine.settings import appsettings
from core.platform_info import is_android

logger = logging.getLogger(__name__)

# Windows draws QGroupBox frames with the native style, which runs a plain
# line through the title. Drawing the frame ourselves gives it a title gap on
# every platform; this is appended on Windows only so macOS and Linux are
# untouched. palette() keeps the colours in step with the active theme.
# margin-top reserves room for the title (up to the 28px game-player titles)
# so the frame does not run through it.
WINDOWS_GROUPBOX_CSS = """
QGroupBox {
    border: 1px solid palette(mid);
    border-radius: 6px;
    margin-top: 36px;
}

QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top center;
    padding: 0 4px;
    background-color: palette(window);
}
"""


def android_palette(theme: Theme) -> QPalette:
    """Explicit light/dark palette for Android.

    Qt's Android platform theme hands widgets a palette taken from the Android
    system theme, which neither follows ``setColorScheme`` nor the app's own
    theme choice, leaving some widgets light and others dark. Desktop
    platforms resolve the colour scheme themselves and are left alone.
    """
    dark = theme == Theme.DARK
    role = QPalette.ColorRole
    group = QPalette.ColorGroup
    colours = {
        role.Window: "#353535" if dark else "#efefef",
        role.WindowText: "#ffffff" if dark else "#000000",
        role.Base: "#252525" if dark else "#ffffff",
        role.AlternateBase: "#353535" if dark else "#f7f7f7",
        role.ToolTipBase: "#252525" if dark else "#ffffdc",
        role.ToolTipText: "#ffffff" if dark else "#000000",
        role.Text: "#ffffff" if dark else "#000000",
        role.Button: "#353535" if dark else "#efefef",
        role.ButtonText: "#ffffff" if dark else "#000000",
        role.BrightText: "#ff5555" if dark else "#ff0000",
        role.Link: "#6fa8dc" if dark else "#0645ad",
        role.Highlight: "#2a82da" if dark else "#308cc6",
        role.HighlightedText: "#ffffff",
        role.PlaceholderText: "#a0a0a0" if dark else "#707070",
    }
    palette = QPalette()
    for colour_role, value in colours.items():
        palette.setColor(colour_role, QColor(value))
    disabled = QColor("#808080")
    for colour_role in (role.WindowText, role.Text, role.ButtonText):
        palette.setColor(group.Disabled, colour_role, disabled)
    return palette


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
        """Install the QSS stylesheet (and, on Android, palette) for ``theme``."""
        # Resolve the theme being applied rather than asking Qt for the
        # scheme: where the OS ignores setColorScheme (Android) that would
        # still report the system's, not the one the user picked.
        effective = self.system_theme if theme == Theme.SYSTEM else theme
        app = cast(QApplication, QApplication.instance())
        if is_android():
            app.setPalette(android_palette(effective))
        file = QFile(f":/styles/{effective}.qss")
        if file.open(QFile.OpenModeFlag.ReadOnly | QFile.OpenModeFlag.Text):
            stylesheet = QTextStream(file).readAll()
            if sys.platform == "win32":
                stylesheet += WINDOWS_GROUPBOX_CSS
            app.setStyleSheet(stylesheet)
        else:
            logger.warning("Could not load :/styles/%s.qss", effective)

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
