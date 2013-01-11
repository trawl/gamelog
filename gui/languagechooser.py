#!/usr/bin/env python
# -*- coding: utf-8 -*-

try:
    from PySide import QtGui,QtCore
except ImportError as error:
    from PyQt4 import QtGui,QtCore
    
    
class LanguageChooser(QtGui.QDialog):
    
    newQM = QtCore.Signal(str)
    supportedLanguages = {u'Español':'i18n/es_ES',u'English':'i18n/en_GB',u'Català':'i18n/ca_ES'}
    
    def __init__(self,parent=None):
        super(LanguageChooser,self).__init__(parent)
        self.initUI()
        
    def initUI(self):
        self.setWindowTitle(unicode(QtGui.QApplication.translate("LanguageChooser","Language")))
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
            fname = self.supportedLanguages[unicode(selected)]
            self.newQM.emit(fname)
        self.close()

