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
