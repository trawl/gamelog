#!/usr/bin/env bash
# Build the Android APK with pyside6-android-deploy.
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
# Usage: utils/build_android.sh <pyside6 wheel> <shiboken6 wheel>
set -euo pipefail

if [ "$#" -ne 2 ]; then
    echo "usage: $0 <pyside6-android wheel> <shiboken6-android wheel>" >&2
    exit 2
fi

cd "$(dirname "$0")/.."
SPEC="$PWD/pysidedeploy.spec"
ICON="core/resources/icons/cards.png"

rm -f "$SPEC"
pyside6-android-deploy --init --name "Gamelog" \
    --wheel-pyside="$1" --wheel-shiboken="$2" -c "$SPEC"

# Settings the generated spec gets wrong or lacks (add further ones here).
# The tool only bundles the Android platform plugin; the language flags are
# SVGs, which need the SVG image-format and icon-engine plugins as well.
# Plugins are listed twice: copied into the APK ([android] plugins, named
# <dir>_<name>) and loaded at startup ([buildozer] local_libs, plugins_<...>).
sed -i.bak \
    -e "s#^icon = .*#icon = $ICON#" \
    -e "/^\[android\]/,/^\[/ s#^plugins = .*#plugins = platforms_qtforandroid,imageformats_qsvg,iconengines_qsvgicon#" \
    -e "s#^local_libs = .*#local_libs = plugins_platforms_qtforandroid,plugins_imageformats_qsvg,plugins_iconengines_qsvgicon#" \
    "$SPEC"
rm -f "$SPEC.bak"

APP_VERSION="$(sed -n 's/^__version__ = "\(.*\)".*/\1/p' core/_version.py)"
[ -n "$APP_VERSION" ] || { echo "could not read core/_version.py" >&2; exit 1; }
export APP_ORIENTATION=landscape APP_VERSION
pyside6-android-deploy --name "Gamelog" \
    --wheel-pyside="$1" --wheel-shiboken="$2" -c "$SPEC"
