#!/usr/bin/env python
# -*- coding: utf-8 -*-
from PyQt5 import QtCore, QtWidgets, QtGui
from PyQt5.QtWidgets import (QAction, QApplication, QDialog, QHBoxLayout,
                             QLabel, QMainWindow, QMessageBox, QTabWidget,
                             QVBoxLayout, QWidget)

from controllers.db import db
from gui.newgame import NewGameWidget
from gui.languagechooser import LanguageChooser

i18n = QApplication.translate


class MainWindow(QMainWindow):

    # Dialog translations
    QtCore.QT_TRANSLATE_NOOP("QDialogButtonBox", "&Yes")
    QtCore.QT_TRANSLATE_NOOP("QDialogButtonBox", "&No")
    QtCore.QT_TRANSLATE_NOOP("QDialogButtonBox", "OK")
    QtCore.QT_TRANSLATE_NOOP("QDialogButtonBox", "Cancel")

    def __init__(self, parent=None):
        super(MainWindow, self).__init__(parent)
        db.connectDB()
        self.openedGames = []
        self.translator = None
        self.initUI()

    def initUI(self):

        # Window settings

        self.setGeometry(100, 50, 1024, 600)

        self.icon = QtGui.QIcon('icons/cards.png')
        self.setWindowIcon(self.icon)

        # Menu settings
        self.menubar = self.menuBar()
        self.fileMenu = self.menubar.addMenu('')

        self.languageAction = QAction(self)
        self.languageAction.triggered.connect(self.chooseLanguage)
        self.fileMenu.addAction(self.languageAction)

        self.exitAction = QAction(self)
        self.exitAction.triggered.connect(self.close)
        self.fileMenu.addAction(self.exitAction)

        self.helpMenu = self.menubar.addMenu('')
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

        self.retranslateUi()

        # And finally, show it!

        self.setStyleSheet("font-size: 20px;")

        self.show()

    def retranslateUi(self):
        self.setWindowTitle(
            i18n("MainWindow", 'GameLog'))
        self.statusBar().showMessage(
            i18n("MainWindow", 'GameLog'))
        self.fileMenu.setTitle(
            i18n("MainWindow", '&File'))
        self.languageAction.setText(
            i18n("MainWindow", '&Language...'))
        self.exitAction.setText(
            i18n("MainWindow", '&Quit'))
        self.exitAction.setShortcut(
            i18n("MainWindow", 'Ctrl+Q'))
        self.exitAction.setStatusTip(
            i18n("MainWindow", 'Quit GameLog'))

        self.helpMenu.setTitle(
            i18n("MainWindow", '&Help'))
        self.aboutAction.setText(i18n(
            "MainWindow", '&About Gamelog...'))

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
            tit = i18n("MainWindow", 'Exit')
            if (numgames == 1):
                msg = i18n(
                    "MainWindow",
                    ("You have an opened {} match. "
                     "Do you want to save it before exiting?"))
                msg = msg.format(realopened[0].getGameName())
                reply = QMessageBox.question(self, tit, msg,
                                             QMessageBox.Yes |
                                             QMessageBox.No |
                                             QMessageBox.Cancel,
                                             QMessageBox.Cancel)
            else:
                tit = i18n("MainWindow", 'Exit')
                msg = ("You have {} opened matches. "
                       "Do you want to save them before exiting?")
                msg = i18n(
                    "MainWindow", msg).format(numgames)
                reply = QMessageBox.question(self, tit, msg,
                                             QMessageBox.Yes |
                                             QMessageBox.No |
                                             QMessageBox.Cancel,
                                             QMessageBox.Cancel)

            if reply == QMessageBox.Cancel:
                return False

            for game in realopened:
                if reply == QMessageBox.No:
                    game.closeMatch()
                else:
                    game.saveMatch()
        else:
            tit = i18n("MainWindow", 'Exit')
            msg = "Are you sure you want to exit GameLog?"
            msg = i18n("MainWindow", msg)
            reply = QMessageBox.question(self, tit, msg,
                                         QMessageBox.Yes | QMessageBox.No,
                                         QMessageBox.No)

            if reply == QMessageBox.No:
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

    def loadTranslator(self, tfile):
        translator = QtCore.QTranslator()
        ret = translator.load(tfile)
        if ret:
            if self.translator:
                qApp.removeTranslator(self.translator)
            self.translator = translator
            qApp.installTranslator(self.translator)

    def changeEvent(self, event):
        if event.type() == QtCore.QEvent.LanguageChange:
            self.retranslateUi()

        return super(MainWindow, self).changeEvent(event)


class AboutDialog(QDialog):

    def __init__(self, parent=None):
        super(AboutDialog, self).__init__(parent)
        self.setFixedSize(QtCore.QSize(250, 150))
        self.setWindowTitle(i18n(
            "AboutDialog", 'About Gamelog'))
        self.widgetlayout = QHBoxLayout(self)
        self.iconlabel = QLabel(self)
        self.iconlabel.setMaximumSize(75, 75)
        self.iconlabel.setScaledContents(True)
        self.iconlabel.setPixmap(QtGui.QPixmap('icons/cards.png'))
        self.widgetlayout.addWidget(self.iconlabel)
        self.contentlayout = QVBoxLayout()
        self.widgetlayout.addLayout(self.contentlayout)
        self.title = QLabel("Gamelog")
        self.title.setStyleSheet("QLabel{font-size:18px; font-weight:bold}")
        self.title.setAlignment(QtCore.Qt.AlignLeft)
        self.contentlayout.addWidget(self.title)
        self.content = QLabel(i18n(
            "AboutDialog",
            'Gamelog is a utility to keep track of the score in board games.'))
        self.content.setWordWrap(True)
        self.content.setAlignment(QtCore.Qt.AlignTop)
        self.contentlayout.addWidget(self.content)
        self.content = QLabel('Xavi Abellan 2012')
        self.content.setWordWrap(True)
        self.content.setAlignment(QtCore.Qt.AlignLeft)
        self.contentlayout.addWidget(self.content)
