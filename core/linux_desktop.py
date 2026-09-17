"""Per-user desktop entry so Linux shells can show the application icon.

On Wayland a client cannot hand the compositor a pixmap icon the way X11,
Windows and macOS allow. GNOME resolves the icon shown in the dock and
Activities view by taking the window's app ID (see
``QGuiApplication.setDesktopFileName``) and looking for a matching
``<app-id>.desktop`` in the XDG applications directories. Without one it
shows a generic placeholder.

To keep ``uvx gamelog`` self-contained, the app writes that desktop entry
(and the icon it points to) into the user's XDG data home on start-up. The
write is idempotent and skipped entirely when a system-wide entry already
exists, e.g. from a distribution package.
"""

from __future__ import annotations

import importlib.metadata
import json
import logging
import os
import shutil
import sys
import urllib.parse
import urllib.request
from pathlib import Path

logger = logging.getLogger(__name__)

DESKTOP_ID = "gamelog"
APP_DISPLAY_NAME = "Gamelog"
APP_COMMENT = "Keep track of board and card game scores"
ICON_RESOURCE = ":/icons/cards.png"

_DEFAULT_DATA_DIRS = "/usr/local/share:/usr/share"


def install_desktop_entry() -> Path | None:
    """Ensure the per-user desktop entry exists. No-op off Linux.

    Never raises: any failure is logged and start-up carries on without an
    icon rather than without an application.
    """
    if not sys.platform.startswith("linux"):
        return None
    try:
        return write_desktop_entry()
    except Exception:  # noqa: BLE001 - cosmetic feature; never break start-up
        logger.warning("Could not install the desktop entry", exc_info=True)
        return None


def write_desktop_entry(
    data_home: Path | None = None,
    data_dirs: list[Path] | None = None,
    exec_command: list[str] | None = None,
) -> Path | None:
    """Write ``<data_home>/applications/gamelog.desktop`` and its icon.

    Returns the desktop file path, or ``None`` when a system-wide entry was
    found in ``data_dirs`` and nothing was written. Existing files are only
    rewritten when their content differs, so repeated runs are cheap and do
    not churn modification times.
    """
    data_home = data_home or xdg_data_home()
    data_dirs = data_dirs if data_dirs is not None else xdg_data_dirs()

    for base in data_dirs:
        if (base / "applications" / f"{DESKTOP_ID}.desktop").is_file():
            logger.debug("System desktop entry found under %s; not writing ours", base)
            return None

    # cards.png is 512x512; the directory name must match the pixel size.
    icon_path = (
        data_home / "icons" / "hicolor" / "512x512" / "apps" / f"{DESKTOP_ID}.png"
    )
    _write_if_changed(icon_path, _icon_bytes())

    exec_command = exec_command or default_exec_command()
    desktop_path = data_home / "applications" / f"{DESKTOP_ID}.desktop"
    _write_if_changed(
        desktop_path, render_desktop_entry(exec_command, icon_path).encode()
    )
    return desktop_path


def render_desktop_entry(exec_command: list[str], icon_path: Path) -> str:
    """Return the desktop entry text for the given launch command and icon."""
    exec_line = " ".join(quote_exec_arg(arg) for arg in exec_command)
    return (
        "[Desktop Entry]\n"
        "Type=Application\n"
        "Version=1.5\n"
        f"Name={APP_DISPLAY_NAME}\n"
        f"Comment={APP_COMMENT}\n"
        f"Exec={exec_line}\n"
        # An absolute path side-steps icon-theme cache staleness on first run.
        f"Icon={icon_path}\n"
        "Terminal=false\n"
        "Categories=Game;BoardGame;\n"
        "StartupNotify=true\n"
        # Lets the shell match the window when running under XWayland too.
        f"StartupWMClass={DESKTOP_ID}\n"
    )


def default_exec_command() -> list[str]:
    """Best guess at how to relaunch this very installation.

    In order of preference:

    1. ``uvx --from <source> gamelog`` when we run from uv's ephemeral cache
       (``uvx <url>``): the cached environment may be pruned at any time, so
       point at the source uv fetched it from instead;
    2. the ``gamelog`` console script next to the running interpreter, which
       ``uv tool install`` and pip create in a durable location;
    3. the launcher script we were started from (``uv run gamelog.pyw`` in a
       source checkout, where the project is *not* installed into the venv
       and ``core`` is only importable because Python puts the script's
       directory on ``sys.path``);
    4. ``python -m core`` as a last resort.
    """
    uvx_command = uvx_relaunch_command()
    if uvx_command:
        return uvx_command

    script = Path(sys.executable).with_name(DESKTOP_ID)
    if script.is_file() and os.access(script, os.X_OK):
        return [str(script)]

    launcher = Path(sys.argv[0]).resolve() if sys.argv and sys.argv[0] else None
    if launcher and launcher.suffix in {".py", ".pyw"} and launcher.is_file():
        return [sys.executable, str(launcher)]

    return [sys.executable, "-m", "core"]


