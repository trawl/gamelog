"""Log-level resolution: env var > explicit arg > saved setting > default."""

import logging

from core.logging_config import _resolve_level, set_log_level

ENV = "GAMELOG_LOG_LEVEL"


def test_explicit_arg_used_when_no_env(monkeypatch):
    monkeypatch.delenv(ENV, raising=False)
    assert _resolve_level("INFO") == "INFO"


def test_env_overrides_everything(monkeypatch, settings):
    settings.set("log_level", "DEBUG", persistent=True)
    monkeypatch.setenv(ENV, "ERROR")
    # Wins over both the saved setting and an explicit argument.
    assert _resolve_level() == "ERROR"
    assert _resolve_level("DEBUG") == "ERROR"


def test_saved_setting_used_when_no_env(monkeypatch, settings):
    monkeypatch.delenv(ENV, raising=False)
    settings.set("log_level", "DEBUG", persistent=True)
    assert _resolve_level() == "DEBUG"


def test_default_when_nothing_set(monkeypatch, settings):
    monkeypatch.delenv(ENV, raising=False)
    settings.set("log_level", "WARNING", persistent=True)
    assert _resolve_level() == "WARNING"


def test_set_log_level_applies_to_root(monkeypatch, settings):
    monkeypatch.delenv(ENV, raising=False)
    try:
        set_log_level("DEBUG")
        assert logging.getLogger().level == logging.DEBUG
    finally:
        logging.getLogger().setLevel(logging.WARNING)
