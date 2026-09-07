"""Default settings for Phase 10 and Phase 10 Master (phase order and dealer policy)."""

from PySide6.QtCore import QCoreApplication

from core.engine.common_settings import DEALER_POLICY_SETTING

# Strings registered for lupdate extraction:
QCoreApplication.translate("Phase10Settings", "Phase order")
QCoreApplication.translate(
    "Phase10Settings", "Whether players must complete phases in the fixed sequence"
)
QCoreApplication.translate("Phase10Settings", "Free phase order")
QCoreApplication.translate("Phase10Settings", "Phases in order")

game_settings = {
    "phase10_dealer_policy": DEALER_POLICY_SETTING,
    "phase10_phases_in_order": {
        "value": False,
        "type": "bool",
        "choices": ["Free phase order", "Phases in order"],
        "displayname": "Phase order",
        "description": "Whether players must complete phases in the fixed sequence",
        "context": "Phase10Settings",
    },
}
