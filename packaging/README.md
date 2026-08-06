# Sticker Toolkit 封裝

版本唯一來源為 `src/sticker_toolkit/version.py`。PyInstaller spec 會從該檔讀取版本，App 名稱固定為 `Sticker Toolkit`，macOS Bundle Identifier 為 `com.saunterlin.stickertoolkit`。

## 安裝建置依賴

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -e '.[desktop,build]'
```

## macOS

```bash
PYTHON_BIN=.venv/bin/python packaging/build_macos.sh
packaging/verify_macos_app.sh
PYTHON_BIN=.venv/bin/python packaging/create_dmg.sh
```

產物為 `dist/Sticker Toolkit.app` 與 `dist/release/StickerToolkit-v<version>-macOS-<arch>.dmg`。目前只在 Apple Silicon `arm64` 驗證。App 未使用 Apple Developer 憑證簽章或公證；首次開啟可能需在 Finder 按右鍵選擇「打開」，或在「系統設定 → 隱私權與安全性」允許。

## Windows

請只在原生 Windows PowerShell 執行：

```powershell
py -m venv .venv
.venv\Scripts\python -m pip install -e ".[desktop,build]"
packaging\build_windows.ps1 -Python .venv\Scripts\python
```

預期 onedir 產物位於 `dist/Sticker Toolkit/`。Windows 正式建置與測試仍須完成 [原生驗證清單](WINDOWS_TEST_CHECKLIST.md)，macOS 不會產生或發布未驗證的 EXE。

## 封裝範圍

spec 會包含 PySide6／Qt plugins、Pillow、App Icon 與必要的 runtime 資源；不包含 tests、cache、logs、output、build、dist 或虛擬環境。`build/` 與 `dist/` 均為可重新產生且不提交 Git 的產物。
