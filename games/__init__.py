"""Built-in game definitions and registry bootstrap."""

from importlib import import_module
from pkgutil import iter_modules

from games.registry import registry

_loaded = False


def load_builtin_games() -> None:
    """Import each built-in definition exactly once.

    Definitions register themselves as an import side effect.  Keeping this
    explicit avoids importing Qt widgets while core modules are imported.
    """
    global _loaded
    if _loaded:
        return
    module_names = sorted(
        module.name
        for module in iter_modules(__path__, f"{__name__}.")
        if module.name != "games.registry"
    )
    for module_name in module_names:
        import_module(module_name)
    _loaded = True


__all__ = ["load_builtin_games", "registry"]
