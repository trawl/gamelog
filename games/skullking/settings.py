"""Default settings for Skull King (scoring and round mode)."""

from PySide6.QtCore import QCoreApplication

# Strings registered for lupdate extraction:
QCoreApplication.translate("SkullKingSettings", "Scoring mode")
QCoreApplication.translate("SkullKingSettings", "Default scoring rules for new games")
QCoreApplication.translate("SkullKingSettings", "classic_scoring")
QCoreApplication.translate("SkullKingSettings", "standard_scoring")
QCoreApplication.translate("SkullKingSettings", "rascal_scoring")
QCoreApplication.translate("SkullKingSettings", "Round mode")
QCoreApplication.translate(
    "SkullKingSettings", "Default card-count sequence for new games"
)
QCoreApplication.translate("SkullKingSettings", "standard_rounds")
QCoreApplication.translate("SkullKingSettings", "even")
QCoreApplication.translate("SkullKingSettings", "brawl")
QCoreApplication.translate("SkullKingSettings", "skirmish")
QCoreApplication.translate("SkullKingSettings", "barrage")
QCoreApplication.translate("SkullKingSettings", "whirlpool")

game_settings = {
    "skullking_scoring_mode": {
        "value": "classic_scoring",
        "type": "str",
        "choices": ["classic_scoring", "standard_scoring", "rascal_scoring"],
        "displayname": "Scoring mode",
        "description": "Default scoring rules for new games",
        "context": "SkullKingSettings",
    },
    "skullking_round_mode": {
        "value": "standard_rounds",
        "type": "str",
        "choices": [
            "standard_rounds",
            "even",
            "brawl",
            "skirmish",
            "barrage",
            "whirlpool",
        ],
        "displayname": "Round mode",
        "description": "Default card-count sequence for new games",
        "context": "SkullKingSettings",
    },
}
