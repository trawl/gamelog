#!/usr/bin/env python
# -*- coding: utf-8 -*-

try:
    from PySide import QtCore,QtGui
    QtGui.QFileDialog.getOpenFileNameAndFilter = QtGui.QFileDialog.getOpenFileName
except ImportError as error:
    from PyQt4 import QtCore,QtGui
    QtCore.Signal = QtCore.pyqtSignal
    QtCore.Slot = QtCore.pyqtSlot

from gui.newgame import *

class MainWindow(QtGui.QMainWindow):

    def __init__(self):
        super(MainWindow, self).__init__()
        self.initUI()

    def initUI(self):

        #Window settings
        self.setWindowTitle('GameLog')
        self.statusBar().showMessage('GameLog')
        self.setGeometry(100, 50, 1024, 600)

        #Menu settings
        menubar = self.menuBar()
        fileMenu = menubar.addMenu('&Archivo')
        exitAction = QtGui.QAction(QtGui.QIcon('exit.png'), '&Salir', self)
        exitAction.setShortcut('Ctrl+Q')
        exitAction.setStatusTip('Salir de GameLog')
        exitAction.triggered.connect(QtGui.qApp.quit)
        fileMenu.addAction(exitAction)

        #Central stuff!!
        self.centralwidget = QtGui.QWidget(None)
        self.setCentralWidget(self.centralwidget)
        self.verticalLayout = QtGui.QVBoxLayout(self.centralwidget)

        # Tab widget
        self.tabWidget = QtGui.QTabWidget(self.centralwidget)
        self.verticalLayout.addWidget(self.tabWidget)

        #New game tab
        #self.newGameTab = QtGui.QWidget()
        self.newGameTab = NewGameWidget(self)
        self.tabWidget.addTab(self.newGameTab, "Nueva Partida")
        self.tabWidget.setCurrentIndex(1)

        #And finally, show it!
        self.show()
        
    def closeEvent(self, event):
        
        reply = QtGui.QMessageBox.question(self, 'Salir',
            u"Estás seguro que quieres salir de GameLog?", QtGui.QMessageBox.Yes | 
            QtGui.QMessageBox.No, QtGui.QMessageBox.No)

        if reply == QtGui.QMessageBox.Yes:
            event.accept()
            self.newGameTab.closeMatches()
        else:
            event.ignore()    
