"""Export and import of the whole SQLite database.

Both operate on plain file paths and go through SQLite's online backup API, so
they are safe while the application holds the database open. Importing
*replaces* the current data (after validating the file and keeping a backup).
"""

from __future__ import annotations

import datetime
import logging
import sqlite3 as lite
from pathlib import Path

from core.engine.db import DatabaseError, db

logger = logging.getLogger(__name__)

# Tables a file must have to be recognised as a Gamelog database.
REQUIRED_TABLES = frozenset(
    {"AppSettings", "Game", "Match", "MatchPlayer", "Player", "Round"}
)
BACKUPS_TO_KEEP = 2


def backup_dir() -> Path:
    """Folder next to the live database where pre-import backups are kept."""
    path = db.getDBPath()
    if path is None:
        raise DatabaseError("Database not connected")
    return path.parent / "backups"


def _open_readonly(path: Path) -> lite.Connection:
    return lite.connect(f"{path.resolve().as_uri()}?mode=ro", uri=True)


def _same_file(a: Path, b: Path | None) -> bool:
    return b is not None and a.exists() and b.exists() and a.samefile(b)


def export_database(dest: str | Path) -> None:
    """Write a consistent copy of the live database to ``dest``."""
    dest = Path(dest)
    if db.con is None:
        raise DatabaseError("Database not connected")
    if _same_file(dest, db.getDBPath()):
        raise DatabaseError("Cannot export the database over itself")
    try:
        # backup() overwrites the destination's content, so start from nothing.
        dest.unlink(missing_ok=True)
        out = lite.connect(str(dest))
        try:
            db.con.backup(out)
        finally:
            out.close()
    except (lite.Error, OSError) as e:
        raise DatabaseError(f"Could not export database to {dest}: {e}") from e
    logger.info("Database exported to %s", dest)


def validate_database(path: str | Path) -> None:
    """Raise :class:`DatabaseError` unless ``path`` is an intact Gamelog database."""
    path = Path(path)
    if not path.is_file():
        raise DatabaseError(f"{path} is not a file")
    try:
        con = _open_readonly(path)
        try:
            if con.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
                raise DatabaseError(f"{path} is damaged")
            tables = {
                row[0]
                for row in con.execute(
                    "SELECT name FROM sqlite_master WHERE type='table'"
                )
            }
        finally:
            con.close()
    except lite.Error as e:
        raise DatabaseError(f"{path} is not a valid database: {e}") from e
    missing = REQUIRED_TABLES - tables
    if missing:
        raise DatabaseError(
            f"{path} is not a Gamelog database (missing {', '.join(sorted(missing))})"
        )


def import_database(src: str | Path) -> Path:
    """Replace the live database's content with that of ``src``.

    The file is validated first and the current data is saved to a timestamped
    file in :func:`backup_dir`, whose path is returned. Callers must refresh
    anything cached from the old data (settings, player lists, ...).
    """
    src = Path(src)
    if db.con is None:
        raise DatabaseError("Database not connected")
    if _same_file(src, db.getDBPath()):
        raise DatabaseError("Cannot import the database that is already in use")
    validate_database(src)

    folder = backup_dir()
    stamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    backup = folder / f"gamelog-{stamp}.db"
    try:
        folder.mkdir(parents=True, exist_ok=True)
    except OSError as e:
        raise DatabaseError(f"Could not create backup folder {folder}: {e}") from e
    export_database(backup)

    try:
        source = _open_readonly(src)
        try:
            # Replaces the live database's pages in a single transaction, so a
            # failure leaves the current data untouched.
            source.backup(db.con)
        finally:
            source.close()
        # Bring older files up to date and add any games they lack.
        db._checkDB()
    except lite.Error as e:
        raise DatabaseError(f"Could not import {src}: {e}") from e
    logger.info("Database imported from %s (backup %s)", src, backup)
    _prune_backups(folder)
    return backup


def _prune_backups(folder: Path) -> None:
    old = sorted(folder.glob("gamelog-*.db"))[:-BACKUPS_TO_KEEP]
    for path in old:
        path.unlink(missing_ok=True)
