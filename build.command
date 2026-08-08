#!/bin/bash

cd "$(dirname "$0")" || exit 1

pause_on_error() {
  echo
  echo "處理失敗：$1"
  echo "請按任意鍵關閉視窗……"
  read -n 1 -s
  exit 1
}

echo "Sticker Toolkit v1.3.2-dev"
echo "=================="

command -v python3 >/dev/null 2>&1 || pause_on_error "找不到 Python 3。請先從 https://www.python.org/downloads/macos/ 安裝。"

PYTHON="python3"
if [ -x ".venv/bin/python" ] && .venv/bin/python -c "import PIL" >/dev/null 2>&1; then
  PYTHON=".venv/bin/python"
elif ! python3 -c "import PIL" >/dev/null 2>&1; then
  echo "尚未偵測到 Pillow，正在建立本地 .venv 並安裝依賴……"
  python3 -m venv .venv || pause_on_error "無法建立 .venv。"
  .venv/bin/python -m pip install --upgrade pip || pause_on_error "無法更新 pip，請檢查網路連線。"
  .venv/bin/python -m pip install -r requirements.txt || pause_on_error "無法安裝 Pillow，請檢查網路連線。"
  PYTHON=".venv/bin/python"
fi

PYTHONPATH="$PWD/src${PYTHONPATH:+:$PYTHONPATH}" \
  "$PYTHON" -m sticker_toolkit.ui.cli "$@" --interactive --open-preview \
  || pause_on_error "圖片處理未完成，請查看上方錯誤訊息。"

echo
echo "處理成功！"
