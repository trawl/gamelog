from core.registry import GameDefinition, registry

registry.register(GameDefinition(
    "Skull King", 8, "Skull King card game", "Home rules",
    "games.skullking.model:SkullKingMatch", "games.skullking.engine:SkullKingEngine",
    "games.skullking.widget:SkullKingWidget", "games.skullking.widget:SkullKingQSTW",
    "games.skullking.engine:SkullKingStatsEngine",
    "games.skullking.engine:SkullKingParticularStatsEngine",
))
