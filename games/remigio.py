from games.registry import GameDefinition, registry

registry.register(GameDefinition(
    "Remigio", 12, "Classic Remigio", "Home rules",
    "model.remigio:RemigioMatch", "controllers.remigioengine:RemigioEngine",
    "gui.remigio:RemigioWidget",
))
