from core.registry import GameDefinition, registry

registry.register(GameDefinition(
    "Skull King", 8, "Skull King card game", "Home rules",
    "model.skullking:SkullKingMatch", "controllers.skullkingengine:SkullKingEngine",
    "gui.skullking:SkullKingWidget", "gui.skullking:SkullKingQSTW",
    "controllers.skullkingengine:SkullKingStatsEngine",
    "controllers.skullkingengine:SkullKingParticularStatsEngine",
))
