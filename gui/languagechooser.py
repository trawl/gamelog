#!/usr/bin/env python
# -*- coding: utf-8 -*-

try:
    from PyQt4 import QtCore,QtGui
    QtCore.Signal = QtCore.pyqtSignal
    QtCore.Slot = QtCore.pyqtSlot
except ImportError as error:
    from PySide import QtCore,QtGui
    QtGui.QFileDialog.getOpenFileNameAndFilter = QtGui.QFileDialog.getOpenFileName
    
    
class LanguageChooser(QtGui.QDialog):
    
    newQM = QtCore.Signal(str)
    supportedLanguages = {'Español':'i18n/es_ES','English':'i18n/en_GB','Català':'i18n/ca_ES'}
    
    def __init__(self,parent=None):
        super(LanguageChooser,self).__init__(parent)
        self.initUI()
        
    def initUI(self):
        self.setWindowTitle(QtGui.QApplication.translate("LanguageChooser","Language"))
        self.widgetLayout = QtGui.QVBoxLayout(self)
        self.infoLabel = QtGui.QLabel(self)
        self.infoLabel.setText(QtGui.QApplication.translate("LanguageChooser","Select the desired language:"))
        self.widgetLayout.addWidget(self.infoLabel)
        self.languageListWidget = QtGui.QListWidget(self)
        self.widgetLayout.addWidget(self.languageListWidget)
        for language in self.supportedLanguages.keys():
            self.languageListWidget.addItem(language)

            
        self.buttonBox = QtGui.QDialogButtonBox(QtGui.QDialogButtonBox.Ok|QtGui.QDialogButtonBox.Cancel,QtCore.Qt.Horizontal,self)
        self.buttonBox.accepted.connect(self.changeLanguage)
        self.buttonBox.rejected.connect(self.close)
        self.widgetLayout.addWidget(self.buttonBox)

    def changeLanguage(self):

        ci = self.languageListWidget.currentItem()
        if ci:
            selected = ci.text()
            fname = self.supportedLanguages[selected]
            self.newQM.emit(fname)
        self.close()

