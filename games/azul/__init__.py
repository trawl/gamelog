from core.registry import GameDefinition, registry

registry.register(
    GameDefinition(
        "Azul",
        4,
        "Azul tile-drafting board game",
        "Standard rules",
        "games.azul.model:AzulMatch",
        "games.azul.engine:AzulEngine",
        "games.azul.widget:AzulWidget",
        "games.azul.widget:AzulQSTW",
        "games.azul.engine:AzulStatsEngine",
        "games.azul.engine:AzulParticularStatsEngine",
    )
)
registry.register(
    GameDefinition(
        "Azul Summer Pavilion",
        4,
        "Summer Pavilion edition",
        "Standard rules",
        "games.azul.model:AzulSummerPavilionMatch",
        "games.azul.engine:AzulSummerPavilionEngine",
        "games.azul.widget:AzulWidget",
        "games.azul.widget:AzulQSTW",
        "games.azul.engine:AzulSummerPavilionStatsEngine",
        "games.azul.engine:AzulSummerPavilionParticularStatsEngine",
    )
)
