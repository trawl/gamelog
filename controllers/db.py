#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys
import sqlite3 as lite

class GameLogDB:
    __shared_state = {}
    def __init__(self):
        self.__dict__ = self.__shared_state
        if not hasattr(self,'con'):
            self.con=None
    def connectDB(self,dbname='db/gamelog.db'):
        if not self.con:
            self.con = lite.connect(dbname)
            self.con.row_factory = lite.Row
    def disconnectDB(self):
        if self.con:
            self.con.close()
    def execute(self,query):
        try:
            with self.con:
                self.con.row_factory = lite.Row
                cur = self.con.cursor()
                cur.execute(query)
                return cur
        except lite.Error, e:
            print "Error running query {}\n {}".format(query,e.args[0])
            sys.exit(1)

        return None

        
db = GameLogDB()