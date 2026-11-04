#!/usr/bin/env bash
# Build the Android APK with pyside6-android-deploy.
#
# The PySide6 and shiboken6 Android wheels are downloaded from download.qt.io
# on first use and cached (checksum-verified), so no arguments are needed.
# The APK lands in dist/.
#
# The tool generates pysidedeploy.spec (machine-specific paths, default .icns
# icon buildozer cannot use) and buildozer.spec, and exposes no orientation
# option. So: regenerate the spec each time with --init, pin our settings
# into it, then build from that spec with -c.
#
# Orientation and version: buildozer lets SECTION_KEY environment variables
# override any spec value, so APP_ORIENTATION forces landscape and APP_VERSION
# (read from core/_version.py, which release-please bumps) replaces the
# template's default 0.1.
#
# python-for-android patches to the Qt bootstrap's PythonActivity:
#  - onActivityResult never calls super.onActivityResult, so Qt never hears
#    back from any Android activity it starts, such as the system file picker
#    behind QFileDialog (the app freezes with the dialog still "open");
#  - onKeyDown treated every key as Back, swallowing keyboard input (upstream
#    fixed it in kivy/python-for-android#3376, after the tool's pinned commit);
#  - the system bars and the window behind them are coloured to the system's
#    light/dark mode (utils/android/system_bars.java.snippet).
# Buildozer clones p4a at the tool's
# pinned commit, so we keep a local copy with the missing super call committed
# on top and make buildozer clone and reset to that instead.
#
# Usage: utils/build_android.sh
# Environment overrides:
#   PYSIDE_ANDROID_VERSION  wheel version      (default: 6.12.0)
#   PYSIDE_ANDROID_TAG      wheel python tag   (default: cp310-abi3; 6.11.x and
#                           older are cp311-cp311)
#   ANDROID_WHEEL_CACHE     download cache dir (default: ~/.cache/gamelog/android-wheels)
set -euo pipefail

VERSION="${PYSIDE_ANDROID_VERSION:-6.12.0}"
TAG="${PYSIDE_ANDROID_TAG:-cp310-abi3}"
CACHE="${ANDROID_WHEEL_CACHE:-${XDG_CACHE_HOME:-$HOME/.cache}/gamelog/android-wheels}"
BASE_URL="https://download.qt.io/official_releases/QtForPython"

cd "$(dirname "$0")/.."
SPEC="$PWD/pysidedeploy.spec"
ICON="core/resources/icons/cards.png"
DIST="dist"

# fetch_wheel <pyside6|shiboken6>: download into the cache if absent, verify
# its published sha256, and print the cached path.
fetch_wheel() {
    local name="$1"
    local file="$name-$VERSION-$VERSION-$TAG-android_aarch64.whl"
    local url="$BASE_URL/$name/$file"
    mkdir -p "$CACHE"
    if [ ! -f "$CACHE/$file" ]; then
        echo "Downloading $file" >&2
        curl -fL --retry 3 --progress-bar -o "$CACHE/$file.part" "$url"
        curl -fsSL --retry 3 -o "$CACHE/$file.sha256" "$url.sha256"
        local expected actual
        expected="$(cut -d' ' -f1 "$CACHE/$file.sha256")"
        actual="$(shasum -a 256 "$CACHE/$file.part" | cut -d' ' -f1)"
        if [ "$expected" != "$actual" ]; then
            rm -f "$CACHE/$file.part" "$CACHE/$file.sha256"
            echo "checksum mismatch for $file" >&2
            exit 1
        fi
        mv "$CACHE/$file.part" "$CACHE/$file"
    fi
    echo "$CACHE/$file"
}