def uvx_relaunch_command() -> list[str] | None:
    """``uvx --from <source> gamelog`` if that is how we appear to have started.

    Only applies when the interpreter lives inside uv's cache (the
    environments ``uvx`` builds on the fly), ``uvx`` itself can be found on
    ``PATH`` and the installed package records where it was fetched from.
    Returns ``None`` otherwise so the caller can fall back to a local path.
    """
    if not running_from_uv_cache():
        return None
    uvx = shutil.which("uvx")
    if not uvx:
        return None
    source = installed_from()
    if not source:
        return None
    return [uvx, "--from", source, DESKTOP_ID]


def running_from_uv_cache(
    prefix: Path | None = None, cache_dir: Path | None = None
) -> bool:
    """True when the active environment sits under uv's cache directory."""
    prefix = (prefix or Path(sys.prefix)).resolve()
    cache_dir = (cache_dir or uv_cache_dir()).resolve()
    return prefix.is_relative_to(cache_dir)


def uv_cache_dir() -> Path:
    """Where uv keeps its cache: ``$UV_CACHE_DIR``, else ``$XDG_CACHE_HOME/uv``."""
    env = os.environ.get("UV_CACHE_DIR")
    if env:
        return Path(env)
    xdg = os.environ.get("XDG_CACHE_HOME")
    return (Path(xdg) if xdg else Path.home() / ".cache") / "uv"


def installed_from(dist_name: str = DESKTOP_ID) -> str | None:
    """The source this package was installed from, as a ``uvx --from`` spec.

    Reads the PEP 610 ``direct_url.json`` the installer left in the
    distribution's metadata. A VCS origin becomes ``git+<url>[@<rev>]``, a
    remote archive is returned as-is, a local directory (``uvx /path/to/gl``)
    becomes that path, and an index install with no direct URL yields
    ``None``.
    """
    try:
        raw = importlib.metadata.distribution(dist_name).read_text("direct_url.json")
    except importlib.metadata.PackageNotFoundError:
        return None
    if not raw:
        return None
    return direct_url_to_requirement(json.loads(raw))


def direct_url_to_requirement(info: dict[str, object]) -> str | None:
    """Turn a parsed PEP 610 ``direct_url.json`` into a requirement string."""
    url = info.get("url")
    if not isinstance(url, str) or not url:
        return None

    vcs_info = info.get("vcs_info")
    if isinstance(vcs_info, dict):
        source = f"{vcs_info.get('vcs', 'git')}+{url}"
        rev = vcs_info.get("requested_revision")
        if rev:
            source += f"@{rev}"
        subdirectory = info.get("subdirectory")
        if subdirectory:
            source += f"#subdirectory={subdirectory}"
        return source

    if "archive_info" in info:
        return url

    if "dir_info" in info:
        # uvx accepts a plain directory; turn file:///home/me/gl into /home/me/gl.
        parts = urllib.parse.urlsplit(url)
        if parts.scheme != "file":
            return None
        path = urllib.request.url2pathname(parts.path)
        return path if os.path.isdir(path) else None

    return None


def quote_exec_arg(arg: str) -> str:
    """Quote one ``Exec=`` argument per the Desktop Entry Specification.

    Plain arguments are left alone; anything containing reserved characters
    is wrapped in double quotes with ``\\``, ``"``, `````` and ``$`` escaped.
    """
    reserved = set(" \t\n\"'\\><~|&;$*?#()`")
    if arg and not (reserved & set(arg)):
        return arg
    escaped = (
        arg.replace("\\", "\\\\")
        .replace('"', '\\"')
        .replace("`", "\\`")
        .replace("$", "\\$")
    )
    return f'"{escaped}"'


def xdg_data_home() -> Path:
    """``$XDG_DATA_HOME`` or its spec default, ``~/.local/share``."""
    env = os.environ.get("XDG_DATA_HOME")
    return Path(env) if env else Path.home() / ".local" / "share"


def xdg_data_dirs() -> list[Path]:
    """``$XDG_DATA_DIRS`` or its spec default, split into paths."""
    raw = os.environ.get("XDG_DATA_DIRS") or _DEFAULT_DATA_DIRS
    return [Path(p) for p in raw.split(":") if p]


def _icon_bytes() -> bytes:
    """The application icon, read from the compiled Qt resources."""
    from PySide6.QtCore import QFile, QIODevice

    import core.resources_rc  # noqa: F401 - registers the resource data

    f = QFile(ICON_RESOURCE)
    if not f.open(QIODevice.OpenModeFlag.ReadOnly):
        raise OSError(f"cannot read {ICON_RESOURCE} from the Qt resources")
    try:
        return bytes(f.readAll().data())
    finally:
        f.close()


def _write_if_changed(path: Path, content: bytes) -> bool:
    """Atomically write ``content`` to ``path`` unless it is already there."""
    if path.is_file() and path.read_bytes() == content:
        return False
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_bytes(content)
    os.replace(tmp, path)
    logger.debug("Wrote %s", path)
    return True
