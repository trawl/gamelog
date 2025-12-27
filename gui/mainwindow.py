#!/usr/bin/env python
# -*- coding: utf-8 -*-
from PySide6 import QtCore, QtGui
from PySide6.QtCore import QCoreApplication
from PySide6.QtGui import QAction
from PySide6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QVBoxLayout,
    QWidget,
)

from controllers.db import db
from gui.languagechooser import LanguageChooser
from gui.newgame import NewGameWidget


class MainWindow(QMainWindow):
    # Dialog translations
    QtCore.QT_TRANSLATE_NOOP("QDialogButtonBox", "&Yes")
    QtCore.QT_TRANSLATE_NOOP("QDialogButtonBox", "&No")
    QtCore.QT_TRANSLATE_NOOP("QDialogButtonBox", "OK")
    QtCore.QT_TRANSLATE_NOOP("QDialogButtonBox", "Cancel")

    def __init__(self, translator=None, qt_translator=None, parent=None):
        super(MainWindow, self).__init__(parent)
        db.connectDB()
        self.openedGames = []
        self.translator = translator
        self.qt_translator = qt_translator
        self.initUI()

    def initUI(self):
        # Window settings

        self.setGeometry(100, 50, 1024, 600)

        self.icon = QtGui.QIcon("icons/cards.png")
        self.setWindowIcon(self.icon)

        # Menu settings
        self.menubar = self.menuBar()
        self.fileMenu = self.menubar.addMenu("")

        self.languageAction = QAction(self)
        self.languageAction.triggered.connect(self.chooseLanguage)
        self.fileMenu.addAction(self.languageAction)

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
        #        self.tabWidget.addTab(self.newGameTab, "")
        #        self.tabWidget.setCurrentIndex(0)
        self.statusBar().hide()

        self.retranslateUi()

        # And finally, show it!

        # self.setStyleSheet("font-size: 20px;")
        self.setStyleSheet("font-size: 18px;")

        self.show()

    def retranslateUi(self):
        self.setWindowTitle(self.tr("GameLog"))
        self.statusBar().showMessage(self.tr("GameLog"))
        self.fileMenu.setTitle(self.tr("&File"))
        self.languageAction.setText(self.tr("&Language..."))
        self.exitAction.setText(self.tr("&Quit"))
        self.exitAction.setShortcut(self.tr("Ctrl+Q"))
        self.exitAction.setStatusTip(self.tr("Quit GameLog"))

        self.helpMenu.setTitle(self.tr("&Help"))
        self.aboutAction.setText(self.tr("&About Gamelog..."))

        self.newGameTab.retranslateUI()
        for game in self.openedGames:
            game.retranslateUI()

    def closeEvent(self, event):
        if self.ensureClose():
            event.accept()
        else:
            event.ignore()

    def ensureClose(self):
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

    def newTab(self, matchTab, title):
        self.newGameTab.hide()
        self.verticalLayout.addWidget(matchTab)
        self.setWindowTitle("Gamelog - {}".format(title))
        matchTab.show()
        matchTab.setFocus()
        self.openedGames.append(matchTab)

    #        idx = self.tabWidget.addTab(matchTab, title)
    #        self.tabWidget.setCurrentIndex(idx)

    def removeTab(self, tab):
        tab.close()
        self.openedGames.remove(tab)
        self.setWindowTitle("Gamelog")
        self.newGameTab.show()

    #        self.tabWidget.removeTab(self.tabWidget.indexOf(tab))

    def chooseLanguage(self):
        lc = LanguageChooser(self)
        lc.newQM.connect(self.loadTranslator)
        lc.exec_()

    def about(self):
        self.abdialog = AboutDialog(self)
        self.abdialog.exec_()

    def loadTranslator(self, lang):
        translator = QtCore.QTranslator()
        ret = translator.load(lang, "i18n/")
        qt_translator = QtCore.QTranslator()
        qt_qm = "qtbase_" + lang.split("_")[0]
        qt_translator.load(qt_qm, "i18n/")
        if ret:
            if self.translator:
                QCoreApplication.removeTranslator(self.translator)
            if self.qt_translator:
                QCoreApplication.removeTranslator(self.qt_translator)
            self.qt_translator = qt_translator
            self.translator = translator
            QCoreApplication.installTranslator(self.qt_translator)
            QCoreApplication.installTranslator(self.translator)

    def changeEvent(self, event):
        if event.type() == QtCore.QEvent.Type.LanguageChange:
            self.retranslateUi()
        return super(MainWindow, self).changeEvent(event)


class AboutDialog(QDialog):
    def __init__(self, parent=None):
        super(AboutDialog, self).__init__(parent)
        # self.setFixedSize(QtCore.QSize(450, 350))
        # self.setWindowTitle(i18n("AboutDialog", "About Gamelog"))
        self.setWindowTitle(self.tr("About Gamelog"))
        self.widgetlayout = QHBoxLayout(self)
        self.iconlabel = QLabel(self)
        self.iconlabel.setMaximumSize(75, 75)
        self.iconlabel.setScaledContents(True)
        self.iconlabel.setPixmap(QtGui.QPixmap("icons/cards.png"))
        self.widgetlayout.addWidget(self.iconlabel)
        self.contentlayout = QVBoxLayout()
        self.widgetlayout.addLayout(self.contentlayout)
        self.title = QLabel("Gamelog")
        self.title.setStyleSheet("QLabel{font-size:18px; font-weight:bold}")
        self.title.setAlignment(QtCore.Qt.AlignmentFlag.AlignLeft)
        self.contentlayout.addWidget(self.title)
        # self.content = QLabel(
        #     i18n(
        #         "AboutDialog",
        #         "Gamelog is a utility to keep track of the score in board games.",
        #     )
        # )
        self.content = QLabel(
            self.tr("Gamelog is a utility to keep track of the score in board games.")
        )
        self.content.setWordWrap(True)
        self.content.setAlignment(QtCore.Qt.AlignmentFlag.AlignTop)
        self.contentlayout.addWidget(self.content)
        self.content = QLabel(f"QT {QtCore.qVersion()}")
        self.content.setWordWrap(True)
        self.content.setAlignment(QtCore.Qt.AlignmentFlag.AlignLeft)
        self.contentlayout.addWidget(self.content)
        self.content = QLabel("Xavi Abellan 2012")
        self.content.setWordWrap(True)
        self.content.setAlignment(QtCore.Qt.AlignmentFlag.AlignLeft)
        self.contentlayout.addWidget(self.content)
