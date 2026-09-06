"""Default settings for Phase 10 and Phase 10 Master (phase order and dealer policy)."""

from PySide6.QtCore import QCoreApplication

# Strings registered for lupdate extraction:
QCoreApplication.translate("Phase10Settings", "Dealer policy")
QCoreApplication.translate("Phase10Settings", "Who deals at the start of each round")
QCoreApplication.translate("Phase10Settings", "Next player deals")
QCoreApplication.translate("Phase10Settings", "Winner deals")
QCoreApplication.translate("Phase10Settings", "Phase order")
QCoreApplication.translate("Phase10Settings", "Whether players must complete phases in the fixed sequence")
QCoreApplication.translate("Phase10Settings", "Free phase order")
QCoreApplication.translate("Phase10Settings", "Phases in order")

game_settings = {
    "phase10_dealer_policy": {
        "value": True,
        "type": "bool",
        "choices": ["Next player deals", "Winner deals"],
        "displayname": "Dealer policy",
        "description": "Who deals at the start of each round",
        "context": "Phase10Settings",
    },
    "phase10_phases_in_order": {
        "value": False,
        "type": "bool",
        "choices": ["Free phase order", "Phases in order"],
        "displayname": "Phase order",
        "description": "Whether players must complete phases in the fixed sequence",
        "context": "Phase10Settings",
    },
}
