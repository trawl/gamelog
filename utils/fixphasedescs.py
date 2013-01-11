#!/usr/bin/env python
# -*- coding: utf-8 -*-

from controllers.db import GameLogDB, db

_mainquery = """UPDATE GameExtras SET value='{2}' WHERE Game_name='{0}' AND key='{1}';"""

if __name__ == "__main__":
    db = GameLogDB()
    db.connectDB("../db/gamelog.db")      
    
    phases = {
    'Phase10' : ['2s3','1s3 1r4','1s4 1r4','1r7','1r8','1r9','2s4','1c7','1s5 1s2','1s5 1s3'],
    'Phase10Master' : ['4s2','1c6','1s4 1r4','1r8','1c7','1r9','2s4','1cr4 1s3','1s5 1s3','1s5 1cr3']
    }

    for game,phases in phases.items():
        for i, phase in enumerate(phases,start=1):
            key = "Phase {0:02}".format(i)
            query = _mainquery.format(game,key,phase)
            print (query)
            db.execute(query)
            
    db.disconnectDB()