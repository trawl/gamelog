#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import os.path
import sqlite3 as lite
import datetime

class GameLogDB:
    __shared_state = {}
    def __init__(self):
        self.__dict__ = self.__shared_state
        if not hasattr(self,'con'):
            self.con=None
    def connectDB(self,dbname='db/gamelog.db'):
        self.disconnectDB()
        dbdir, _ = os.path.split(dbname)
        if not os.path.isdir(dbdir):
            try: 
                os.makedirs(dbdir)
            except os.error as e:
                self._printError("Error creating DB: {}".format(e.args[0]))
                sys.exit(1)
        try:    
            self.con = lite.connect(dbname)
            self._checkDB()
        except Exception as e:
            self._printError("Error creating DB: {}".format(e.args[0]))

    def isConnected(self):
        return self.con is not None

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
        except lite.Error as e:
            self._printError("Error running query {}\n {}".format(query,e.args[0]))
            sys.exit(1)
            
    def queryDict(self,query):
        result=[]
        for row in self.execute(query):
            entry = {}
            for key in row.keys():
                entry[key]=row[key]
            result.append(entry)
        return result
            
    def _executeScript(self,script):
        try:
            with self.con:
                cur = self.con.cursor()
                cur.executescript(script)
                return cur
        except lite.Error as e:
            self._printError("Error running script: {}".format(e.args[0]))
            sys.exit(1)
            
    def _checkDB(self):
        cur = self.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='Game'")
        if not cur.fetchone():
            self._executeScript(_emptydb)
            
    def getAvailableGames(self):
        cur = db.execute("Select name,maxPlayers,description,rules from Game")
        games=dict()
        for row in cur:
            games[row['name']]=dict()
            games[row['name']]['maxPlayers']=row['maxPlayers']
            games[row['name']]['description']=row['description']
            games[row['name']]['rules']=row['rules']
        return games
    
    def getLastGame(self):
        cur = db.execute("Select Game_name from Match order by idMatch desc limit 1")
        row = cur.fetchone()
        if not row: return None
        return str(row['Game_name'])
    
    def getPlayerNicks(self):
        cur = db.execute("Select nick from Player order by nick")
        return [ row['nick'] for row in cur ]
    
    def getPlayers(self):
        cur = db.execute("Select * from Player order by nick")
        return cur
    
    def addPlayer(self,nick,fullname):
        db.execute("INSERT INTO Player(nick,fullName,dateCreation) VALUES('{}','{}','{}')".format(nick,fullname,datetime.datetime.now()))

    def isPlayerFavourite(self,nick):
        cur = db.execute("Select nick from Player where nick='{}' and favourite=1".format(nick))
        if not cur.fetchone(): return False
        else: return True
    
    def setPlayerFavourite(self,nick,isfav):  
        if isfav: flag = 0
        else: flag = 1
        db.execute("UPDATE Player set favourite={} where nick='{}'".format(flag,nick))
           
    def _printError(self,message):
        # Python 2 syntax
        print >> sys.stderr, message
        # Python 3 syntax
#        print(message,file=sys.stderr)
           
           
db = GameLogDB()


