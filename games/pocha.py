from games.registry import GameDefinition, registry

registry.register(GameDefinition(
    "Pocha", 6, "Carcassonne board game", "Home rules", "model.pocha:PochaMatch",
    "controllers.pochaengine:PochaEngine", "gui.pocha:PochaWidget", "gui.pocha:PochaQSTW",
    "controllers.pochaengine:PochaStatsEngine",
    "controllers.pochaengine:PochaParticularStatsEngine",
))
