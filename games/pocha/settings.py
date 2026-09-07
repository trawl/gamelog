"""Default settings for Pocha (deck suit type)."""

from PySide6.QtCore import QCoreApplication

# Strings registered for lupdate extraction:
QCoreApplication.translate("PochaSettings", "Deck type")
QCoreApplication.translate("PochaSettings", "Card suit style for new games")
QCoreApplication.translate("PochaSettings", "spanish")
QCoreApplication.translate("PochaSettings", "french")

game_settings = {
    "pocha_suit_type": {
        "value": "spanish",
        "type": "str",
        "choices": ["spanish", "french"],
        "displayname": "Deck type",
        "description": "Card suit style for new games",
        "context": "PochaSettings",
    },
}
