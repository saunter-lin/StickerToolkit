#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
PYTHON_BIN="${PYTHON_BIN:-python3}"

fail() {
    echo "錯誤：$1" >&2
    exit 1
}

[[ "$(uname -s)" == "Darwin" ]] || fail "此腳本只能在 macOS 執行。"
cd "$PROJECT_ROOT"
"$PYTHON_BIN" -c "import PyInstaller" >/dev/null 2>&1 || fail "尚未安裝 PyInstaller，請先安裝 .[desktop,build]。"
[[ -f assets/icons/StickerToolkit.icns ]] || fail "找不到 macOS App Icon。"
[[ -f packaging/StickerToolkit.spec ]] || fail "找不到 PyInstaller spec。"

rm -rf build/pyinstaller "dist/Sticker Toolkit" "dist/Sticker Toolkit.app"
"$PYTHON_BIN" -m PyInstaller \
    --clean \
    --noconfirm \
    --distpath dist \
    --workpath build/pyinstaller \
    packaging/StickerToolkit.spec

APP_PATH="dist/Sticker Toolkit.app"
[[ -d "$APP_PATH" ]] || fail "建置完成但找不到 Sticker Toolkit.app。"
[[ -x "$APP_PATH/Contents/MacOS/Sticker Toolkit" ]] || fail "App Bundle 內缺少可執行檔。"
echo "macOS App 建置完成：$APP_PATH"
