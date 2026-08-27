"""Application-wide logging setup.

Diagnostics throughout the code go through the standard :mod:`logging` module
(``logging.getLogger(__name__)``) rather than ``print``. This keeps the app
quiet by default and lets verbosity be turned up when debugging, without
touching any call sites.

The effective level is resolved with this precedence:

1. the ``GAMELOG_LOG_LEVEL`` environment variable (always wins);
2. an explicit ``level`` argument;
3. the ``log_level`` application setting saved in the database;
4. the built-in default (``WARNING``).
"""

import logging
import os

_DEFAULT_LEVEL = "WARNING"


def _resolve_level(level: int | str | None = None) -> int | str:
    """Resolve the effective log level, honouring the precedence above."""
    env = os.environ.get("GAMELOG_LOG_LEVEL")
    if env:
        return env
    if level is not None:
        return level
    try:
        from core.engine.settings import appsettings

        saved = appsettings["log_level"]
    except Exception:  # noqa: BLE001 - settings/DB not ready; fall back to default
        saved = None
    return saved or _DEFAULT_LEVEL


def configure_logging(level: int | str | None = None) -> None:
    """Initialise root logging once, resolving the level via _resolve_level."""
    logging.basicConfig(
        level=_resolve_level(level),
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )


def set_log_level(level: int | str | None = None) -> None:
    """Change the active log level at runtime (e.g. from the settings dialog).

    Re-resolves precedence, so an environment override still wins over a value
    chosen in the UI.
    """
    logging.getLogger().setLevel(_resolve_level(level))
