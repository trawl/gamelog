from games.registry import GameDefinition, registry

registry.register(GameDefinition(
    "Carcassonne", 6, "Carcassonne board game", "Home rules",
    "model.carcassonne:CarcassonneMatch",
    "controllers.carcassonneengine:CarcassonneEngine", "gui.carcassonne:CarcassonneWidget",
    "gui.carcassonne:CarcassonneQSTW",
    "controllers.carcassonneengine:CarcassonneStatsEngine",
    "controllers.carcassonneengine:CarcassonneParticularStatsEngine",
))
