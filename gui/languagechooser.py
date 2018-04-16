#!/usr/bin/env python
# -*- coding: utf-8 -*-

from PyQt5 import QtCore,QtWidgets
QtCore.Signal = QtCore.pyqtSignal
QtCore.Slot = QtCore.pyqtSlot
    
    
class LanguageChooser(QtWidgets.QDialog):
    
    newQM = QtCore.Signal(str)
    supportedLanguages = {'Español':'i18n/es_ES','English':'i18n/en_GB','Català':'i18n/ca_ES'}
    
    def __init__(self,parent=None):
        super(LanguageChooser,self).__init__(parent)
        self.initUI()
        
    def initUI(self):
        self.setWindowTitle(QtWidgets.QApplication.translate("LanguageChooser","Language"))
        self.widgetLayout = QtWidgets.QVBoxLayout(self)
        self.infoLabel = QtWidgets.QLabel(self)
        self.infoLabel.setText(QtWidgets.QApplication.translate("LanguageChooser","Select the desired language:"))
        self.widgetLayout.addWidget(self.infoLabel)
        self.languageListWidget = QtWidgets.QListWidget(self)
        self.widgetLayout.addWidget(self.languageListWidget)
        for language in self.supportedLanguages.keys():
            self.languageListWidget.addItem(language)

            
        self.buttonBox = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Ok|QtWidgets.QDialogButtonBox.Cancel,QtCore.Qt.Horizontal,self)
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

