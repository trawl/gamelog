from games.registry import GameDefinition, registry

registry.register(GameDefinition(
    "Scrabble", 4, "Scrabble word game", "Standard rules", "model.scrabble:ScrabbleMatch",
    "controllers.scrabbleengine:ScrabbleEngine", "gui.scrabble:ScrabbleWidget",
    "gui.scrabble:ScrabbleQSTW", "controllers.scrabbleengine:ScrabbleStatsEngine",
    "controllers.scrabbleengine:ScrabbleParticularStatsEngine",
))
