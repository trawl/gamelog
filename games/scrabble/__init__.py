from core.registry import GameDefinition, registry

registry.register(
    GameDefinition(
        "Scrabble",
        4,
        "Scrabble word game",
        "Standard rules",
        "games.scrabble.model:ScrabbleMatch",
        "games.scrabble.engine:ScrabbleEngine",
        "games.scrabble.widget:ScrabbleWidget",
        "games.scrabble.widget:ScrabbleQSTW",
        "games.scrabble.engine:ScrabbleStatsEngine",
        "games.scrabble.engine:ScrabbleParticularStatsEngine",
        settings_factory="games.scrabble.settings:game_settings",
        rules_doc="scrabble",
        rules_url="https://service.mattel.com/instruction_sheets/53639-ENG.pdf",
        short_name="Scr",
        player_stats_factory="games.scrabble.playerstats:player_stats",
    )
)
