import datetime
import os
import sqlite3 as lite
import sys
from pathlib import Path
from typing import ClassVar

APP_NAME = "Gamelog"


def _project_root() -> Path:
    """Locate the repository root by walking up to the ``pyproject.toml``.

    Anchoring to a project marker keeps the development-database lookup
    independent of where this module lives in the package tree.
    """
    here = Path(__file__).resolve()
    for parent in here.parents:
        if (parent / "pyproject.toml").exists():
            return parent
    # Fallback: repository root relative to this module's current location.
    return here.parents[2]


def _is_android() -> bool:
    # CPython exposes sys.getandroidapilevel() only on Android builds.
    return hasattr(sys, "getandroidapilevel")


def _app_data_dir() -> Path:
    """OS-standard per-user writable data directory for the application.

    Pure-Python equivalent of Qt's ``QStandardPaths.AppDataLocation`` on the
    desktop platforms, so the persistence layer stays free of any Qt import
    there.  Android reports ``sys.platform == "linux"`` but its app sandbox is
    not discoverable from the environment (no usable HOME/XDG paths), so on
    that platform we defer to Qt's writable location.  The Qt import is lazy
    and confined to this branch, which is never taken on desktop, so the
    desktop import path remains Qt-free.
    """
    if _is_android():
        from PySide6.QtCore import QCoreApplication, QStandardPaths

        if not QCoreApplication.applicationName():
            QCoreApplication.setApplicationName(APP_NAME)
        location = QStandardPaths.writableLocation(
            QStandardPaths.StandardLocation.AppDataLocation
        )
        if location:
            return Path(location)
        # Defensive fallback should Qt yield nothing on this device.
        return Path(os.environ.get("HOME", "/data/local/tmp")) / APP_NAME

    if sys.platform.startswith("win"):
        base = os.environ.get("APPDATA") or (Path.home() / "AppData" / "Roaming")
    elif sys.platform == "darwin":
        base = Path.home() / "Library" / "Application Support"
    else:  # Linux / other POSIX
        base = os.environ.get("XDG_DATA_HOME") or (Path.home() / ".local" / "share")
    return Path(base) / APP_NAME


class GameLogDB:
    __shared_state: ClassVar[dict] = {}

    def __init__(self):
        self.__dict__ = self.__shared_state
        self.dbpath = None
        if not hasattr(self, "con"):
            self.con = None

    def getDBLocation(self):
        # First, environment
        dbpath = os.getenv("GAMELOG_DB")
        if dbpath:
            dbpath = Path(dbpath)
            dbdir = dbpath.parent
            try:
                dbdir.mkdir(parents=True, exist_ok=True)
            except OSError as e:
                self._printError(f"Error creating DB: {e.args[0]}")
                sys.exit(1)
            return dbpath

        # Second, load the local development database if exists
        dbpath = _project_root() / "db" / "gamelog.db"
        if dbpath.exists():
            return dbpath

        # Last, for proper native app mode, use standard OS writable location
        data_dir = _app_data_dir()
        try:
            data_dir.mkdir(parents=True, exist_ok=True)
        except OSError as e:
            self._printError(f"Error creating DB: {e.args[0]}")
            sys.exit(1)

        return data_dir / "gamelog.db"

    def connectDB(self, dbpath=None):
        self.disconnectDB()
        if not dbpath:
            dbpath = self.getDBLocation()
        else:
            dbpath = Path(dbpath)
        try:
            print(f"Loading database from {dbpath}")
            self.con = lite.connect(str(dbpath))
            self._checkDB()
        except Exception as e:  # noqa: BLE001
            self._printError(f"Error connecting to DB: {e.args[0]}")
        self.dbpath = dbpath
        db.execute("PRAGMA synchronous=OFF")

    def isConnected(self):
        return self.con is not None

    def disconnectDB(self):
        if self.con:
            self.con.close()
        self.dbpath = None

    def getDBPath(self):
        return self.dbpath

    def execute(self, query, params=()):
        if self.con is None:
            raise RuntimeError("Database not connected")
        try:
            with self.con:
                self.con.row_factory = lite.Row
                cur = self.con.cursor()
                cur.execute(query, params)
                return cur
        except lite.Error as e:
            self._printError(f"Error running query {query}\n {e.args[0]}")
            sys.exit(1)

    def queryDict(self, query, params=()):
        result = []
        for row in self.execute(query, params):
            entry = {}
            for key in row.keys():  # noqa: SIM118
                entry[key] = row[key]
            result.append(entry)
        return result

    def _executeScript(self, script):
        if self.con is None:
            raise RuntimeError("Database not connected")
        try:
            with self.con:
                cur = self.con.cursor()
                cur.executescript(script)
                return cur
        except lite.Error as e:
            self._printError(f"Error running script: {e.args[0]}")
            sys.exit(1)

    def _checkDB(self):
        from core.registry import registry
        from games import load_builtin_games

        load_builtin_games()
        cur = self.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='Game'"
        )
        if not cur.fetchone():
            self._executeScript(_emptydb)
        # Ensure we have all the games we support
        for definition in registry.definitions():
            ge = definition.database_row()
            self.execute(
                'INSERT OR IGNORE INTO "Game" VALUES (?,?,?,?)', ge
            )

    def getAvailableGames(self):
        cur = db.execute("Select name,maxPlayers,description,rules from Game")
        games = {}
        for row in cur:
            games[row["name"]] = {}
            games[row["name"]]["maxPlayers"] = row["maxPlayers"]
            games[row["name"]]["description"] = row["description"]
            games[row["name"]]["rules"] = row["rules"]
        return games

    def getLastGame(self):
        cur = db.execute("Select Game_name from Match order by idMatch desc limit 1")
        if not cur:
            return None
        row = cur.fetchone()
        if not row:
            return None
        return str(row["Game_name"])

    def getPlayerNicks(self):
        cur = db.execute("Select nick from Player order by nick")
        return [row["nick"] for row in cur]

    def getPlayers(self):
        cur = db.execute("Select * from Player order by nick")
        if cur:
            return cur
        return []

    def addPlayer(self, nick, fullname):
        db.execute(
            "INSERT INTO Player(nick,fullName,dateCreation) VALUES(?,?,?)",
            (nick, fullname, str(datetime.datetime.now(tz=datetime.UTC))),
        )

    def isPlayerFavourite(self, nick):
        cur = db.execute(
            "SELECT nick FROM Player WHERE nick=? and favourite=1", (nick,)
        )
        if not cur.fetchone():  # noqa: SIM103
            return False
        else:
            return True

    def setPlayerFavourite(self, nick, isfav):
        flag = 1 if isfav else 0
        db.execute(
            "UPDATE Player SET favourite=? WHERE nick=?", (flag, nick)
        )

    def _printError(self, message):
        # Python 2 syntax
        #         print >> sys.stderr, message
        # Python 3 syntax
        print(message, file=sys.stderr)


db = GameLogDB()

_emptydb = """
DROP TABLE IF EXISTS "AppSettings";
CREATE TABLE `AppSettings` (
  `key` VARCHAR(255) NOT NULL ,
  `type` VARCHAR(45) NOT NULL ,
  `value` TEXT NULL ,
  PRIMARY KEY (`key`) );
DROP TABLE IF EXISTS "Game";
CREATE TABLE `Game` (
  `name` VARCHAR(45) NOT NULL ,
  `maxPlayers` INT NOT NULL ,
  `description` TEXT NULL ,
  `rules` TEXT NULL ,
  PRIMARY KEY (`name`) );
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
