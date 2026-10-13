from core.registry import GameDefinition, registry

registry.register(
    GameDefinition(
        "Remigio",
        12,
        "Classic Remigio",
        "Home rules",
        "games.remigio.model:RemigioMatch",
        "games.remigio.engine:RemigioEngine",
        "games.remigio.widget:RemigioWidget",
        settings_factory="games.remigio.settings:game_settings",
        rules_doc="remigio",
        rules_url="https://www.nhfournier.es/en/como-jugar/remigio/",
    )
)
