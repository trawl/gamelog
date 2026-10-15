"""Top-level application window."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from PySide6 import QtCore, QtGui
from PySide6.QtGui import QAction, QCloseEvent
from PySide6.QtWidgets import (
    QMainWindow,
    QMessageBox,
    QVBoxLayout,
    QWidget,
)

from core.engine.db import db
from core.engine.resume import open_match
from core.model.match import GenericMatch
from core.registry import registry
from core.ui.dialogs import AboutDialog
from core.ui.explorer import MatchExplorerWidget
from core.ui.newgame import NewGameWidget

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from PySide6.QtCore import QEvent

    from core.ui.game import GameWidget


class MainWindow(QMainWindow):
    """Main window hosting the new-game tab and any running match tabs."""

    # Dialog translations
    QtCore.QT_TRANSLATE_NOOP("QDialogButtonBox", "&Yes")
    QtCore.QT_TRANSLATE_NOOP("QDialogButtonBox", "&No")
    QtCore.QT_TRANSLATE_NOOP("QDialogButtonBox", "OK")
    QtCore.QT_TRANSLATE_NOOP("QDialogButtonBox", "Cancel")

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        if not db.isConnected():
            db.connectDB()
        logger.info("MainWindow opened")
        self.openedGames: list[GameWidget] = []
        # Where to go back to when a match tab closes (the screen it was
        # opened from); the new-game screen when absent.
        self._origins: dict[GameWidget, QWidget] = {}
        self.initUI()

    def initUI(self) -> None:
        """Build the menus, central widget and new-game tab, then show."""
        # Window settings

        self.setGeometry(100, 50, 1024, 600)

        self.icon = QtGui.QIcon(":/icons/cards.png")
        self.setWindowIcon(self.icon)

        # Menu settings
        self.menubar = self.menuBar()
        self.fileMenu = self.menubar.addMenu("")

        self.exitAction = QAction(self)
        self.exitAction.triggered.connect(self.close)
        self.fileMenu.addAction(self.exitAction)

        self.helpMenu = self.menubar.addMenu("")
        self.aboutAction = QAction(self)
        self.aboutAction.triggered.connect(self.about)
        self.helpMenu.addAction(self.aboutAction)

        # Central stuff!!
        self.centralwidget = QWidget(None)
        self.setCentralWidget(self.centralwidget)
        self.verticalLayout = QVBoxLayout(self.centralwidget)

        # Tab widget
        #        self.tabWidget = QTabWidget(self.centralwidget)
        #        self.verticalLayout.addWidget(self.tabWidget)

        # New game tab
        self.newGameTab = NewGameWidget(self)
        self.verticalLayout.addWidget(self.newGameTab)

        # Match explorer, shown in place of the new-game screen on demand
        self.explorerTab = MatchExplorerWidget(self)
        self.explorerTab.backRequested.connect(self.hideExplorer)
        self.explorerTab.openRequested.connect(self.openStoredMatch)
        self.verticalLayout.addWidget(self.explorerTab)
        self.explorerTab.hide()
        #        self.tabWidget.addTab(self.newGameTab, "")
        #        self.tabWidget.setCurrentIndex(0)
        self.statusBar().hide()

        self.retranslateUi()

        # And finally, show it!

        # self.setStyleSheet("font-size: 20px;")
        self.setStyleSheet("font-size: 18px;")

        self.show()

    def retranslateUi(self) -> None:
        """Re-apply translated text to every widget after a language change."""
        self.setWindowTitle(self.tr("GameLog"))
        self.statusBar().showMessage(self.tr("GameLog"))
        self.fileMenu.setTitle(self.tr("&File"))
        # self.languageAction.setText(self.tr("&Language..."))
        self.exitAction.setText(self.tr("&Quit"))
        self.exitAction.setShortcut(self.tr("Ctrl+Q"))
        self.exitAction.setStatusTip(self.tr("Quit GameLog"))

        self.helpMenu.setTitle(self.tr("&Help"))
        self.aboutAction.setText(self.tr("&About Gamelog..."))

        self.newGameTab.retranslateUI()
        self.explorerTab.retranslateUI()
        for game in self.openedGames:
            game.retranslateUI()

    def closeEvent(self, event: QCloseEvent) -> None:
        if self.ensureClose():
            logger.info("MainWindow closing")
            event.accept()
        else:
            logger.debug("MainWindow close cancelled by user")
            event.ignore()

    def ensureClose(self) -> bool:
        """Prompt to save any open matches; return False to abort closing."""
        realopened = [x for x in self.openedGames if not x.isFinished()]
        numgames = len(realopened)
        if numgames > 0:
            tit = self.tr("Exit")
            if numgames == 1:
                msg = self.tr(
                    "You have an opened {} match. Do you want to save it before exiting?"
                )
                msg = msg.format(realopened[0].getGameName())
                reply = QMessageBox.question(
                    self,
                    tit,
                    msg,
                    QMessageBox.StandardButton.Yes
                    | QMessageBox.StandardButton.No
                    | QMessageBox.StandardButton.Cancel,
                    QMessageBox.StandardButton.Cancel,
                )
            else:
                tit = self.tr("Exit")
                msg = self.tr(
                    "You have {} opened matches. Do you want to save them before exiting?"
                )
                msg = msg.format(numgames)
                reply = QMessageBox.question(
                    self,
                    tit,
                    msg,
                    QMessageBox.StandardButton.Yes
                    | QMessageBox.StandardButton.No
                    | QMessageBox.StandardButton.Cancel,
                    QMessageBox.StandardButton.Cancel,
                )

            if reply == QMessageBox.StandardButton.Cancel:
                return False

            for game in realopened:
                game.toggleScreenLock(True)
                if reply == QMessageBox.StandardButton.No:
                    game.closeMatch()
                else:
                    game.saveMatch()
        else:
            tit = self.tr("Exit")
            msg = self.tr("Are you sure you want to exit GameLog?")

            reply = QMessageBox.question(
                self,
                tit,
                msg,
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No,
            )

            if reply == QMessageBox.StandardButton.No:
                return False

        if db:
            db.disconnectDB()
        return True

    def showExplorer(self) -> None:
        """Swap the new-game screen for the match explorer."""
        self.newGameTab.hide()
        self.explorerTab.show()
        self.setWindowTitle(self.tr("Gamelog - Match history"))

    def hideExplorer(self) -> None:
        """Return from the match explorer to the new-game screen."""
        self.explorerTab.hide()
        self.newGameTab.show()
        self.setWindowTitle("Gamelog")

    def openStoredMatch(self, idMatch: int, game: str) -> None:
        """Open a match from the archive in its own state.

        A saved match is resumed; a finished one shows its final board; a
        cancelled or interrupted one opens locked, for review only.
        """
        # A double-click raises both "double-clicked" and "activated".
        if any(g.engine.match.idMatch == idMatch for g in self.openedGames):
            return
        engine = open_match(game, idMatch)
        matchTab = registry.create_widget(game, None, engine, self) if engine else None
        if engine is None or matchTab is None:
            logger.error("Could not open %s match #%d", game, idMatch)
            QMessageBox.warning(
                self, self.tr("Match history"), self.tr("The match could not be opened")
            )
            return
        logger.info("Opening %s match #%d from the match history", game, idMatch)
        matchTab.restartRequested.connect(self.newGameTab.restartGame)
        matchTab.closeRequested.connect(self.removeTab)
        stored = engine.match.loadedState
        if stored == GenericMatch.FINISHED:
            matchTab.showFinishedMatch()
        elif stored is not None:
            if stored == GenericMatch.CANCELLED:
                status = self.tr("This match was cancelled")
            else:
                status = self.tr("This match was interrupted")
            matchTab.setReviewOnly(status)
        self.newTab(matchTab, game, origin=self.explorerTab)

    def newTab(
        self, matchTab: GameWidget, title: str, origin: QWidget | None = None
    ) -> None:
        """Show a running match widget and track it as an open game."""
        logger.info("Opening game tab: %s", title)
        self.newGameTab.hide()
        self.explorerTab.hide()
        if origin is not None:
            self._origins[matchTab] = origin
        self.verticalLayout.addWidget(matchTab)
        self.setWindowTitle(f"Gamelog - {title}")
        matchTab.show()
        matchTab.setFocus()
        self.openedGames.append(matchTab)

    #        idx = self.tabWidget.addTab(matchTab, title)
    #        self.tabWidget.setCurrentIndex(idx)

    def removeTab(self, tab: GameWidget) -> None:
        """Close a match widget and restore the new-game tab."""
        tab.close()
        self.openedGames.remove(tab)
        origin = self._origins.pop(tab, self.newGameTab)
        if origin is self.explorerTab:
            self.showExplorer()
        else:
            self.setWindowTitle("Gamelog")
            self.newGameTab.show()

    #        self.tabWidget.removeTab(self.tabWidget.indexOf(tab))

    def about(self) -> None:
        """Open the modal About dialog."""
        self.abdialog = AboutDialog(self)
        self.abdialog.exec_()

    def changeEvent(self, event: QEvent) -> None:
        if event.type() == QtCore.QEvent.Type.LanguageChange:
            self.retranslateUi()
        return super().changeEvent(event)
