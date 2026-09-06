"""Default settings for Qwirkle (per-turn countdown and dealer policy)."""

from PySide6.QtCore import QCoreApplication

# Strings registered for lupdate extraction:
QCoreApplication.translate("QwirkleSettings", "Turn time (s)")
QCoreApplication.translate("QwirkleSettings", "Per-turn countdown duration in seconds")
QCoreApplication.translate("QwirkleSettings", "Dealer policy")
QCoreApplication.translate("QwirkleSettings", "Who deals at the start of each round")
QCoreApplication.translate("QwirkleSettings", "Next player deals")
QCoreApplication.translate("QwirkleSettings", "Winner deals")

game_settings = {
    "qwirkle_turn_time": {
        "value": 120,
        "type": "int",
        "min": 10,
        "max": 600,
        "displayname": "Turn time (s)",
        "description": "Per-turn countdown duration in seconds",
        "context": "QwirkleSettings",
    },
}
