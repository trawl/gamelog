"""Export/Import buttons for the whole database, shown in the settings dialog."""

from __future__ import annotations

import datetime
import logging
import tempfile
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from pathlib import Path

from PySide6.QtCore import QEvent, QFile, QIODevice, Qt, QUrl, Signal
from PySide6.QtWidgets import (
    QApplication,
    QFileDialog,
    QHBoxLayout,
    QMessageBox,
    QProgressDialog,
    QPushButton,
    QWidget,
)

from core.engine.db import DatabaseError
from core.engine.dbtransfer import backup_dir, export_database, import_database
from core.engine.settings import appsettings
from core.ui.glyphs import platform_glyph, set_button_text

logger = logging.getLogger(__name__)

DEFAULT_FILENAME = "gamelog.db"


def suggested_export_name(now: datetime.datetime | None = None) -> str:
    """A dated file name, so a default export never clashes with an old one
    (Android's picker invents a name that then cannot be written to)."""
    now = now or datetime.datetime.now()
    return f"gamelog-{now:%Y%m%d-%H%M}.db"


def _location(url: QUrl) -> str:
    """A path or URL string ``QFile`` can open, for what the user picked."""
    if url.isLocalFile():
        return url.toLocalFile()
    # Fully encoded: the default form turns %20 back into a space, and Android
    # then cannot open documents whose names contain one ("gamelog.db (2)").
    return url.toString(QUrl.ComponentFormattingOption.FullyEncoded)


def _describe(file: QFile, location: str) -> str:
    """Why ``file`` failed, with the error kind: Qt's text alone can be just
    "Unknown error" for the Android content URLs."""
    return f"{file.errorString()} ({file.error().name}) for {location}"


def read_user_file(location: str, dest: Path) -> None:
    """Copy the file the user picked to ``dest``.

    Goes through ``QFile`` rather than the filesystem because on Android the
    system file picker returns ``content://`` URIs only Qt can open.
    """
    source = QFile(location)
    if not source.open(QIODevice.OpenModeFlag.ReadOnly):
        raise OSError(_describe(source, location))
    try:
        dest.write_bytes(bytes(source.readAll().data()))
    finally:
        source.close()


def write_user_file(location: str, data: Path) -> None:
    """Write ``data``'s bytes to the location the user picked (see above)."""
    target = QFile(location)
    logger.info("Writing %s (exists: %s)", location, target.exists())
    # Some Android providers refuse one open mode for a document and accept
    # another, so try the modes in turn, noting why each one failed.
    flags = QIODevice.OpenModeFlag
    failures = []
    for mode in (
        flags.WriteOnly | flags.Truncate,
        flags.WriteOnly,
        flags.ReadWrite,
    ):
        if target.open(mode):
            break
        failures.append(f"{mode}: {_describe(target, location)}")
        logger.warning("Could not open for writing: %s", failures[-1])
    else:
        raise OSError("; ".join(failures))
    try:
        if not mode & flags.Truncate and not target.resize(0):
            logger.warning("Could not empty %s before writing", location)
        if target.write(data.read_bytes()) < 0:
            raise OSError(_describe(target, location))
    finally:
        target.close()


@contextmanager
def _busy(parent: QWidget, text: str) -> Iterator[None]:
    """Show a "working" popup while a blocking step runs on the UI thread.

    Reading or writing through Android's content URLs can take seconds with
    nothing else on screen to show that something is happening.
    """
    dialog = QProgressDialog(text, "", 0, 0, parent)
    dialog.setCancelButton(None)  # pyright: ignore[reportArgumentType]
    dialog.setWindowModality(Qt.WindowModality.WindowModal)
    dialog.setMinimumDuration(0)
    dialog.show()
    QApplication.processEvents()
    try:
        yield
    finally:
        dialog.close()
        dialog.deleteLater()


def _staging_dir() -> tempfile.TemporaryDirectory[str]:
    """Scratch folder beside the database, which is writable on every platform
    (Android has no usable system temp directory)."""
    return tempfile.TemporaryDirectory(dir=backup_dir().parent)


def open_matches() -> bool:
    """True while any match tab is open, as importing would pull its data away."""
    window = getattr(QApplication.instance(), "mainWindow", None)
    return bool(getattr(window, "openedGames", None))


