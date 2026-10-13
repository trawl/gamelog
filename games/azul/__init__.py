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
        rules_doc="azul",
        rules_url="https://cdn.svc.asmodee.net/production-nextmove/uploads/sites/4/2024/06/EN-Azul-Rules-Next-Move-web.pdf",
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
        rules_doc="azul_summer_pavilion",
        rules_url="https://cdn.svc.asmodee.net/production-nextmove/uploads/sites/4/2024/06/EN-Azul-SP-Rules-2019-12-16_compressed.pdf",
    )
)
