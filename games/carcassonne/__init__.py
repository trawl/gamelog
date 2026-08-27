from core.registry import GameDefinition, registry

registry.register(GameDefinition(
    "Carcassonne", 6, "Carcassonne board game", "Home rules",
    "games.carcassonne.model:CarcassonneMatch",
    "games.carcassonne.engine:CarcassonneEngine", "games.carcassonne.widget:CarcassonneWidget",
    "games.carcassonne.widget:CarcassonneQSTW",
    "games.carcassonne.engine:CarcassonneStatsEngine",
    "games.carcassonne.engine:CarcassonneParticularStatsEngine",
))
