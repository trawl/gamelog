from core.registry import GameDefinition, registry

registry.register(
    GameDefinition(
        "Pocha",
        6,
        "Spanish trick-taking card game",
        "Home rules",
        "games.pocha.model:PochaMatch",
        "games.pocha.engine:PochaEngine",
        "games.pocha.widget:PochaWidget",
        "games.pocha.widget:PochaQSTW",
        "games.pocha.engine:PochaStatsEngine",
        "games.pocha.engine:PochaParticularStatsEngine",
        settings_factory="games.pocha.settings:game_settings",
        rules_doc="pocha",
        rules_url="https://www.nhfournier.es/en/como-jugar/pocha/",
        short_name="Poc",
        round_winners=True,
        player_stats_factory="games.pocha.playerstats:player_stats",
    )
)
