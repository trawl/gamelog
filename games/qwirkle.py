from games.registry import GameDefinition, registry

registry.register(GameDefinition(
    "Qwirkle", 4, "Qwirkle tile game", "Standard rules", "model.qwirkle:QwirkleMatch",
    "controllers.qwirkleengine:QwirkleEngine", "gui.qwirkle:QwirkleWidget",
    "gui.qwirkle:QwirkleQSTW", "controllers.qwirkleengine:QwirkleStatsEngine",
    "controllers.qwirkleengine:QwirkleParticularStatsEngine",
))
