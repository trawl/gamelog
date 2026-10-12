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
    )
)
