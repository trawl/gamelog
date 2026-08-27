from core.registry import GameDefinition, registry

registry.register(GameDefinition(
    "Toma6", 10, "Toma6 card game", "Home rules", "model.toma6:Toma6Match",
    "controllers.toma6engine:Toma6Engine", "gui.toma6:Toma6Widget",
))
