from PySide6.QtWidgets import QApplication

from gui.languagechooser import LanguageManager
from gui.thememanager import ThemeManager


class GamelogApplication(QApplication):
    languageManager: LanguageManager
    themeManager: ThemeManager
