import sys
import traceback

from PySide6.QtWidgets import QApplication, QMessageBox

from core.ui.languagechooser import LanguageManager
from core.ui.thememanager import ThemeManager


class GamelogApplication(QApplication):
    languageManager: LanguageManager
    themeManager: ThemeManager

    def __init__(self, *args):
        super().__init__(*args)
        # Surface uncaught errors (e.g. database failures raised by the
        # persistence layer) instead of letting the process die silently.
        sys.excepthook = self._handleUncaughtException

    def _handleUncaughtException(self, exc_type, exc_value, exc_tb):
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
