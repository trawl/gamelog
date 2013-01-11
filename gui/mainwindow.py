#!/usr/bin/env python
# -*- coding: utf-8 -*-
try:
    from PySide import QtCore,QtGui
    QtGui.QFileDialog.getOpenFileNameAndFilter = QtGui.QFileDialog.getOpenFileName
except ImportError as error:
    from PyQt4 import QtCore,QtGui
    QtCore.Signal = QtCore.pyqtSignal
    QtCore.Slot = QtCore.pyqtSlot

from controllers.db import db
from gui.newgame import NewGameWidget
from gui.languagechooser import LanguageChooser

class MainWindow(QtGui.QMainWindow):
    
    #Dialog translations
    QtCore.QT_TRANSLATE_NOOP("QDialogButtonBox", "&Yes")
    QtCore.QT_TRANSLATE_NOOP("QDialogButtonBox", "&No")
    QtCore.QT_TRANSLATE_NOOP("QDialogButtonBox", "OK")
    QtCore.QT_TRANSLATE_NOOP("QDialogButtonBox", "Cancel")

    def __init__(self,parent=None):
        super(MainWindow, self).__init__(parent)
        db.connectDB()
        self.initUI()
        self.openedGames = []
        self.translator = None

    def initUI(self):

        #Window settings

        self.setGeometry(100, 50, 1024, 600)

        #Menu settings
        self.menubar = self.menuBar()
        self.fileMenu = self.menubar.addMenu('')
        
        self.languageAction = QtGui.QAction(self)
        self.languageAction.triggered.connect(self.chooseLanguage)
        self.fileMenu.addAction(self.languageAction)
        
        self.exitAction = QtGui.QAction(self)
        self.exitAction.triggered.connect(self.close)
        self.fileMenu.addAction(self.exitAction)
        
        #Central stuff!!
        self.centralwidget = QtGui.QWidget(None)
        self.setCentralWidget(self.centralwidget)
        self.verticalLayout = QtGui.QVBoxLayout(self.centralwidget)

        # Tab widget
        self.tabWidget = QtGui.QTabWidget(self.centralwidget)
        self.verticalLayout.addWidget(self.tabWidget)

        #New game tab
        self.newGameTab = NewGameWidget(self)
        self.tabWidget.addTab(self.newGameTab, "")
        self.tabWidget.setCurrentIndex(0)

        self.retranslateUi()

        #And finally, show it!
        self.show()
        
    def retranslateUi(self):
        self.setWindowTitle(QtGui.QApplication.translate("MainWindow",'GameLog'))
        self.statusBar().showMessage(QtGui.QApplication.translate("MainWindow",'GameLog'))
        self.fileMenu.setTitle(QtGui.QApplication.translate("MainWindow",'&File'))
        self.languageAction.setText(QtGui.QApplication.translate("MainWindow",'&Language...'))
        self.exitAction.setText(QtGui.QApplication.translate("MainWindow",'&Quit'))
        self.exitAction.setShortcut(QtGui.QApplication.translate("MainWindow",'Ctrl+Q'))
        self.exitAction.setStatusTip(QtGui.QApplication.translate("MainWindow",'Quit GameLog'))
        self.tabWidget.setTabText(0,QtGui.QApplication.translate("MainWindow",'New Match'))
        for i in range(self.tabWidget.count()):
            self.tabWidget.widget(i).retranslateUI()
        
    def closeEvent(self, event):
        if self.ensureClose(): event.accept()
        else: event.ignore()
        
    def ensureClose(self):
        reply = QtGui.QMessageBox.question(self, QtGui.QApplication.translate("MainWindow",'Exit'),
            QtGui.QApplication.translate("MainWindow","Are you sure you want to exit GameLog?"), QtGui.QMessageBox.Yes | 
            QtGui.QMessageBox.No, QtGui.QMessageBox.No)

        if reply == QtGui.QMessageBox.Yes:
            for game in self.openedGames:
                game.closeMatch()
            if db: db.disconnectDB()
            return True
        
        return False
            
    def newTab(self,matchTab,title):
        self.openedGames.append(matchTab)
        idx = self.tabWidget.addTab(matchTab, title)
        self.tabWidget.setCurrentIndex(idx)

    def removeTab(self,tab):
        self.tabWidget.removeTab(self.tabWidget.indexOf(tab))
        
    def chooseLanguage(self):
        lc = LanguageChooser(self)
        lc.newQM.connect(self.loadTranslator)
        lc.exec_()
        
    def loadTranslator(self,tfile):
        translator = QtCore.QTranslator()
        ret = translator.load(tfile)
        if ret: 
            if self.translator: QtGui.qApp.removeTranslator(self.translator)
            self.translator = translator
            QtGui.qApp.installTranslator(self.translator)
                
        
    def changeEvent(self,event):
        if event.type() == QtCore.QEvent.LanguageChange:
            self.retranslateUi()
            
        return super(MainWindow,self).changeEvent(event)
        
        
        
