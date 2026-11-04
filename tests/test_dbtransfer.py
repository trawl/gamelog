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


@pytest.fixture
def picker(monkeypatch):
    """Make the non-blocking file dialog 'select' a chosen path at once, and
    record the message boxes instead of showing them."""
    from PySide6.QtCore import QUrl
    from PySide6.QtWidgets import QFileDialog, QMessageBox

    chosen: dict[str, str] = {}
    shown: list[tuple[str, str]] = []
    # Like the real dialog: urlSelected always fires, fileSelected only for
    # local files, so a test passing on fileSelected would miss Android.
    monkeypatch.setattr(
        QFileDialog,
        "open",
        lambda self: self.urlSelected.emit(
            QUrl.fromLocalFile(chosen["path"])
            if "://" not in chosen["path"]
            else QUrl(chosen["path"])
        ),
    )
    for kind in ("information", "warning"):
        monkeypatch.setattr(
            QMessageBox,
            kind,
            lambda _parent, _title, text, kind=kind: shown.append((kind, text)),
        )
    monkeypatch.setattr(
        QMessageBox, "question", lambda *_a, **_k: QMessageBox.StandardButton.Yes
    )
    return chosen, shown


def test_export_button_writes_the_chosen_file(qapp, gamedb, tmp_path, picker):
    from core.ui.dbtransfer import DatabaseTransferBar

    chosen, shown = picker
    chosen["path"] = str(tmp_path / "picked.db")
    db.addPlayer("ann", "Ann")
    DatabaseTransferBar().exportDatabase()

    validate_database(chosen["path"])
    assert [kind for kind, _ in shown] == ["information"]


def test_import_button_replaces_the_data(qapp, gamedb, other_db, picker):
    from core.ui.dbtransfer import DatabaseTransferBar

    chosen, shown = picker
    chosen["path"] = str(other_db)
    db.connectDB(str(other_db.parent / "live.db"))
    bar = DatabaseTransferBar()
    replaced = []
    bar.databaseReplaced.connect(lambda: replaced.append(True))
    bar.importDatabase()

    assert _nicks() == ["O'Brien"]
    assert replaced == [True]
    assert [kind for kind, _ in shown] == ["information"]


def test_import_button_reports_a_bad_file(qapp, gamedb, tmp_path, picker):
    from core.ui.dbtransfer import DatabaseTransferBar

    chosen, shown = picker
    junk = tmp_path / "junk.db"
    junk.write_text("nope")
    chosen["path"] = str(junk)
    db.addPlayer("mine", "Mine")
    DatabaseTransferBar().importDatabase()

    assert _nicks() == ["mine"]
    assert [kind for kind, _ in shown] == ["warning"]


def test_import_accepts_a_content_url(qapp, gamedb, picker, monkeypatch):
    """Android's picker returns content:// URLs, which are not local files."""
    from core.ui import dbtransfer
    from core.ui.dbtransfer import DatabaseTransferBar

    chosen, shown = picker
    chosen["path"] = "content://com.android.providers/document/1234"
    opened = []

    def fake_read(location, dest):
        opened.append(location)
        raise OSError("unreadable in this test")

    monkeypatch.setattr(dbtransfer, "read_user_file", fake_read)
    DatabaseTransferBar().importDatabase()

    assert opened == ["content://com.android.providers/document/1234"]
    assert [kind for kind, _ in shown] == ["warning"]


def test_content_url_keeps_its_percent_encoding(qapp):
    """Android names clashing documents like "gamelog.db (2)"; the space must
    stay %20 or the provider cannot find the document."""
    from PySide6.QtCore import QUrl

    from core.ui.dbtransfer import _location

    url = QUrl(
        "content://com.android.externalstorage.documents/document/"
        "primary%3ADownload%2Fgamelog.db%20(2)"
    )
    assert _location(url) == (
        "content://com.android.externalstorage.documents/document/"
        "primary%3ADownload%2Fgamelog.db%20(2)"
    )


def test_local_path_with_spaces_is_decoded(qapp, tmp_path):
    from PySide6.QtCore import QUrl

    from core.ui.dbtransfer import _location

    path = tmp_path / "my data (1).db"
    assert _location(QUrl.fromLocalFile(str(path))) == str(path)


def test_a_repeated_selection_is_handled_once(
    qapp, gamedb, other_db, picker, monkeypatch
):
    """Android's picker reports one selection twice; only one popup may show."""
    from PySide6.QtCore import QUrl
    from PySide6.QtWidgets import QFileDialog

    from core.ui.dbtransfer import DatabaseTransferBar

    chosen, shown = picker
    chosen["path"] = str(other_db)
    db.connectDB(str(other_db.parent / "live.db"))

    def emit_twice(self):
        url = QUrl.fromLocalFile(chosen["path"])
        self.urlSelected.emit(url)
        self.urlSelected.emit(url)

    monkeypatch.setattr(QFileDialog, "open", emit_twice)
    questions = []
    from PySide6.QtWidgets import QMessageBox

    monkeypatch.setattr(
        QMessageBox,
        "question",
        lambda *_a, **_k: questions.append(1) or QMessageBox.StandardButton.Yes,
    )
    DatabaseTransferBar().importDatabase()

    assert len(questions) == 1
    assert [kind for kind, _ in shown] == ["information"]


def test_write_falls_back_when_truncate_is_refused(qapp, tmp_path, monkeypatch):
    """Some Android providers refuse the truncating mode for a document."""
    from PySide6.QtCore import QFile, QIODevice

    real_open = QFile.open
    attempts = []

    def open_without_truncate(self, mode):
        attempts.append(mode)
        if mode & QIODevice.OpenModeFlag.Truncate:
            return False
        return real_open(self, mode)

    monkeypatch.setattr(QFile, "open", open_without_truncate)
    source = tmp_path / "source.bin"
    source.write_bytes(b"new")
    target = tmp_path / "target.bin"
    target.write_bytes(b"much older and longer content")
    write_user_file(str(target), source)

    assert len(attempts) == 2
    assert target.read_bytes() == b"new"


def test_write_reports_every_failed_mode(qapp, tmp_path):
    source = tmp_path / "source.bin"
    source.write_bytes(b"x")
    with pytest.raises(OSError) as error:
        write_user_file(str(tmp_path / "missing-dir" / "target.bin"), source)
    assert str(error.value).count("OpenError") == 3


def test_suggested_export_name_is_dated():
    import datetime

    from core.ui.dbtransfer import suggested_export_name

    name = suggested_export_name(datetime.datetime(2026, 11, 1, 22, 13))
    assert name == "gamelog-20261101-2213.db"


def test_export_to_an_unwritable_content_url_explains_what_to_do(qapp, gamedb, picker):
    from core.ui.dbtransfer import DatabaseTransferBar

    chosen, shown = picker
    chosen["path"] = "content://com.android.externalstorage.documents/document/x%20(4)"
    DatabaseTransferBar().exportDatabase()

    assert [kind for kind, _ in shown] == ["warning"]
    assert "select it in the file picker" in shown[0][1]
