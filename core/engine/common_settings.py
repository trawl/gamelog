"""Reusable setting templates shared across multiple games.

Each template is a plain dict ready to be used as a value in a game's
``game_settings`` dict.  All strings use the ``"GameSettings"`` translation
context, so they only need to be translated once regardless of how many games
share them.
"""

from PySide6.QtCore import QCoreApplication

# Strings registered for lupdate extraction:
QCoreApplication.translate("GameSettings", "Dealer policy")
QCoreApplication.translate("GameSettings", "Who deals at the start of each round")
QCoreApplication.translate("GameSettings", "Next player deals")
QCoreApplication.translate("GameSettings", "Winner deals")
QCoreApplication.translate("GameSettings", "Turn time (s)")
QCoreApplication.translate("GameSettings", "Per-turn countdown duration in seconds")

DEALER_POLICY_SETTING: dict = {
    "value": True,
    "type": "bool",
    "choices": ["Next player deals", "Winner deals"],
    "displayname": "Dealer policy",
    "description": "Who deals at the start of each round",
    "context": "GameSettings",
}

TURN_TIME_SETTING: dict = {
    "value": 120,
    "type": "int",
    "min": 10,
    "max": 600,
    "displayname": "Turn time (s)",
    "description": "Per-turn countdown duration in seconds",
    "context": "GameSettings",
}
