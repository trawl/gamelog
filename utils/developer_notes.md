# Developer notes

# Installing the necessary environment
The easiest strategy is with [uv](https://docs.astral.sh/uv/getting-started/installation/). Once you have installed it, from the main project directory:

```
uv run gamelog.pyw
```
This will automatically create a local python venv under .venv with the necessary dependencies.

## I18N support
Whenever there has been some change in the code that includes translatable text, you need to follow these steps to incorporate it to the application:

1. Update the language files from the code:
```
pyside6-lupdate gui/* controllers/* -ts i18n/*.ts
```

2. Use Linguist to provide the necessary translations:
```
pyside6-linguist i18n/*.ts &
```

3. From Linguist, click save all, then release all.

4. Refresh resources as explained below
```
pyside6-rcc resources.qrc -o  resources_rc.py
```

## Resources (Style an icons) changex
Any changes on the resources used by the application need to be recompiled into the resources_rc.py. That includes changing or adding icons, as well as any modifications to the stylesheets(qss).

1. If adding a new file, make sure it is present in `resources.qrc`.
2. Update resources with:
```
pyside6-rcc resources.qrc -o  resources_rc.py
```
