#!/usr/bin/env python
# -*- coding: utf-8 -*-

try:
    from PyQt4 import QtCore,QtGui
    QtCore.Signal = QtCore.pyqtSignal
    QtCore.Slot = QtCore.pyqtSlot
except ImportError as error:
    from PySide import QtCore,QtGui
    QtGui.QFileDialog.getOpenFileNameAndFilter = QtGui.QFileDialog.getOpenFileName

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
        self.openedGames = []
        self.translator = None
        self.initUI()

    def initUI(self):

        #Window settings

        self.setGeometry(100, 50, 1024, 600)
        
        self.icon = QtGui.QIcon('icons/cards.png')
        self.setWindowIcon(self.icon)

        #Menu settings
        self.menubar = self.menuBar()
        self.fileMenu = self.menubar.addMenu('')
        
        self.languageAction = QtGui.QAction(self)
        self.languageAction.triggered.connect(self.chooseLanguage)
        self.fileMenu.addAction(self.languageAction)
        
        self.exitAction = QtGui.QAction(self)
        self.exitAction.triggered.connect(self.close)
        self.fileMenu.addAction(self.exitAction)
        
        self.helpMenu = self.menubar.addMenu('')
        self.aboutAction = QtGui.QAction(self)
        self.aboutAction.triggered.connect(self.about)
        self.helpMenu.addAction(self.aboutAction)
        
        
        #Central stuff!!
        self.centralwidget = QtGui.QWidget(None)
        self.setCentralWidget(self.centralwidget)
        self.verticalLayout = QtGui.QVBoxLayout(self.centralwidget)

        # Tab widget
#        self.tabWidget = QtGui.QTabWidget(self.centralwidget)
#        self.verticalLayout.addWidget(self.tabWidget)

        #New game tab
        self.newGameTab = NewGameWidget(self)
        self.verticalLayout.addWidget(self.newGameTab)
#        self.tabWidget.addTab(self.newGameTab, "")
#        self.tabWidget.setCurrentIndex(0)

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
        
        self.helpMenu.setTitle(QtGui.QApplication.translate("MainWindow",'&Help'))
        self.aboutAction.setText(QtGui.QApplication.translate("MainWindow",'&About Gamelog...'))
        
        self.newGameTab.retranslateUI()
        for game in self.openedGames: game.retranslateUI()
#        self.tabWidget.setTabText(0,QtGui.QApplication.translate("MainWindow",'New Match'))
#        for i in range(self.tabWidget.count()):
#            self.tabWidget.widget(i).retranslateUI()
        
    def closeEvent(self, event):
        if self.ensureClose(): event.accept()
        else: event.ignore()
        
    def ensureClose(self):
        realopened = [x for x in self.openedGames if not x.isFinished()]
        numgames = len(realopened)
        if numgames > 0:
            if (numgames == 1):
                reply = QtGui.QMessageBox.question(self, QtGui.QApplication.translate("MainWindow",'Exit'),
                                                   QtGui.QApplication.translate("MainWindow","You have an opened {} match. Do you want to save it before exiting?").format(realopened[0].getGameName()), QtGui.QMessageBox.Yes | 
                                                   QtGui.QMessageBox.No | QtGui.QMessageBox.Cancel, QtGui.QMessageBox.Cancel)
            else:
                reply = QtGui.QMessageBox.question(self, QtGui.QApplication.translate("MainWindow",'Exit'),
                                                   QtGui.QApplication.translate("MainWindow","You have {} opened matches. Do you want to save them before exiting?").format(numgames), QtGui.QMessageBox.Yes | 
                                                   QtGui.QMessageBox.No | QtGui.QMessageBox.Cancel, QtGui.QMessageBox.Cancel)
            
            if reply == QtGui.QMessageBox.Cancel: return False
            
            for game in realopened:
                if reply == QtGui.QMessageBox.No:
                    game.closeMatch()
                else:
                    game.saveMatch()
        else:
            reply = QtGui.QMessageBox.question(self, QtGui.QApplication.translate("MainWindow",'Exit'),
                QtGui.QApplication.translate("MainWindow","Are you sure you want to exit GameLog?"), QtGui.QMessageBox.Yes | 
                QtGui.QMessageBox.No, QtGui.QMessageBox.No)

            if reply == QtGui.QMessageBox.No: return False
            
        if db: db.disconnectDB()
        return True
        

            
    def newTab(self,matchTab,title):
        self.newGameTab.hide()
        self.verticalLayout.addWidget(matchTab)
        self.setWindowTitle("Gamelog - {}".format(title))
        matchTab.show()
        self.openedGames.append(matchTab)
#        idx = self.tabWidget.addTab(matchTab, title)
#        self.tabWidget.setCurrentIndex(idx)

    def removeTab(self,tab):
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
        
        
class AboutDialog(QtGui.QDialog):
    
    def __init__(self,parent=None):
        super(AboutDialog,self).__init__(parent)
        self.setFixedSize(QtCore.QSize(250,150))
        self.setWindowTitle(QtGui.QApplication.translate("AboutDialog",'About Gamelog'))
        self.widgetlayout = QtGui.QHBoxLayout(self)
        self.iconlabel = QtGui.QLabel(self)
        self.iconlabel.setMaximumSize(75, 75)
        self.iconlabel.setScaledContents(True)
        self.iconlabel.setPixmap(QtGui.QPixmap('icons/cards.png'))
        self.widgetlayout.addWidget(self.iconlabel)
        self.contentlayout = QtGui.QVBoxLayout()
        self.widgetlayout.addLayout(self.contentlayout)
        self.title = QtGui.QLabel("Gamelog")
        self.title.setStyleSheet("QLabel{font-size:18px; font-weight:bold}")
        self.title.setAlignment(QtCore.Qt.AlignLeft)
        self.contentlayout.addWidget(self.title)
        self.content = QtGui.QLabel(QtGui.QApplication.translate("AboutDialog",'Gamelog is a utility to keep track of the score in board games.'))
        self.content.setWordWrap(True)
        self.content.setAlignment(QtCore.Qt.AlignTop)
        self.contentlayout.addWidget(self.content)    
        self.content = QtGui.QLabel('Xavi Abellan 2012')
        self.content.setWordWrap(True)
        self.content.setAlignment(QtCore.Qt.AlignLeft)
        self.contentlayout.addWidget(self.content) 
