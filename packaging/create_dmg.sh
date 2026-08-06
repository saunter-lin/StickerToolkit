#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
PYTHON_BIN="${PYTHON_BIN:-python3}"
APP_PATH="$PROJECT_ROOT/dist/Sticker Toolkit.app"

fail() {
    echo "錯誤：$1" >&2
    exit 1
}

[[ "$(uname -s)" == "Darwin" ]] || fail "此腳本只能在 macOS 執行。"
[[ -d "$APP_PATH" ]] || fail "找不到 Sticker Toolkit.app，請先執行 build_macos.sh。"

VERSION="$({ PYTHONPATH="$PROJECT_ROOT/src" "$PYTHON_BIN" -c 'from sticker_toolkit.version import __version__; print(__version__.split("-")[0])'; })"
ARCH="$(uname -m)"
[[ "$ARCH" == "arm64" ]] || fail "目前只驗證 arm64 建置，偵測到：$ARCH"

RELEASE_DIR="$PROJECT_ROOT/dist/release"
DMG_PATH="$RELEASE_DIR/StickerToolkit-v${VERSION}-macOS-${ARCH}.dmg"
STAGING_DIR="$(mktemp -d "${TMPDIR:-/tmp}/stickertoolkit-dmg.XXXXXX")"
cleanup() {
    rm -rf "$STAGING_DIR"
}
trap cleanup EXIT

mkdir -p "$RELEASE_DIR"
/usr/bin/ditto "$APP_PATH" "$STAGING_DIR/Sticker Toolkit.app"
ln -s /Applications "$STAGING_DIR/Applications"
/usr/bin/hdiutil create \
    -volname "Sticker Toolkit" \
    -srcfolder "$STAGING_DIR" \
    -ov \
    -format UDZO \
    "$DMG_PATH"
/usr/bin/shasum -a 256 "$DMG_PATH" > "$DMG_PATH.sha256"

echo "DMG 建置完成：$DMG_PATH"
cat "$DMG_PATH.sha256"
