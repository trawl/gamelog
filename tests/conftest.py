"""Shared test fixtures.

Database access is isolated from the developer's real database: an environment
override points any connection at a throwaway location, and the ``gamedb``
fixture gives each test its own fresh SQLite file.
"""

import os
import tempfile
from typing import cast

# Must be set before importing anything that may touch the DB or Qt.
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
os.environ.setdefault(
    "GAMELOG_DB", os.path.join(tempfile.mkdtemp(prefix="gamelog-test-"), "import.db")
)

import pytest  # noqa: E402

from core.engine.db import db  # noqa: E402
from games import load_builtin_games  # noqa: E402

load_builtin_games()


@pytest.fixture
def gamedb(tmp_path):
    """Connect the shared DB singleton to a fresh per-test SQLite file."""
    db.connectDB(str(tmp_path / "test.db"))
    try:
        yield db
    finally:
        db.disconnectDB()


@pytest.fixture
def settings(gamedb):
    """Application settings backed by the per-test database."""
    from core.engine.settings import appsettings

    appsettings.dbseed()  # ensure the AppSettings table exists in this DB
    appsettings.refresh()
    return appsettings


@pytest.fixture(scope="session")
def qapp():
    """A headless GamelogApplication for widget-level tests."""
    from PySide6.QtWidgets import QMessageBox

    import resources_rc  # noqa: F401
    from core.ui.gamelogapplication import GamelogApplication
    from core.ui.languagechooser import LanguageManager
    from core.ui.thememanager import ThemeManager

    # Never let an error dialog block a headless run.
    QMessageBox.critical = staticmethod(lambda *a, **k: QMessageBox.StandardButton.Ok)  # pyright: ignore[reportAttributeAccessIssue]

    app = cast(GamelogApplication, GamelogApplication.instance()) or GamelogApplication(
        []
    )
    if not hasattr(app, "languageManager"):
        app.languageManager = LanguageManager(app)
    if not hasattr(app, "themeManager"):
        app.themeManager = ThemeManager(app)
    return app
