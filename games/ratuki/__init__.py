from core.registry import GameDefinition, registry

registry.register(
    GameDefinition(
        "Ratuki",
        5,
        "Ratuki Slap game",
        "Home rules",
        "games.ratuki.model:RatukiMatch",
        "games.ratuki.engine:RatukiEngine",
        "games.ratuki.widget:RatukiWidget",
    )
)
