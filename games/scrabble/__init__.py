from core.registry import GameDefinition, registry

registry.register(GameDefinition(
    "Scrabble", 4, "Scrabble word game", "Standard rules", "games.scrabble.model:ScrabbleMatch",
    "games.scrabble.engine:ScrabbleEngine", "games.scrabble.widget:ScrabbleWidget",
    "games.scrabble.widget:ScrabbleQSTW", "games.scrabble.engine:ScrabbleStatsEngine",
    "games.scrabble.engine:ScrabbleParticularStatsEngine",
))
