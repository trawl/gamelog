"""Default settings for Catan (victory points needed to win)."""

from PySide6.QtCore import QCoreApplication

# Strings registered for lupdate extraction:
QCoreApplication.translate("CatanSettings", "Victory points")
QCoreApplication.translate(
    "CatanSettings", "Victory points a player must reach to win the game"
)

game_settings = {
    "catan_top_score": {
        "value": 10,
        "type": "int",
        "min": 3,
        "max": 30,
        "displayname": "Victory points",
        "description": "Victory points a player must reach to win the game",
        "context": "CatanSettings",
    },
}
