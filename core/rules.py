"""Quick-reference rule sheets: lookup of the bundled Markdown documents.

Each sheet is a ``<doc>_<locale>.md`` file under a game's ``rules/`` folder,
compiled into the resource bundle as ``:/rules/<doc>_<locale>.md``. Lookup
falls back from the exact locale to its language and finally to English, so a
translation can be added later without touching any code.
"""

from __future__ import annotations

from PySide6.QtCore import QFile

DEFAULT_LOCALE = "en_GB"


def candidate_locales(locale: str | None) -> list[str]:
    """Locales to try for ``locale``, most specific first, ending in English."""
    candidates: list[str] = []
    if locale and locale != "C":
        candidates.append(locale)
        language = locale.split("_")[0]
        if language != locale:
            candidates.append(language)
    candidates.append(DEFAULT_LOCALE)
    # Keep order, drop duplicates.
    return list(dict.fromkeys(candidates))


def load_rules(doc: str, locale: str | None = None) -> str | None:
    """Return the Markdown text of ``doc`` for ``locale``, or ``None``."""
    for candidate in candidate_locales(locale):
        file = QFile(f":/rules/{doc}_{candidate}.md")
        if file.open(QFile.OpenModeFlag.ReadOnly):
            try:
                return bytes(file.readAll().data()).decode("utf-8")
            finally:
                file.close()
    return None
