"""Export/Import buttons for the whole database, shown in the settings dialog."""

from __future__ import annotations

import logging
import tempfile
from pathlib import Path

from PySide6.QtCore import QEvent, QFile, QIODevice, Signal
from PySide6.QtWidgets import (
    QApplication,
    QFileDialog,
    QHBoxLayout,
    QMessageBox,
    QPushButton,
    QWidget,
)

from core.engine.db import DatabaseError
from core.engine.dbtransfer import backup_dir, export_database, import_database
from core.engine.settings import appsettings
from core.ui.glyphs import platform_glyph

logger = logging.getLogger(__name__)

DEFAULT_FILENAME = "gamelog.db"


def read_user_file(location: str, dest: Path) -> None:
    """Copy the file the user picked to ``dest``.

    Goes through ``QFile`` rather than the filesystem because on Android the
    system file picker returns ``content://`` URIs only Qt can open.
    """
    source = QFile(location)
    if not source.open(QIODevice.OpenModeFlag.ReadOnly):
        raise OSError(source.errorString())
    try:
        dest.write_bytes(bytes(source.readAll().data()))
    finally:
        source.close()


def write_user_file(location: str, data: Path) -> None:
    """Write ``data``'s bytes to the location the user picked (see above)."""
    target = QFile(location)
    mode = QIODevice.OpenModeFlag.WriteOnly | QIODevice.OpenModeFlag.Truncate
    if not target.open(mode):
        raise OSError(target.errorString())
    try:
        if target.write(data.read_bytes()) < 0:
            raise OSError(target.errorString())
    finally:
        target.close()


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
        self.exportButton.setText(export_text if words else platform_glyph("⬆"))
        self.importButton.setText(import_text if words else platform_glyph("⬇"))
        # Arrows say little on their own; the words are the tooltip.
        self.exportButton.setToolTip("" if words else export_text)
        self.importButton.setToolTip("" if words else import_text)

    def changeEvent(self, event: QEvent) -> None:
        if event.type() == QEvent.Type.LanguageChange:
            self.retranslateUI()
        super().changeEvent(event)

    def _filter(self) -> str:
        return self.tr("Gamelog database (*.db *.sqlite);;All files (*)")

    def exportDatabase(self) -> None:
        """Ask where to save, then write a copy of the database there."""
        title = self.tr("Export database")
        location, _ = QFileDialog.getSaveFileName(
            self, title, DEFAULT_FILENAME, self._filter()
        )
        if not location:
            return
        try:
            with _staging_dir() as tmp:
                staged = Path(tmp) / DEFAULT_FILENAME
                export_database(staged)
                write_user_file(location, staged)
        except (DatabaseError, OSError) as e:
            logger.warning("Database export failed", exc_info=True)
            QMessageBox.warning(
                self, title, self.tr("Could not export the database: {}").format(e)
            )
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
        location, _ = QFileDialog.getOpenFileName(self, title, "", self._filter())
        if not location:
            return
        try:
            with _staging_dir() as tmp:
                staged = Path(tmp) / DEFAULT_FILENAME
                read_user_file(location, staged)
                if not self._confirmReplace(title):
                    return
                import_database(staged)
        except (DatabaseError, OSError) as e:
            logger.warning("Database import failed", exc_info=True)
            QMessageBox.warning(
                self, title, self.tr("Could not import the database: {}").format(e)
            )
            return
        self.databaseReplaced.emit()
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
