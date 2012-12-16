#!/usr/bin/env python
# -*- coding: utf-8 -*-

import datetime

# Model

class Player:
    def __init__(self):
        self.nick = ""
        self.fullName = ""
        self.dateCreation = None

class Match:
    def __init__(self,players=dict()):
        self.game = None
        self.players = players
        self.winner = None
        self.start = datetime.datetime.now()
        self.finish = None

class Round:
    pass
