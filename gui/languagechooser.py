#!/usr/bin/env python
# -*- coding: utf-8 -*-

try:
    from PySide import QtGui,QtCore
except ImportError as error:
    from PyQt4 import QtGui,QtCore
    
    
class LanguageChooser(QtGui.QDialog):
    def __init__(self,parent=None):
        super(LanguageChooser,self).__init__(parent)
        self.supportedLanguages = {u'Español':'i18n/es_ES',u'English':'i18n/en_GB',u'Català':'i18n/ca_ES'}
        self.initUI()
        
    def initUI(self):
        self.widgetLayout = QtGui.QVBoxLayout(self)
        self.infoLabel = QtGui.QLabel(self)
        self.infoLabel.setText(QtGui.QApplication.translate("LanguageChooser","Select the desired language:"))
        self.widgetLayout.addWidget(self.infoLabel)
        self.languageListWidget = QtGui.QListWidget(self)
        self.widgetLayout.addWidget(self.languageListWidget)
        for language in self.supportedLanguages.keys():
            self.languageListWidget.addItem(language)
        self.buttonsLayout = QtGui.QHBoxLayout()
        self.widgetLayout.addLayout(self.buttonsLayout)
        self.cancelButton = QtGui.QPushButton(self)
        self.cancelButton.setText(QtGui.QApplication.translate("LanguageChooser","Cancel"))
        self.cancelButton.pressed.connect(self.close)
        self.buttonsLayout.addWidget(self.cancelButton)
        self.okButton = QtGui.QPushButton(self)
        self.okButton.setText(QtGui.QApplication.translate("LanguageChooser","OK"))
        self.okButton.pressed.connect(self.changeLanguage)
        self.buttonsLayout.addWidget(self.okButton)

    def changeLanguage(self):

        ci = self.languageListWidget.currentItem()
        if ci:
            selected = ci.text()
            print("Now I would change the language to {}!".format(selected))
        self.close()

