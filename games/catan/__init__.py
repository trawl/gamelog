from core.registry import GameDefinition, registry

registry.register(
    GameDefinition(
        "Catan",
        6,
        "Catan board game",
        "Standard rules",
        "games.catan.model:CatanMatch",
        "games.catan.engine:CatanEngine",
        "games.catan.widget:CatanWidget",
        rules_doc="catan",
        rules_url="https://www.catan.com/sites/default/files/2021-06/catan_base_rules_2020_200707.pdf",
        short_name="Cat",
        player_stats_factory="games.catan.playerstats:player_stats",
    )
)
