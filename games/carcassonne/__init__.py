from core.registry import GameDefinition, registry

registry.register(
    GameDefinition(
        "Carcassonne",
        6,
        "Carcassonne board game",
        "Home rules",
        "games.carcassonne.model:CarcassonneMatch",
        "games.carcassonne.engine:CarcassonneEngine",
        "games.carcassonne.widget:CarcassonneWidget",
        "games.carcassonne.widget:CarcassonneQSTW",
        "games.carcassonne.engine:CarcassonneStatsEngine",
        "games.carcassonne.engine:CarcassonneParticularStatsEngine",
        rules_doc="carcassonne",
        rules_url="https://cdn.svc.asmodee.net/production-zman/uploads/2024/09/carcassonne_v3_rulesheet_en-1.pdf",
    )
)
