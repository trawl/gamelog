"""Application settings: environment overrides and defaults."""


def test_defaults_seeded(settings):
    assert settings["theme"] == "system"
    assert settings["log_level"] == "WARNING"


def test_env_var_overrides_known_setting(monkeypatch, settings):
    monkeypatch.setenv("GAMELOG_THEME", "dark")
    settings.refresh()
    assert settings["theme"] == "dark"


def test_unknown_env_var_is_ignored(monkeypatch, settings):
    monkeypatch.setenv("GAMELOG_NOT_A_SETTING", "boom")
    settings.refresh()
    assert settings.get("not_a_setting") is None


def test_persistent_set_roundtrips(settings):
    settings.set("theme", "light", persistent=True)
    settings.refresh()
    assert settings["theme"] == "light"


def test_game_settings_discovered(settings):
    game_settings = settings.getGameSettings()
    assert isinstance(game_settings, dict)
    assert len(game_settings) > 0
    # Every registered game with a settings_factory should appear as a key.
    all_keys = {k for gsettings in game_settings.values() for k in gsettings}
    assert "remigio_dealer_policy" in all_keys
    assert "skullking_scoring_mode" in all_keys


def test_game_setting_persistent_roundtrip(settings):
    settings.getGameSettings()  # trigger lazy discovery
    settings.set("remigio_top_score", 200, persistent=True)
    assert settings["remigio_top_score"] == 200
