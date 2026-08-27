# Developer notes

# Installing the necessary environment
The easiest strategy is with [uv](https://docs.astral.sh/uv/getting-started/installation/). Once you have installed it, from the main project directory:

```
uv run gamelog.pyw
```
This will automatically create a local python venv under .venv with the necessary dependencies.

## I18N support
Translations are **split by unit**: framework strings live in
`core/resources/i18n/core_<locale>.ts`, and each game owns
`games/<name>/i18n/<name>_<locale>.ts`. A string is assigned to a unit by the
source file it appears in, so a game's translations travel with the game.

Whenever code with translatable text changes:

1. Sync and compile every catalogue (`lupdate` + `lrelease` per unit):
```
python utils/build_translations.py
```

2. Translate any new (unfinished) strings with Linguist, then re-run the
   command above to recompile:
```
pyside6-linguist core/resources/i18n/core_*.ts games/*/i18n/*.ts &
```

3. Refresh the resource bundle as explained below.

## Resources (styles, icons, translations)
Resources are **auto-discovered** and compiled into `resources_rc.py`. You never
edit `resources.qrc` by hand — it is generated. After adding, changing, or
removing any icon, stylesheet, or compiled translation (`.qm`), run:

```
python utils/build_resources.py
```

This scans the resource folders, regenerates `resources.qrc`, and compiles it
with `pyside6-rcc`.

### Where resources live
* **Shared / framework-wide:** `core/resources/{icons,styles,i18n}`
* **Per-game:** `games/<name>/{icons,styles,i18n}` — a game folder can carry its
  own assets, so adding a game needs no changes elsewhere.

Every file is exposed under a flat alias regardless of where it lives:
`:/icons/<name>`, `:/styles/<name>`, `:/i18n/<name>`. Because the namespace is
flat, **file names must be unique across all games** (the build script errors on
a collision).

### Per-game stylesheets
A game may ship an optional stylesheet that is layered on top of the global
theme, scoped to that game's widget:

* `games/<name>/styles/<name>.qss` — applied for any theme, or
* `games/<name>/styles/<name>.light.qss` / `<name>.dark.qss` — theme-specific
  (preferred over the plain file when present).

`<name>` is the game's package directory name. The stylesheet is applied
automatically when the game's board is opened and re-applied on theme changes.
