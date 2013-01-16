#!/usr/bin/env python
# -*- coding: utf-8 -*-

from controllers.db import db

class ResumeEngine():
    
    def __init__(self,game):
        self.game = game
        self.candidates = {}
        
