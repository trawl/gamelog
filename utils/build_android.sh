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
pyside6-android-deploy --name "Gamelog" \
    --wheel-pyside="$PYSIDE_WHEEL" --wheel-shiboken="$SHIBOKEN_WHEEL" -c "$SPEC"

echo "APK(s) in $DIST/:"
ls -1 "$DIST"
