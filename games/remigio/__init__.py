from core.registry import GameDefinition, registry

registry.register(GameDefinition(
    "Remigio", 12, "Classic Remigio", "Home rules",
    "games.remigio.model:RemigioMatch", "games.remigio.engine:RemigioEngine",
    "games.remigio.widget:RemigioWidget",
))
