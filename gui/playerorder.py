#!/usr/bin/env python
# -*- coding: utf-8 -*-
from PySide6.QtWidgets import (
    QDialog,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QVBoxLayout,
    QWidget,
)


class PlayerOrderDialog(QDialog):
    def __init__(self, engine, parent=None):
        super(PlayerOrderDialog, self).__init__(parent)
        self.engine = engine
        self.setWindowTitle(self.tr("Player Order"))
        self.widgetlayout = QVBoxLayout(self)
        self.pow = PlayerOrderWidget(self.engine, self)
        self.widgetlayout.addWidget(self.pow)


class PlayerOrderWidget(QWidget):
    def __init__(self, engine, parent=None):
        super(PlayerOrderWidget, self).__init__(parent)
        self.engine = engine
        self.players = self.engine.getListPlayers()
        self.widgetLayout = QVBoxLayout(self)
        self.setAcceptDrops(True)
        for player in self.players:
            self.widgetLayout.addWidget(
                PlayerTile(player, self.engine.getDealer() == player, self)
            )

    def dragEnterEvent(self, event):
        event.accept()

    # def dropEvent(self, event):
    #     print("'%s' was dropped onto me." % event)


class PlayerTile(QGroupBox):
    def __init__(self, player, isDealer=False, parent=None):
        print("Creaing tile for {}".format(player))
        super(PlayerTile, self).__init__(parent)
        self.player = player
        self.isDealer = isDealer
        self.widgetLayout = QHBoxLayout(self)
        self.playerLabel = QLabel(self)
        self.widgetLayout.addWidget(self.playerLabel)
        self.playerLabel.setText(self.player)

    # def dragEnterEvent(self, event):
    #     print("{} drag enter".format(self.player))
