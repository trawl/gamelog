from core.registry import GameDefinition, registry

registry.register(
    GameDefinition(
        "Skull King",
        8,
        "Skull King card game",
        "Home rules",
        "games.skullking.model:SkullKingMatch",
        "games.skullking.engine:SkullKingEngine",
        "games.skullking.widget:SkullKingWidget",
        "games.skullking.widget:SkullKingQSTW",
        "games.skullking.engine:SkullKingStatsEngine",
        "games.skullking.engine:SkullKingParticularStatsEngine",
        "games.skullking.settings:game_settings",
        rules_doc="skullking",
        rules_url="https://cdnm.heyzine.com/files/uploaded/46b5bd7166a9f579404e175e4990c9d415b4aac7.pdf",
        short_name="SK",
        round_winners=True,
        player_stats_factory="games.skullking.playerstats:player_stats",
    )
)
