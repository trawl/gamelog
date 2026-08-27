from core.registry import GameDefinition, registry

registry.register(
    GameDefinition(
        "Phase10",
        6,
        "Standard Edition",
        "Home rules",
        "games.phase10.model:Phase10Match",
        "games.phase10.engine:Phase10Engine",
        "games.phase10.widget:Phase10Widget",
        "games.phase10.widget:Phase10QSTW",
        "games.phase10.engine:Phase10StatsEngine",
        "games.phase10.engine:Phase10ParticularStatsEngine",
    )
)
registry.register(
    GameDefinition(
        "Phase10Master",
        6,
        "Master Edition",
        "Home rules",
        "games.phase10.model:Phase10MasterMatch",
        "games.phase10.engine:Phase10MasterEngine",
        "games.phase10.widget:Phase10Widget",
        "games.phase10.widget:Phase10QSTW",
        "games.phase10.engine:Phase10StatsEngine",
        "games.phase10.engine:Phase10ParticularStatsEngine",
    )
)
