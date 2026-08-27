from core.registry import GameDefinition, registry

registry.register(
    GameDefinition(
        "Qwirkle",
        4,
        "Qwirkle tile game",
        "Standard rules",
        "games.qwirkle.model:QwirkleMatch",
        "games.qwirkle.engine:QwirkleEngine",
        "games.qwirkle.widget:QwirkleWidget",
        "games.qwirkle.widget:QwirkleQSTW",
        "games.qwirkle.engine:QwirkleStatsEngine",
        "games.qwirkle.engine:QwirkleParticularStatsEngine",
    )
)