class DatabaseTransferBar(QWidget):
    """Export and Import buttons; importing replaces all current data."""

    databaseReplaced = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self.exportButton = QPushButton(self)
        self.exportButton.clicked.connect(self.exportDatabase)
        layout.addWidget(self.exportButton)
        self.importButton = QPushButton(self)
        self.importButton.clicked.connect(self.importDatabase)
        layout.addWidget(self.importButton)
        self.retranslateUI()

    def retranslateUI(self) -> None:
        """Label the buttons with words or arrows, per the text-in-buttons setting."""
        export_text = self.tr("Export database...")
        import_text = self.tr("Import database...")
        words = appsettings["text_in_buttons"]
        set_button_text(
            self.exportButton, export_text if words else platform_glyph("⬆")
        )
        set_button_text(
            self.importButton, import_text if words else platform_glyph("⬇")
        )
        # Arrows say little on their own; the words are the tooltip.
        self.exportButton.setToolTip("" if words else export_text)
        self.importButton.setToolTip("" if words else import_text)

    def changeEvent(self, event: QEvent) -> None:
        if event.type() == QEvent.Type.LanguageChange:
            self.retranslateUI()
        super().changeEvent(event)

    def _filter(self) -> str:
        return self.tr("Gamelog database (*.db *.sqlite);;All files (*)")

    def _pickFile(
        self, title: str, mode: QFileDialog.AcceptMode, chosen: Callable[[str], None]
    ) -> None:
        """Show a file dialog without blocking, calling ``chosen(location)``.

        ``open()`` rather than the static ``getOpenFileName()``/``exec()``: those
        spin a nested event loop inside the modal settings dialog, which on
        Android hung the app once the system file picker returned.
        """
        dialog = QFileDialog(self, title)
        dialog.setAcceptMode(mode)
        dialog.setNameFilter(self._filter())
        if mode == QFileDialog.AcceptMode.AcceptSave:
            dialog.selectFile(suggested_export_name())
        else:
            dialog.setFileMode(QFileDialog.FileMode.ExistingFile)
        dialog.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
        # fileSelected is only emitted for local files; Android's picker hands
        # back content:// URLs, which QFile can open from their string form.
        picked: list[str] = []

        def on_selected(url: QUrl) -> None:
            # Android's picker reports the same selection more than once, and
            # the second report arrives while the first one's confirmation
            # popup is open, so handle only the first.
            if picked:
                logger.debug("Ignoring repeated selection of %s", url.toString())
                return
            picked.append(_location(url))
            chosen(picked[0])

        dialog.urlSelected.connect(on_selected)
        logger.info("Showing file dialog: %s", title)
        dialog.open()

    def exportDatabase(self) -> None:
        """Ask where to save, then write a copy of the database there."""
        self._pickFile(
            self.tr("Export database"),
            QFileDialog.AcceptMode.AcceptSave,
            self._exportTo,
        )

    def _exportTo(self, location: str) -> None:
        title = self.tr("Export database")
        logger.info("Exporting database to %s", location)
        try:
            with _busy(self, self.tr("Exporting database...")), _staging_dir() as tmp:
                staged = Path(tmp) / DEFAULT_FILENAME
                export_database(staged)
                write_user_file(location, staged)
        except (DatabaseError, OSError) as e:
            logger.warning("Database export failed", exc_info=True)
            if isinstance(e, OSError) and location.startswith("content:"):
                # The picker returned a name of its own for an existing file
                # (e.g. "gamelog.db (1)") that does not exist and cannot be
                # created, which only picking the existing file avoids.
                message = self.tr(
                    "Could not save to that file. If a file with that name "
                    "already exists, select it in the file picker and confirm "
                    "replacing it."
                )
            else:
                message = self.tr("Could not export the database: {}").format(e)
            QMessageBox.warning(self, title, message)
            return
        QMessageBox.information(self, title, self.tr("Database exported."))

    def importDatabase(self) -> None:
        """Ask for a database file and, once confirmed, replace the data with it."""
        title = self.tr("Import database")
        if open_matches():
            QMessageBox.warning(
                self,
                title,
                self.tr("Close all open matches before importing a database."),
            )
            return
        self._pickFile(title, QFileDialog.AcceptMode.AcceptOpen, self._importFrom)

    def _importFrom(self, location: str) -> None:
        title = self.tr("Import database")
        logger.info("Importing database from %s", location)
        try:
            with _staging_dir() as tmp:
                staged = Path(tmp) / DEFAULT_FILENAME
                with _busy(self, self.tr("Importing database...")):
                    read_user_file(location, staged)
                logger.info("Read %d bytes", staged.stat().st_size)
                if not self._confirmReplace(title):
                    return
                # Stays up through the reload below: rebuilding the screens
                # from the new data takes seconds of its own.
                with _busy(self, self.tr("Importing database...")):
                    import_database(staged)
                    logger.info("Database imported; reloading the app")
                    self.databaseReplaced.emit()
        except (DatabaseError, OSError) as e:
            logger.warning("Database import failed", exc_info=True)
            QMessageBox.warning(
                self, title, self.tr("Could not import the database: {}").format(e)
            )
            return
        QMessageBox.information(self, title, self.tr("Database imported."))

    def _confirmReplace(self, title: str) -> bool:
        reply = QMessageBox.question(
            self,
            title,
            self.tr(
                "This replaces all current data (players, matches and settings) "
                "with the imported file. A backup of the current data is kept in "
                "{}. Continue?"
            ).format(backup_dir()),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        return reply == QMessageBox.StandardButton.Yes
