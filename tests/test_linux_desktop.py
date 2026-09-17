"""Per-user desktop entry written on Linux so the shell can find our icon."""

import struct
import sys
from pathlib import Path

import pytest

from core import linux_desktop
from core.linux_desktop import (
    DESKTOP_ID,
    default_exec_command,
    direct_url_to_requirement,
    install_desktop_entry,
    installed_from,
    quote_exec_arg,
    render_desktop_entry,
    running_from_uv_cache,
    uv_cache_dir,
    write_desktop_entry,
)

PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"


@pytest.fixture
def data_home(tmp_path):
    return tmp_path / "share"


def test_writes_desktop_file_and_icon(data_home, tmp_path):
    path = write_desktop_entry(data_home, data_dirs=[], exec_command=["/opt/gamelog"])

    assert path == data_home / "applications" / f"{DESKTOP_ID}.desktop"
    assert path is not None
    text = path.read_text()
    assert text.startswith("[Desktop Entry]\n")
    assert "Exec=/opt/gamelog\n" in text
    assert f"StartupWMClass={DESKTOP_ID}\n" in text

    icon = data_home / "icons" / "hicolor" / "512x512" / "apps" / f"{DESKTOP_ID}.png"
    assert f"Icon={icon}\n" in text
    data = icon.read_bytes()
    assert data.startswith(PNG_SIGNATURE)
    # IHDR width/height must agree with the hicolor directory name.
    assert struct.unpack(">II", data[16:24]) == (512, 512)


def test_rewrite_is_idempotent(data_home):
    path = write_desktop_entry(data_home, data_dirs=[], exec_command=["/opt/gamelog"])
    assert path is not None
    before = path.stat().st_mtime_ns

    again = write_desktop_entry(data_home, data_dirs=[], exec_command=["/opt/gamelog"])
    assert again == path
    assert path.stat().st_mtime_ns == before
    assert not path.with_name(path.name + ".tmp").exists()


def test_rewrites_when_command_changes(data_home):
    write_desktop_entry(data_home, data_dirs=[], exec_command=["/old/gamelog"])
    path = write_desktop_entry(data_home, data_dirs=[], exec_command=["/new/gamelog"])
    assert path is not None
    assert "Exec=/new/gamelog\n" in path.read_text()


def test_skips_when_system_entry_exists(data_home, tmp_path):
    system = tmp_path / "usr" / "share"
    entry = system / "applications" / f"{DESKTOP_ID}.desktop"
    entry.parent.mkdir(parents=True)
    entry.write_text("[Desktop Entry]\n")

    assert write_desktop_entry(data_home, data_dirs=[system]) is None
    assert not data_home.exists()


def test_exec_arguments_with_spaces_are_quoted():
    text = render_desktop_entry(["/opt/my tools/python", "-m", "core"], Path("/i.png"))
    assert 'Exec="/opt/my tools/python" -m core\n' in text


@pytest.mark.parametrize(
    ("arg", "expected"),
    [
        ("/usr/bin/gamelog", "/usr/bin/gamelog"),
        ("-m", "-m"),
        ("a b", '"a b"'),
        ('say "hi"', '"say \\"hi\\""'),
        ("$HOME", '"\\$HOME"'),
        ("back\\slash", '"back\\\\slash"'),
        ("", '""'),
    ],
)
def test_quote_exec_arg(arg, expected):
    assert quote_exec_arg(arg) == expected


@pytest.fixture
def fake_venv(tmp_path, monkeypatch):
    """A bare interpreter path with no console script and a neutral argv.

    The environment is deliberately outside uv's cache so the uvx branch of
    the launch-command logic stays out of the way unless a test opts in.
    """
    python = tmp_path / "venv" / "bin" / "python"
    python.parent.mkdir(parents=True)
    python.touch()
    monkeypatch.setattr(sys, "executable", str(python))
    monkeypatch.setattr(sys, "prefix", str(python.parent.parent))
    monkeypatch.setattr(sys, "argv", ["pytest"])
    monkeypatch.setenv("UV_CACHE_DIR", str(tmp_path / "uv-cache"))
    return python


GIT_URL = "https://github.ecmwf.int/trawl/gamelog"


def test_exec_uses_uvx_when_running_from_uv_cache(tmp_path, monkeypatch):
    # `uvx <url>`: the interpreter and its console script live in a cached,
    # prunable environment, so relaunch through uvx from the recorded source.
    cache = tmp_path / "uv-cache"
    env = cache / "archive-v0" / "abc123"
    (env / "bin").mkdir(parents=True)
    (env / "bin" / DESKTOP_ID).touch()
    uvx = tmp_path / "bin" / "uvx"
    uvx.parent.mkdir()
    uvx.touch()
    uvx.chmod(0o755)

    monkeypatch.setenv("UV_CACHE_DIR", str(cache))
    monkeypatch.setattr(sys, "prefix", str(env))
    monkeypatch.setattr(sys, "executable", str(env / "bin" / "python"))
    monkeypatch.setenv("PATH", str(uvx.parent))
    monkeypatch.setattr(linux_desktop, "installed_from", lambda: f"git+{GIT_URL}")

    assert default_exec_command() == [str(uvx), "--from", f"git+{GIT_URL}", DESKTOP_ID]


def test_exec_falls_back_to_cached_script_without_uvx(tmp_path, monkeypatch):
    cache = tmp_path / "uv-cache"
    env = cache / "archive-v0" / "abc123"
    (env / "bin").mkdir(parents=True)
    script = env / "bin" / DESKTOP_ID
    script.touch()
    script.chmod(0o755)

    monkeypatch.setenv("UV_CACHE_DIR", str(cache))
    monkeypatch.setattr(sys, "prefix", str(env))
    monkeypatch.setattr(sys, "executable", str(env / "bin" / "python"))
    monkeypatch.setenv("PATH", str(tmp_path / "nowhere"))
    monkeypatch.setattr(linux_desktop, "installed_from", lambda: f"git+{GIT_URL}")

    assert default_exec_command() == [str(script)]


