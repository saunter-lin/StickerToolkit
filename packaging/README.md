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

原生 Windows x64 已驗證的建置入口為：

```powershell
py -m venv .venv
.venv\Scripts\python -m pip install -e ".[desktop,build]"
powershell -ExecutionPolicy Bypass -File .\scripts\build_windows.ps1 -Python "C:\path\to\python.exe"
```

專用 spec 位於 `packaging/windows/sticker_toolkit_windows.spec`，版本化 onedir 與 ZIP 位於 `release/windows/`。既有 `packaging/build_windows.ps1` 與跨平台 spec 保留作為簡易／相容建置入口。詳見 [Windows x64 建置說明](../docs/WINDOWS_BUILD.md) 與 [原生驗證清單](WINDOWS_TEST_CHECKLIST.md)。

## 封裝範圍

spec 會包含 PySide6／Qt plugins、Pillow、App Icon 與必要的 runtime 資源；不包含 tests、cache、logs、output、build、dist 或虛擬環境。`build/` 與 `dist/` 均為可重新產生且不提交 Git 的產物。

原始品牌圖位於 `assets/app_icon.png`；封裝專用透明簡化圖位於 `assets/app_icon_packaging.png`，並衍生 `assets/icons/StickerToolkit.icns` 與 `assets/icons/StickerToolkit.ico`。重新建置 Icon 時不得覆蓋原始品牌圖。
