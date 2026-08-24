import os
import re

from PySide6.QtCore import QCoreApplication

from controllers.db import db

QCoreApplication.translate("AppSettings", "symbols")
QCoreApplication.translate("AppSettings", "text")
QCoreApplication.translate("AppSettings", "system")
QCoreApplication.translate("AppSettings", "light")
QCoreApplication.translate("AppSettings", "dark")
QCoreApplication.translate("AppSettings", "en_GB")
QCoreApplication.translate("AppSettings", "es_ES")
QCoreApplication.translate("AppSettings", "ca_ES")

default_settings = {
    "text_in_buttons": {
        "value": False,
        "type": "bool",
        "displayname": QCoreApplication.translate(
            "AppSettings", "Show text in buttons"
        ),
        "description": QCoreApplication.translate(
            "AppSettings", "Use text or symbols in buttons"
        ),
        "choices": ["symbols", "text"],
    },
    "language": {
        "value": "system",
        "type": "str",
        "displayname": QCoreApplication.translate("AppSettings", "Language"),
        "description": QCoreApplication.translate(
            "AppSettings", "Application language"
        ),
        "choices": ["system", "en_GB", "es_ES", "ca_ES"],
    },
    "theme": {
        "value": "system",
        "type": "str",
        "choices": [
            "system",
            "light",
            "dark",
        ],
        "displayname": QCoreApplication.translate(
            "AppSettings",
            "Theme",
        ),
        "description": QCoreApplication.translate(
            "AppSettings",
            "Application appearance",
        ),
    },
}


class AppSettings:
    # textInButtons = False
    def __init__(self):
        self.settings = {"db": {}, "env": {}, "defaults": default_settings}
        if not db.isConnected():
            db.connectDB()
        self.dbseed()
        self.refresh()

    def flush(self):
        for k, d in self.settings["db"].items():
            db.execute(
                f"INSERT OR REPLACE INTO `AppSettings`(`key`, `value`, `type`, `displayname`, `description`) VALUES ('{k}', '{d['value']}', '{d['type']}','{d['displayname']}', '{d['description']}') "
            )

    def refresh(self):
        self.loadFromEnv()
        self.loadFromDB()

    def loadFromEnv(self):
        for var, value in os.environ.items():
            m = re.match(r"GAMELOG_(\w)+", var)
            if m:
                key = m.groups()
                self.settings["env"][key] = value

    def loadFromDB(self):
        cur = db.execute("SELECT key,value,type FROM AppSettings")
        for row in cur:
            key = row["key"]
            value = row["value"]
            try:
                type = default_settings[row["key"]]["type"]
                if row["type"] in ("int", "float", "bool"):
                    if type == "int":
                        value = int(value)
                    elif type == "float":
                        value = float(value)
                    elif type == "bool":
                        value = value.lower() in ("true", "1", "y", "yes")
                self.settings["db"][key] = value
            except KeyError:
                raise Warning(f"Could not load unknown setting {key}")

    def __getitem__(self, name: str, /):
        return self.get(name)

    def get(self, key):
        try:
            return self.settings["env"][key]
        except KeyError:
            try:
                return self.settings["db"][key]
            except KeyError:
                return None

    def getSettings(self):
        return self.settings

    def set(self, key, value, persistent=True):
        if persistent:
            self.settings["db"][key] = value
            db.execute(f"UPDATE `AppSettings` SET `value`='{value}' WHERE key='{key}'")
        else:
            self.settings["env"][key] = value

    def dbseed(self):
        cur = db.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='AppSettings'"
        )
        if not cur.fetchone():
            db.execute("""CREATE TABLE `AppSettings` (
            `key` VARCHAR(255) NOT NULL ,
            `value` TEXT NULL ,
            `type` VARCHAR(45) NOT NULL ,
            PRIMARY KEY (`key`) );""")

        for k, d in default_settings.items():
            cur = db.execute(f"SELECT `key` FROM `AppSettings` WHERE `key`= '{k}'")
            if not cur.fetchone():
                value = "NULL" if d["value"] is None else f"'{d['value']}'"
                db.execute(
                    f"INSERT OR REPLACE INTO `AppSettings`(`key`, `value`, `type`) VALUES ('{k}', {value}, '{d['type']}') "
                )


appsettings = AppSettings()
