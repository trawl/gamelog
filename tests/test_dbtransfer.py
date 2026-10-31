"""Whole-database export and import."""

import sqlite3

import pytest

from core.engine.db import DatabaseError, db
from core.engine.dbtransfer import (
    BACKUPS_TO_KEEP,
    backup_dir,
    export_database,
    import_database,
    validate_database,
)
from core.engine.settings import appsettings
from core.ui.dbtransfer import read_user_file, write_user_file


def _live_path():
    path = db.getDBPath()
    assert path is not None
    return path


def _nicks() -> list[str]:
    return db.getPlayerNicks()


@pytest.fixture
def other_db(tmp_path):
    """A second, populated Gamelog database file to import."""
    path = tmp_path / "other.db"
    db.connectDB(str(path))
    db.addPlayer("O'Brien", "Imported Player")
    export = tmp_path / "export.db"
    export_database(export)
    return export


def test_export_is_a_valid_copy(gamedb, tmp_path):
    db.addPlayer("ann", "Ann")
    dest = tmp_path / "out.db"
    export_database(dest)
    validate_database(dest)
    con = sqlite3.connect(dest)
    assert con.execute("SELECT nick FROM Player").fetchall() == [("ann",)]
    con.close()


def test_export_overwrites_existing_file(gamedb, tmp_path):
    dest = tmp_path / "out.db"
    dest.write_text("not a database")
    export_database(dest)
    validate_database(dest)


def test_export_refuses_the_live_file(gamedb):
    with pytest.raises(DatabaseError):
        export_database(_live_path())


def test_validate_rejects_garbage_and_foreign_databases(gamedb, tmp_path):
    junk = tmp_path / "junk.db"
    junk.write_text("definitely not sqlite")
    with pytest.raises(DatabaseError):
        validate_database(junk)

    foreign = tmp_path / "foreign.db"
    con = sqlite3.connect(foreign)
    con.execute("CREATE TABLE other (x)")
    con.commit()
    con.close()
    with pytest.raises(DatabaseError, match="missing"):
        validate_database(foreign)

    with pytest.raises(DatabaseError):
        validate_database(tmp_path / "absent.db")


def test_import_replaces_data_and_keeps_a_backup(gamedb, other_db):
    db.connectDB(str(other_db.parent / "live.db"))
    db.addPlayer("mine", "Mine")
    backup = import_database(other_db)

    assert _nicks() == ["O'Brien"]
    assert backup.parent == backup_dir()
    old = sqlite3.connect(backup)
    assert old.execute("SELECT nick FROM Player").fetchall() == [("mine",)]
    old.close()


def test_failed_import_leaves_data_untouched(gamedb, tmp_path):
    db.addPlayer("mine", "Mine")
    junk = tmp_path / "junk.db"
    junk.write_text("nope")
    with pytest.raises(DatabaseError):
        import_database(junk)
    assert _nicks() == ["mine"]
    assert not backup_dir().exists()


def test_import_refuses_the_live_file(gamedb):
    with pytest.raises(DatabaseError):
        import_database(_live_path())


def test_old_backups_are_pruned(gamedb, other_db):
    db.connectDB(str(other_db.parent / "live.db"))
    folder = backup_dir()
    folder.mkdir()
    for i in range(BACKUPS_TO_KEEP + 3):
        (folder / f"gamelog-2000010{i}-000000.db").write_bytes(b"")
    import_database(other_db)
    assert len(list(folder.glob("gamelog-*.db"))) == BACKUPS_TO_KEEP


def test_settings_reload_after_import(settings, tmp_path):
    other = tmp_path / "other.db"
    db.connectDB(str(other))
    appsettings.dbseed()
    appsettings.set("theme", "dark")
    staged = tmp_path / "staged.db"
    export_database(staged)

    db.connectDB(str(tmp_path / "live.db"))
    appsettings.reload()
    assert appsettings["theme"] != "dark"
    import_database(staged)
    appsettings.reload()
    assert appsettings["theme"] == "dark"


def test_user_file_round_trip(qapp, tmp_path):
    source = tmp_path / "source.bin"
    source.write_bytes(b"\x00gamelog\xff" * 100)
    target = tmp_path / "target.bin"
    write_user_file(str(target), source)
    copy = tmp_path / "copy.bin"
    read_user_file(str(target), copy)
    assert copy.read_bytes() == source.read_bytes()


def test_read_user_file_reports_missing_file(qapp, tmp_path):
    with pytest.raises(OSError):
        read_user_file(str(tmp_path / "absent"), tmp_path / "dest")
