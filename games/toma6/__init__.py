from core.registry import GameDefinition, registry

registry.register(
    GameDefinition(
        "Toma6",
        10,
        "Toma6 card game",
        "Home rules",
        "games.toma6.model:Toma6Match",
        "games.toma6.engine:Toma6Engine",
        "games.toma6.widget:Toma6Widget",
    )
)
