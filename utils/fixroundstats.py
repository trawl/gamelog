#!/usr/bin/env python
# -*- coding: utf-8 -*-

from controllers.db import GameLogDB, db

_mainquery = """
SELECT idMatch,idRound,nick, value AS completed
FROM Match JOIN RoundStatistics USING (idMatch)
WHERE key='PhaseCompleted'
AND Game_name = 'Phase10'
ORDER BY idMatch,idRound,nick;
"""

if __name__ == "__main__":
    db = GameLogDB()
    db.connectDB("../db/gamelog.db")      
    
    currentMatch = 0
    currentRound = 0
    aimed = {}
    result =[]
    
    for row in db.queryDict(_mainquery):
#        print(row)
        if int(row['idMatch']) != currentMatch:
            currentMatch = int(row['idMatch'])
            currentRound = 0
            aimed = {}
            
        if int(row['idRound']) != currentRound: currentRound+=1
                  
        if currentRound == 1: aimed[row['nick']] = 1
            
        result.append([row['idMatch'],row['idRound'],row['nick'],'PhaseAimed',aimed[row['nick']]])
        if row['completed'] != '0':
            aimed[row['nick']] += 1

    insert = "INSERT INTO RoundStatistics (idMatch,idRound,nick,key,value) VALUES ({0[0]},{0[1]},'{0[2]}','{0[3]}','{0[4]}');"
    for row in result:
        stmt = insert.format(row)
        db.execute(stmt)
#        print(stmt)