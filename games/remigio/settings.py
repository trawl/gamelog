"""Default settings for Remigio (elimination score and dealer policy)."""

from PySide6.QtCore import QCoreApplication

# Strings registered for lupdate extraction:
QCoreApplication.translate("RemigioSettings", "Dealer policy")
QCoreApplication.translate("RemigioSettings", "Who deals at the start of each round")
QCoreApplication.translate("RemigioSettings", "Next player deals")
QCoreApplication.translate("RemigioSettings", "Winner deals")
QCoreApplication.translate("RemigioSettings", "Elimination score")
QCoreApplication.translate("RemigioSettings", "Score at which a player is eliminated from the game")

game_settings = {
    "remigio_dealer_policy": {
        "value": True,
        "type": "bool",
        "choices": ["Next player deals", "Winner deals"],
        "displayname": "Dealer policy",
        "description": "Who deals at the start of each round",
        "context": "RemigioSettings",
    },
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
