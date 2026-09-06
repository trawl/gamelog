"""Default settings for Scrabble (per-turn countdown)."""

from PySide6.QtCore import QCoreApplication

# Strings registered for lupdate extraction:
QCoreApplication.translate("ScrabbleSettings", "Turn time (s)")
QCoreApplication.translate("ScrabbleSettings", "Per-turn countdown duration in seconds")

game_settings = {
    "scrabble_turn_time": {
        "value": 120,
        "type": "int",
        "min": 10,
        "max": 600,
        "displayname": "Turn time (s)",
        "description": "Per-turn countdown duration in seconds",
        "context": "ScrabbleSettings",
    },
}
