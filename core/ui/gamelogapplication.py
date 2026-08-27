from PySide6.QtWidgets import QApplication

from core.ui.languagechooser import LanguageManager
from core.ui.thememanager import ThemeManager


class GamelogApplication(QApplication):
    languageManager: LanguageManager
    themeManager: ThemeManager
