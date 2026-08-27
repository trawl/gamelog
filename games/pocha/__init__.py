from core.registry import GameDefinition, registry

registry.register(
    GameDefinition(
        "Pocha",
        6,
        "Spanish trick-taking card game",
        "Home rules",
        "games.pocha.model:PochaMatch",
        "games.pocha.engine:PochaEngine",
        "games.pocha.widget:PochaWidget",
        "games.pocha.widget:PochaQSTW",
        "games.pocha.engine:PochaStatsEngine",
        "games.pocha.engine:PochaParticularStatsEngine",
    )
)
