"""Default settings for Remigio (elimination score and dealer policy)."""

from PySide6.QtCore import QCoreApplication

from core.engine.common_settings import DEALER_POLICY_SETTING

# Strings registered for lupdate extraction:
QCoreApplication.translate("RemigioSettings", "Elimination score")
QCoreApplication.translate(
    "RemigioSettings", "Score at which a player is eliminated from the game"
)

game_settings = {
    "remigio_dealer_policy": DEALER_POLICY_SETTING,
    "remigio_top_score": {
        "value": 100,
        "type": "int",
        "min": 1,
        "max": 1000,
        "displayname": "Elimination score",
        "description": "Score at which a player is eliminated from the game",
        "context": "RemigioSettings",
    },
}
