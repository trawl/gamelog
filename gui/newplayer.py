#!/usr/bin/env python
# -*- coding: utf-8 -*-

from PyQt5 import QtCore,QtWidgets
QtCore.Signal = QtCore.pyqtSignal
QtCore.Slot = QtCore.pyqtSlot
    
from controllers.db import db

class NewPlayerDialog(QtWidgets.QDialog):
    
    addedNewPlayer = QtCore.Signal(str)
    
    def __init__(self,parent=None):
        super(NewPlayerDialog,self).__init__(parent)
        self.initUI()
        self.setWindowTitle(QtWidgets.QApplication.translate("NewPlayerDialog","New Player"))
        self.existingplayers = [ str(nick).lower() for nick in db.getPlayerNicks() ] 

        
    def initUI(self):
        self.vlayout = QtWidgets.QVBoxLayout(self)
        self.layout = QtWidgets.QGridLayout()
        self.vlayout.addLayout(self.layout)
        self.nicklabel = QtWidgets.QLabel(self)
        self.nicklabel.setText(QtWidgets.QApplication.translate("NewPlayerDialog","Nick"))
        self.layout.addWidget(self.nicklabel,0,0)
        self.nicklineedit = QtWidgets.QLineEdit(self)
        self.nicklineedit.textChanged.connect(self.checkExisting)
        self.layout.addWidget(self.nicklineedit, 0,1)
        self.namelabel = QtWidgets.QLabel(self)
        self.namelabel.setText(QtWidgets.QApplication.translate("NewPlayerDialog","Name"))
        self.layout.addWidget(self.namelabel,1,0)
        self.namelineedit = QtWidgets.QLineEdit(self)
        self.namelineedit.textChanged.connect(self.checkExisting)
        self.layout.addWidget(self.namelineedit, 1,1)
        self.existinglabel = QtWidgets.QLabel()
        self.existinglabel.setStyleSheet("QLabel {color: red; }")
        self.vlayout.addWidget(self.existinglabel)
        self.createbutton = QtWidgets.QPushButton(self)
        self.createbutton.setText(QtWidgets.QApplication.translate("NewPlayerDialog","Create"))
        self.createbutton.setDisabled(True)
        self.createbutton.clicked.connect(self.createAction)
        self.vlayout.addWidget(self.createbutton)
        self.show()
        
    def checkExisting(self,discard):
        tempnick = str(self.nicklineedit.text())
        if len(tempnick) < 3:
            self.existinglabel.setText("")
            self.createbutton.setDisabled(True)
            return
        if tempnick.lower() in self.existingplayers:
            self.existinglabel.setText(QtWidgets.QApplication.translate("NewPlayerDialog","Player already exists!"))
            self.createbutton.setDisabled(True)
        else:
            self.existinglabel.setText("")
            self.createbutton.setEnabled(len(self.namelineedit.text())>0)
    
    def createAction(self):
        nick = str(self.nicklineedit.text())
        db.addPlayer(nick,str(self.namelineedit.text()))
        self.existingplayers.append(nick)
        self.addedNewPlayer.emit(nick)
        self.accept()
                                    
        