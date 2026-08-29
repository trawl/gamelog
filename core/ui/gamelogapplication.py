"""QApplication subclass wiring in managers and a global error handler."""

from __future__ import annotations

import sys
import traceback
from typing import TYPE_CHECKING

from PySide6.QtWidgets import QApplication, QMessageBox

from core.ui.languagechooser import LanguageManager
from core.ui.thememanager import ThemeManager

if TYPE_CHECKING:
    from types import TracebackType


class GamelogApplication(QApplication):
    """Application object owning the language/theme managers and excepthook."""

    languageManager: LanguageManager
    themeManager: ThemeManager

    def __init__(self, *args: list[str]) -> None:
        super().__init__(*args)
        # Surface uncaught errors (e.g. database failures raised by the
        # persistence layer) instead of letting the process die silently.
        sys.excepthook = self._handleUncaughtException

    def _handleUncaughtException(
        self,
        exc_type: type[BaseException],
        exc_value: BaseException,
        exc_tb: TracebackType | None,
    ) -> None:
        """Log an uncaught exception and show it in a modal error box."""
        if issubclass(exc_type, KeyboardInterrupt):
            sys.__excepthook__(exc_type, exc_value, exc_tb)
            return
        # Always log the full traceback to the real stderr (which may have been
        # redirected away under pythonw).
        traceback.print_exception(exc_type, exc_value, exc_tb, file=sys.__stderr__)
        try:
            QMessageBox.critical(
                self.activeWindow(),
                self.tr("Gamelog error"),
                str(exc_value) or exc_type.__name__,
            )
        except Exception:  # noqa: BLE001 S110
            # Never let the error handler raise on its own account.
            pass
