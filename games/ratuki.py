from core.registry import GameDefinition, registry

registry.register(GameDefinition(
    "Ratuki", 5, "Ratuki Slap game", "Home rules",
    "model.ratuki:RatukiMatch", "controllers.ratukiengine:RatukiEngine",
    "gui.ratuki:RatukiWidget",
))
