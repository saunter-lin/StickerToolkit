#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
PYTHON_BIN="${PYTHON_BIN:-python3}"
APP_PATH="$PROJECT_ROOT/dist/Sticker Toolkit.app"
PLIST="$APP_PATH/Contents/Info.plist"
BINARY="$APP_PATH/Contents/MacOS/Sticker Toolkit"

fail() {
    echo "錯誤：$1" >&2
    exit 1
}

[[ -d "$APP_PATH" ]] || fail "找不到 App Bundle。"
[[ -f "$PLIST" ]] || fail "找不到 Info.plist。"
[[ -x "$BINARY" ]] || fail "找不到 App 可執行檔。"

BUNDLE_ID="$(/usr/libexec/PlistBuddy -c 'Print :CFBundleIdentifier' "$PLIST")"
SHORT_VERSION="$(/usr/libexec/PlistBuddy -c 'Print :CFBundleShortVersionString' "$PLIST")"
EXPECTED_VERSION="$({ PYTHONPATH="$PROJECT_ROOT/src" "$PYTHON_BIN" -c 'from sticker_toolkit.version import __version__; print(__version__.split("-")[0])'; })"
[[ "$BUNDLE_ID" == "com.saunterlin.stickertoolkit" ]] || fail "Bundle Identifier 不正確：$BUNDLE_ID"
[[ "$SHORT_VERSION" == "$EXPECTED_VERSION" ]] || fail "Bundle 版本不正確：$SHORT_VERSION"
/usr/bin/file "$BINARY" | grep -q "arm64" || fail "可執行檔不是 arm64。"

if find "$APP_PATH/Contents" -type d \( -name tests -o -name .venv -o -name output -o -name __pycache__ \) | grep -q .; then
    fail "App Bundle 包含不應封裝的開發或輸出目錄。"
fi
if strings "$BINARY" | grep -E -q '/Users/[^/]+/Documents/(GitHub|Codex)/'; then
    fail "可執行檔含本機原始碼絕對路徑。"
fi

echo "App Bundle 驗證通過"
echo "Bundle Identifier: $BUNDLE_ID"
echo "Version: $SHORT_VERSION"
/usr/bin/file "$BINARY"
