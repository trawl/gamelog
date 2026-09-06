"""Default settings for Toma6 (score threshold and dealer policy)."""

from PySide6.QtCore import QCoreApplication

# Strings registered for lupdate extraction:
QCoreApplication.translate("Toma6Settings", "Dealer policy")
QCoreApplication.translate("Toma6Settings", "Who deals at the start of each round")
QCoreApplication.translate("Toma6Settings", "Next player deals")
QCoreApplication.translate("Toma6Settings", "Winner deals")
QCoreApplication.translate("Toma6Settings", "End score")
QCoreApplication.translate(
    "Toma6Settings", "Score any player must reach to trigger the end of the game"
)

game_settings = {
    "toma6_dealer_policy": {
        "value": True,
        "type": "bool",
        "choices": ["Next player deals", "Winner deals"],
        "displayname": "Dealer policy",
        "description": "Who deals at the start of each round",
        "context": "Toma6Settings",
    },
    "toma6_top_score": {
        "value": 66,
        "type": "int",
        "min": 1,
        "max": 1000,
        "displayname": "End score",
        "description": "Score any player must reach to trigger the end of the game",
        "context": "Toma6Settings",
    },
}
