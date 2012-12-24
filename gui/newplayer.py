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

class NewPlayerDialog(QtGui.QDialog):
    
    addedNewPlayer = QtCore.Signal(str)
    
    def __init__(self,parent=None):
        super(NewPlayerDialog,self).__init__(parent)
        self.initUI()
#        self.com = com
        self.setWindowTitle("Nuevo Jugador")
        self.existingplayers = [ str(nick).lower() for nick in db.getPlayerNicks() ] 

        
    def initUI(self):
        self.vlayout = QtGui.QVBoxLayout(self)
        self.layout = QtGui.QGridLayout()
        self.vlayout.addLayout(self.layout)
        self.nicklabel = QtGui.QLabel(self)
        self.nicklabel.setText("Nick")
        self.layout.addWidget(self.nicklabel,0,0)
        self.nicklineedit = QtGui.QLineEdit(self)
        self.nicklineedit.textChanged.connect(self.checkExisting)
        self.layout.addWidget(self.nicklineedit, 0,1)
        self.namelabel = QtGui.QLabel(self)
        self.namelabel.setText("Nombre")
        self.layout.addWidget(self.namelabel,1,0)
        self.namelineedit = QtGui.QLineEdit(self)
        self.namelineedit.textChanged.connect(self.checkExisting)
        self.layout.addWidget(self.namelineedit, 1,1)
        self.existinglabel = QtGui.QLabel()
        self.existinglabel.setStyleSheet("QLabel {color: red; }")
        self.vlayout.addWidget(self.existinglabel)
        self.createbutton = QtGui.QPushButton(self)
        self.createbutton.setText("Crear")
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
            self.existinglabel.setText("El jugador ya existe")
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
                                    
        