# prepare_patched_p4a: keep a local copy of python-for-android whose `master`
# is the pinned commit plus the patch above, and make git serve buildozer's
# clone of the upstream URL from it (git's url.<base>.insteadOf, set through
# the environment so no git config is touched). The tool wipes .buildozer at
# the start of every run, so a pre-seeded checkout there would not survive.
# APP_P4A_COMMIT then makes buildozer reset to the patched commit.
prepare_patched_p4a() {
    local tool python source branch commit
    tool="$(command -v pyside6-android-deploy)"
    python="$(head -n 1 "$tool" | sed 's/^#!//')"
    # The tool pins the p4a commit it was tested with; read it from its source.
    source="$("$python" -c 'import os, PySide6; print(os.path.join(os.path.dirname(PySide6.__file__), "scripts/deploy_lib/android/buildozer.py"))')"
    branch="$(sed -n 's/^P4A_BRANCH = "\(.*\)"/\1/p' "$source")"
    commit="$(sed -n 's/^P4A_COMMIT = "\(.*\)"/\1/p' "$source")"
    if [ -z "$branch" ] || [ -z "$commit" ]; then
        echo "could not read the pinned python-for-android commit from $source" >&2
        exit 1
    fi

    local p4a_cache="${XDG_CACHE_HOME:-$HOME/.cache}/gamelog/python-for-android"
    local url="https://github.com/kivy/python-for-android.git"
    if [ ! -d "$p4a_cache" ]; then
        echo "Cloning python-for-android" >&2
        git clone -q -b "$branch" --single-branch "$url" "$p4a_cache"
    fi
    git -C "$p4a_cache" cat-file -e "$commit^{commit}" 2>/dev/null \
        || git -C "$p4a_cache" fetch -q origin "$branch"

    # Start from the pinned upstream commit every time, then add the patch.
    git -C "$p4a_cache" checkout -q -B "$branch" "$commit"
    local java="$p4a_cache/pythonforandroid/bootstraps/qt/build/src/main/java/org/kivy/android/PythonActivity.java"
    sed -i.bak '/protected void onActivityResult(int requestCode, int resultCode, Intent intent) {/a\
        super.onActivityResult(requestCode, resultCode, intent);
' "$java"
    rm -f "$java.bak"
    # Upstream kivy/python-for-android#3376: only the Back key may trigger the
    # "Click again to close the app" toast; every other key was swallowed by it.
    sed -i.bak '/public boolean onKeyDown(int keyCode, KeyEvent event) {/a\
        if (keyCode != KeyEvent.KEYCODE_BACK) {\
            return super.onKeyDown(keyCode, event);\
        }
' "$java"
    rm -f "$java.bak"
    # Dark/light system bars matching the app's palette (see the snippet).
    sed -i.bak -e '/Log.v(TAG, "Did super onCreate");/r utils/android/system_bars.java.snippet' "$java"
    rm -f "$java.bak"
    grep -q "super.onActivityResult" "$java" \
        && grep -q "keyCode != KeyEvent.KEYCODE_BACK" "$java" \
        && grep -q "setNavigationBarColor" "$java" \
        || { echo "could not patch $java" >&2; exit 1; }
    git -C "$p4a_cache" -c user.name=gamelog -c user.email=gamelog@localhost \
        commit -q -am "qt bootstrap: forward onActivityResult, only Back closes, dark bars"

    APP_P4A_COMMIT="$(git -C "$p4a_cache" rev-parse HEAD)"
    export APP_P4A_COMMIT
    export GIT_CONFIG_COUNT=1
    export GIT_CONFIG_KEY_0="url.file://$p4a_cache.insteadOf"
    export GIT_CONFIG_VALUE_0="$url"
}

PYSIDE_WHEEL="$(fetch_wheel pyside6)"
SHIBOKEN_WHEEL="$(fetch_wheel shiboken6)"

rm -f "$SPEC"
pyside6-android-deploy --init --name "Gamelog" \
    --wheel-pyside="$PYSIDE_WHEEL" --wheel-shiboken="$SHIBOKEN_WHEEL" -c "$SPEC"

# Settings the generated spec gets wrong or lacks (add further ones here).
# The tool only bundles the Android platform plugin; the language flags are
# SVGs, which need the SVG image-format and icon-engine plugins as well.
# Plugins are listed twice: copied into the APK ([android] plugins, named
# <dir>_<name>) and loaded at startup ([buildozer] local_libs, plugins_<...>).
# exec_directory is where the finished APK is written.
mkdir -p "$DIST"
sed -i.bak \
    -e "s#^icon = .*#icon = $ICON#" \
    -e "s#^exec_directory = .*#exec_directory = $DIST#" \
    -e "/^\[android\]/,/^\[/ s#^plugins = .*#plugins = platforms_qtforandroid,imageformats_qsvg,iconengines_qsvgicon#" \
    -e "s#^local_libs = .*#local_libs = plugins_platforms_qtforandroid,plugins_imageformats_qsvg,plugins_iconengines_qsvgicon#" \
    "$SPEC"
rm -f "$SPEC.bak"

APP_VERSION="$(sed -n 's/^__version__ = "\(.*\)".*/\1/p' core/_version.py)"
[ -n "$APP_VERSION" ] || { echo "could not read core/_version.py" >&2; exit 1; }
export APP_ORIENTATION=landscape APP_VERSION
prepare_patched_p4a
pyside6-android-deploy --name "Gamelog" \
    --wheel-pyside="$PYSIDE_WHEEL" --wheel-shiboken="$SHIBOKEN_WHEEL" -c "$SPEC"

echo "APK(s) in $DIST/:"
ls -1 "$DIST"