def test_running_from_uv_cache(tmp_path):
    cache = tmp_path / "cache" / "uv"
    assert running_from_uv_cache(cache / "archive-v0" / "x", cache)
    assert not running_from_uv_cache(tmp_path / "venv", cache)
    assert not running_from_uv_cache(cache, cache / "deeper")


def test_uv_cache_dir_precedence(monkeypatch, tmp_path):
    monkeypatch.setenv("UV_CACHE_DIR", str(tmp_path / "explicit"))
    monkeypatch.setenv("XDG_CACHE_HOME", str(tmp_path / "xdg"))
    assert uv_cache_dir() == tmp_path / "explicit"

    monkeypatch.delenv("UV_CACHE_DIR")
    assert uv_cache_dir() == tmp_path / "xdg" / "uv"

    monkeypatch.delenv("XDG_CACHE_HOME")
    assert uv_cache_dir() == Path.home() / ".cache" / "uv"


@pytest.mark.parametrize(
    ("info", "expected"),
    [
        (
            {"url": GIT_URL, "vcs_info": {"vcs": "git", "commit_id": "deadbeef"}},
            f"git+{GIT_URL}",
        ),
        (
            {
                "url": GIT_URL,
                "vcs_info": {"vcs": "git", "requested_revision": "v2.0.0"},
            },
            f"git+{GIT_URL}@v2.0.0",
        ),
        (
            {"url": GIT_URL, "vcs_info": {"vcs": "git"}, "subdirectory": "app"},
            f"git+{GIT_URL}#subdirectory=app",
        ),
        (
            {"url": "https://example.org/gamelog-2.0.0.tar.gz", "archive_info": {}},
            "https://example.org/gamelog-2.0.0.tar.gz",
        ),
        # A local directory that has since disappeared cannot be relaunched.
        ({"url": "file:///nonexistent/gl", "dir_info": {}}, None),
        ({"url": "https://example.org/gl", "dir_info": {}}, None),
        ({}, None),
    ],
)
def test_direct_url_to_requirement(info, expected):
    assert direct_url_to_requirement(info) == expected


def test_direct_url_local_directory_becomes_a_path(tmp_path):
    # `uvx /home/me/projects/gl`: uv records the directory, which uvx can
    # rebuild from, so prefer it over the prunable cached environment.
    checkout = tmp_path / "my projects" / "gl"
    checkout.mkdir(parents=True)
    info = {"url": checkout.as_uri(), "dir_info": {}}
    assert direct_url_to_requirement(info) == str(checkout)


def test_installed_from_reads_dist_metadata(monkeypatch):
    class FakeDist:
        def read_text(self, name):
            assert name == "direct_url.json"
            return f'{{"url": "{GIT_URL}", "vcs_info": {{"vcs": "git"}}}}'

    monkeypatch.setattr(
        linux_desktop.importlib.metadata, "distribution", lambda n: FakeDist()
    )
    assert installed_from() == f"git+{GIT_URL}"


def test_installed_from_without_direct_url(monkeypatch):
    class FakeDist:
        def read_text(self, name):
            return None

    monkeypatch.setattr(
        linux_desktop.importlib.metadata, "distribution", lambda n: FakeDist()
    )
    assert installed_from() is None


def test_installed_from_when_not_installed(monkeypatch):
    def missing(name):
        raise linux_desktop.importlib.metadata.PackageNotFoundError(name)

    monkeypatch.setattr(linux_desktop.importlib.metadata, "distribution", missing)
    assert installed_from() is None


def test_exec_prefers_console_script(fake_venv):
    script = fake_venv.with_name(DESKTOP_ID)
    script.touch()
    script.chmod(0o755)
    assert default_exec_command() == [str(script)]


def test_exec_uses_launcher_script_from_source_checkout(
    fake_venv, tmp_path, monkeypatch
):
    # `uv run gamelog.pyw`: no console script, argv[0] is the .pyw launcher and
    # `core` is only importable thanks to the launcher's directory.
    launcher = tmp_path / "checkout" / "gamelog.pyw"
    launcher.parent.mkdir()
    launcher.touch()
    monkeypatch.chdir(launcher.parent)
    monkeypatch.setattr(sys, "argv", ["gamelog.pyw"])
    assert default_exec_command() == [str(fake_venv), str(launcher.resolve())]


def test_exec_falls_back_to_module(fake_venv):
    assert default_exec_command() == [str(fake_venv), "-m", "core"]


def test_install_is_noop_off_linux(monkeypatch, data_home):
    monkeypatch.setattr(sys, "platform", "darwin")
    monkeypatch.setenv("XDG_DATA_HOME", str(data_home))
    assert install_desktop_entry() is None
    assert not data_home.exists()


def test_install_uses_xdg_env_on_linux(monkeypatch, data_home, tmp_path):
    monkeypatch.setattr(sys, "platform", "linux")
    monkeypatch.setenv("XDG_DATA_HOME", str(data_home))
    monkeypatch.setenv("XDG_DATA_DIRS", str(tmp_path / "empty"))

    path = install_desktop_entry()
    assert path == data_home / "applications" / f"{DESKTOP_ID}.desktop"


def test_install_never_raises(monkeypatch):
    monkeypatch.setattr(sys, "platform", "linux")

    def boom(*a, **k):
        raise OSError("disk full")

    monkeypatch.setattr(linux_desktop, "write_desktop_entry", boom)
    assert install_desktop_entry() is None
