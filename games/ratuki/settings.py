"""Default settings for Ratuki (target score and dealer policy)."""

from PySide6.QtCore import QCoreApplication

# Strings registered for lupdate extraction:
QCoreApplication.translate("RatukiSettings", "Dealer policy")
QCoreApplication.translate("RatukiSettings", "Who deals at the start of each round")
QCoreApplication.translate("RatukiSettings", "Next player deals")
QCoreApplication.translate("RatukiSettings", "Winner deals")
QCoreApplication.translate("RatukiSettings", "Target score")
QCoreApplication.translate("RatukiSettings", "Score a player must reach to end the game")

game_settings = {
    "ratuki_dealer_policy": {
        "value": True,
        "type": "bool",
        "choices": ["Next player deals", "Winner deals"],
        "displayname": "Dealer policy",
        "description": "Who deals at the start of each round",
        "context": "RatukiSettings",
    },
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
