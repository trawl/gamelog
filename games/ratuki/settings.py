"""Default settings for Ratuki (target score and dealer policy)."""

from PySide6.QtCore import QCoreApplication

from core.engine.common_settings import DEALER_POLICY_SETTING

# Strings registered for lupdate extraction:
QCoreApplication.translate("RatukiSettings", "Target score")
QCoreApplication.translate(
    "RatukiSettings", "Score a player must reach to end the game"
)

game_settings = {
    "ratuki_dealer_policy": DEALER_POLICY_SETTING,
    "ratuki_top_score": {
        "value": 100,
        "type": "int",
        "min": 1,
        "max": 1000,
        "displayname": "Target score",
        "description": "Score a player must reach to end the game",
        "context": "RatukiSettings",
    },
}
