from core.registry import GameDefinition, registry

registry.register(
    GameDefinition(
        "Phase10", 6, "Standard Edition", "Home rules",
        "model.phase10:Phase10Match", "controllers.phase10engine:Phase10Engine",
        "gui.phase10:Phase10Widget", "gui.phase10:Phase10QSTW",
        "controllers.phase10engine:Phase10StatsEngine",
        "controllers.phase10engine:Phase10ParticularStatsEngine",
    )
)
registry.register(
    GameDefinition(
        "Phase10Master", 6, "Master Edition", "Home rules",
        "model.phase10:Phase10MasterMatch",
        "controllers.phase10engine:Phase10MasterEngine", "gui.phase10:Phase10Widget",
        "gui.phase10:Phase10QSTW", "controllers.phase10engine:Phase10StatsEngine",
        "controllers.phase10engine:Phase10ParticularStatsEngine",
    )
)
