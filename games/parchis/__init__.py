from core.registry import GameDefinition, registry

registry.register(
    GameDefinition(
        "Parchis",
        6,
        "Parchis board game",
        "Standard rules",
        "games.parchis.model:ParchisMatch",
        "games.parchis.engine:ParchisEngine",
        "games.parchis.widget:ParchisWidget",
        "games.parchis.widget:ParchisQSTW",
        "games.parchis.engine:ParchisStatsEngine",
        "games.parchis.engine:ParchisParticularStatsEngine",
        settings_factory="games.parchis.settings:game_settings",
    )
)
