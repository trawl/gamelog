#!/usr/bin/env python
# -*- coding: utf-8 -*-
from PySide6.QtWidgets import (
    QApplication,
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
        self.setWindowTitle(QApplication.translate("PlayerOrderDialog", "Player Order"))
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

    def dropEvent(self, event):
        print("'%s' was dropped onto me." % event)


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

    def dragEnterEvent(self, event):
        print("{} drag enter".format(self.player))


if __name__ == "__main__":
    import sys

    from controllers.db import db
    from controllers.enginefactory import GameEngineFactory

    db.connectDB()
    app = QApplication(sys.argv)
    engine = GameEngineFactory.createMatch("Pocha")
    players = ["Xavi", "Rosa", "Dani"]
    for p in players:
        engine.addPlayer(p)
    engine.begin()
    mw = PlayerOrderDialog(engine)
    mw.show()
    sys.exit(app.exec_())