_emptydb = """
DROP TABLE IF EXISTS "Game";
CREATE TABLE `Game` (
  `name` VARCHAR(45) NOT NULL ,
  `maxPlayers` INT NOT NULL ,
  `description` TEXT NULL ,
  `rules` TEXT NULL ,
  PRIMARY KEY (`name`) );
INSERT INTO "Game" VALUES('Phase10',6,'Standard Edition','Todos las sabemos ya');
INSERT INTO "Game" VALUES('Phase10Master',6,'Master Edition','El dani las tiene');
INSERT INTO "Game" VALUES('Remigio',12,'Classic Remigio','Home rules');
INSERT INTO "Game" VALUES('Ratuki',5,'Ratuki Slap game','Home rules');
INSERT INTO "Game" VALUES('Carcassonne',6,'Carcassonne board game','Home rules');
DROP TABLE IF EXISTS "GameExtras";
CREATE TABLE `GameExtras` (
  `Game_name` VARCHAR(45) NOT NULL ,
  `key` VARCHAR(45) NOT NULL ,
  `value` VARCHAR(255) NULL ,
  PRIMARY KEY (`Game_name`, `key`) ,
  CONSTRAINT `fk_GameExtras_Game1`
    FOREIGN KEY (`Game_name` )
    REFERENCES `Game` (`name` )
    ON DELETE NO ACTION
    ON UPDATE NO ACTION);
INSERT INTO "GameExtras" VALUES('Phase10','Phase 01','2s3');
INSERT INTO "GameExtras" VALUES('Phase10','Phase 02','1s3 1r4');
INSERT INTO "GameExtras" VALUES('Phase10','Phase 03','1s4 1r4');
INSERT INTO "GameExtras" VALUES('Phase10','Phase 04','1r7');
INSERT INTO "GameExtras" VALUES('Phase10','Phase 05','1r8');
INSERT INTO "GameExtras" VALUES('Phase10','Phase 06','1r9');
INSERT INTO "GameExtras" VALUES('Phase10','Phase 07','2s4');
INSERT INTO "GameExtras" VALUES('Phase10','Phase 08','1c7');
INSERT INTO "GameExtras" VALUES('Phase10','Phase 09','1s5 1s2');
INSERT INTO "GameExtras" VALUES('Phase10','Phase 10','1s5 1s3');
INSERT INTO "GameExtras" VALUES('Phase10Master','Phase 01','4s2');
INSERT INTO "GameExtras" VALUES('Phase10Master','Phase 02','1c6');
INSERT INTO "GameExtras" VALUES('Phase10Master','Phase 03','1s4 1r4');
INSERT INTO "GameExtras" VALUES('Phase10Master','Phase 04','1r8');
INSERT INTO "GameExtras" VALUES('Phase10Master','Phase 05','1c7');
INSERT INTO "GameExtras" VALUES('Phase10Master','Phase 06','1r9');
INSERT INTO "GameExtras" VALUES('Phase10Master','Phase 07','2s4');
INSERT INTO "GameExtras" VALUES('Phase10Master','Phase 08','1cr4 1s3');
INSERT INTO "GameExtras" VALUES('Phase10Master','Phase 09','1s5 1s3');
INSERT INTO "GameExtras" VALUES('Phase10Master','Phase 10','1s5 1cr3');
INSERT INTO "GameExtras" VALUES ('Carcassonne','Kinds','City,Road,Cloister,Field,Goods');
DROP TABLE IF EXISTS "Match";
CREATE TABLE `Match` (
  `idMatch` INTEGER  PRIMARY KEY ,
  `Game_name` VARCHAR(45) NOT NULL ,
  `started` DATETIME NULL ,
  `finished` DATETIME NULL ,
  `state` INTEGER NULL DEFAULT 0,
  `elapsed` INTEGER DEFAULT 0,
  CONSTRAINT `fk_Match_Game`
    FOREIGN KEY (`Game_name` )
    REFERENCES `Game` (`name` )
    ON DELETE NO ACTION
    ON UPDATE CASCADE);
DROP TABLE IF EXISTS "MatchPlayer";
CREATE TABLE `MatchPlayer` (
  `idMatch` INTEGER  NOT NULL ,
  `nick` VARCHAR(45) NOT NULL ,
  `totalScore` INTEGER NOT NULL DEFAULT 0 ,
  `winner` TINYINT(1)  NOT NULL DEFAULT 0 ,
  PRIMARY KEY (`idMatch`, `nick`) ,
  CONSTRAINT `fk_Match_has_Player_Match1`
    FOREIGN KEY (`idMatch` )
    REFERENCES `Match` (`idMatch` )
    ON DELETE NO ACTION
    ON UPDATE NO ACTION,
  CONSTRAINT `fk_Match_has_Player_Player1`
    FOREIGN KEY (`nick` )
    REFERENCES `Player` (`nick` )
    ON DELETE NO ACTION
    ON UPDATE CASCADE);
DROP TABLE IF EXISTS "MatchExtras";    
CREATE TABLE `MatchExtras` (
  `idMatch` INTEGER  NOT NULL ,
  `key` VARCHAR(45) NOT NULL ,
  `value` VARCHAR(255) NULL ,
  PRIMARY KEY (`idMatch`, `key`) ,
    FOREIGN KEY (`idMatch` )
    REFERENCES `Match` (`idMatch` )
    ON DELETE NO ACTION
    ON UPDATE CASCADE);
DROP TABLE IF EXISTS "MatchStatistics";
CREATE TABLE `MatchStatistics` (
  `idMatch` INTEGER  NOT NULL ,
  `nick` VARCHAR(45) NOT NULL ,
  `key` VARCHAR(45) NOT NULL ,
  `value` VARCHAR(255) NULL ,
  PRIMARY KEY (`idMatch`, `nick`, `key`) ,
  CONSTRAINT `fk_MatchStatistics_Match_has_Player1`
    FOREIGN KEY (`idMatch` , `nick` )
    REFERENCES `MatchPlayer` (`idMatch` , `nick` )
    ON DELETE NO ACTION
    ON UPDATE CASCADE);
DROP TABLE IF EXISTS "Player";
CREATE TABLE `Player` (
  `nick` VARCHAR(45) NOT NULL ,
  `fullName` VARCHAR(255) NULL ,
  `dateCreation` DATETIME NULL ,
  "favourite" BOOL NOT NULL  DEFAULT (0) ,
  PRIMARY KEY (`nick`) );
DROP TABLE IF EXISTS "Round";
CREATE TABLE `Round` (
  `idRound` INTEGER  NOT NULL ,
  `idMatch` INTEGER  NOT NULL ,
  `nick` VARCHAR(45) NOT NULL ,
  `winner` TINYINT(1)  NOT NULL DEFAULT 0 ,
  `score` INT NULL ,
  PRIMARY KEY (`idRound`, `idMatch`, `nick`) ,
  CONSTRAINT `fk_RoundPlayer_MatchPlayer1`
    FOREIGN KEY (`idMatch` , `nick` )
    REFERENCES `MatchPlayer` (`idMatch` , `nick` )
    ON DELETE NO ACTION
    ON UPDATE CASCADE);
DROP TABLE IF EXISTS "RoundStatistics";
CREATE TABLE `RoundStatistics` (
  `idMatch` INTEGER  NOT NULL ,
  `nick` VARCHAR(45) NOT NULL ,
  `idRound` INTEGER  NOT NULL ,
  `key` VARCHAR(45) NOT NULL ,
  `value` VARCHAR(255) NULL ,
  PRIMARY KEY (`idMatch`, `nick`, `idRound`, `key`) ,
  CONSTRAINT `fk_RoundStatistics_Round1`
    FOREIGN KEY (`idRound` , `idMatch` , `nick` )
    REFERENCES `Round` (`idRound` , `idMatch` , `nick` )
    ON DELETE NO ACTION
    ON UPDATE CASCADE);
"""