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
                print >> sys.stderr, "Error creating DB: {}".format(e.args[0])
                sys.exit(1)
        try:    
            self.con = lite.connect(dbname)
            self._checkDB()
        except Exception as e:
            print >> sys.stderr, "Error creating DB: {}".format(e.args[0])


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
            print >> sys.stderr, "Error running query {}\n {}".format(query,e.args[0])
            sys.exit(1)
            
    def _executeScript(self,script):
        try:
            with self.con:
                cur = self.con.cursor()
                cur.executescript(script)
                return cur
        except lite.Error as e:
            print >> sys.stderr, "Error running script: {}".format(e.args[0])
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
    
    
    def getPlayerNicks(self):
        cur = db.execute("Select nick from Player order by nick")
        return [ row['nick'] for row in cur ]
    
    def addPlayer(self,nick,fullname):
        db.execute("INSERT INTO Player(nick,fullName,dateCreation) VALUES('{}','{}','{}')".format(nick,fullname,datetime.datetime.now()))
        print("after inserting user to db")
        
        
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
INSERT INTO "GameExtras" VALUES('Phase10','Phase 01','Dos trios');
INSERT INTO "GameExtras" VALUES('Phase10','Phase 02','Un trio y una escalera de cuatro');
INSERT INTO "GameExtras" VALUES('Phase10','Phase 03','Un cuarteto y una escalera de cuatro');
INSERT INTO "GameExtras" VALUES('Phase10','Phase 04','Una escalera de siete');
INSERT INTO "GameExtras" VALUES('Phase10','Phase 05','Una escalera de ocho');
INSERT INTO "GameExtras" VALUES('Phase10','Phase 06','Una escalera de nueve');
INSERT INTO "GameExtras" VALUES('Phase10','Phase 07','Dos cuartetos');
INSERT INTO "GameExtras" VALUES('Phase10','Phase 08','Siete cartas del mismo color');
INSERT INTO "GameExtras" VALUES('Phase10','Phase 09','Un quinteto y una pareja');
INSERT INTO "GameExtras" VALUES('Phase10','Phase 10','Un quinteto y un trio');
INSERT INTO "GameExtras" VALUES('Phase10Master','Phase 01','4 parejas');
INSERT INTO "GameExtras" VALUES('Phase10Master','Phase 02','6 cartas del mismo color');
INSERT INTO "GameExtras" VALUES('Phase10Master','Phase 03','1 Cuarteto y escalera de 4');
INSERT INTO "GameExtras" VALUES('Phase10Master','Phase 04','1 Escalera de 8');
INSERT INTO "GameExtras" VALUES('Phase10Master','Phase 05','7 cartas del mismo color');
INSERT INTO "GameExtras" VALUES('Phase10Master','Phase 06','1 Escalera de 9');
INSERT INTO "GameExtras" VALUES('Phase10Master','Phase 07','2 cuartetos');
INSERT INTO "GameExtras" VALUES('Phase10Master','Phase 08','1 Escalera de 4 del mismo color y 1 trio');
INSERT INTO "GameExtras" VALUES('Phase10Master','Phase 09','1 Quinteto y 1 trio');
INSERT INTO "GameExtras" VALUES('Phase10Master','Phase 10','1 Quinteto y una escalera de 3 cartas de color');
DROP TABLE IF EXISTS "Match";
CREATE TABLE `Match` (
  `idMatch` INTEGER  PRIMARY KEY ,
  `Game_name` VARCHAR(45) NOT NULL ,
  `started` DATETIME NULL ,
  `finished` DATETIME NULL ,
  `state` INTEGER NULL DEFAULT 0,
  CONSTRAINT `fk_Match_Game`
    FOREIGN KEY (`Game_name` )
    REFERENCES `Game` (`name` )
    ON DELETE NO ACTION
    ON UPDATE CASCADE);
DROP TABLE IF EXISTS "MatchPlayer";
CREATE TABLE `MatchPlayer` (
  `idMatch` INTEGER  NOT NULL ,
  `nick` VARCHAR(45) NOT NULL ,
  `totalScore` VARCHAR(45) NOT NULL DEFAULT 0 ,
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