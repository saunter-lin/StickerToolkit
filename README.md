# Sticker Toolkit v1.3.2（macOS／Windows）

Sticker Toolkit 將一張規則排列的 4×4 貼圖合集切成 16 張，經過共用的 Trim、等比例縮放與 Safe Margin 管線後，可輸出 LINE、WeChat，或同時輸出兩種平台套件。程式不依靠合集檔名判斷來源。

版本演進與相容性修正請參閱 [CHANGELOG.md](CHANGELOG.md)。目前版本為 v1.3.2；正式安裝包將於雙平台封裝驗證完成後發布。

## 支援平台

| 平台 | 架構 | 發布格式 | 狀態 |
| --- | --- | --- | --- |
| macOS | Apple Silicon（arm64） | DMG | ✅ 正式支援 |
| Windows 10／11 | x64 | onedir ZIP | ✅ 正式支援 |

正式安裝包與 SHA-256 校驗檔請從 [GitHub Releases](https://github.com/saunter-lin/StickerToolkit/releases) 下載。

## Quick Start

一般使用者不需要安裝 Python、pip 或建立 virtual environment，直接從 [GitHub Releases](https://github.com/saunter-lin/StickerToolkit/releases) 下載對應平台的正式版本即可。

### macOS（Apple Silicon）

1. 下載 `StickerToolkit-v1.3.1-macOS-arm64.dmg`。
2. 開啟 DMG，將 `Sticker Toolkit.app` 拖曳至 `Applications`。
3. 從「應用程式」啟動 Sticker Toolkit。

App 目前未使用 Apple Developer 簽章或公證；若 Gatekeeper 阻擋，請在 Finder 對 App 按右鍵選擇「打開」，再確認開啟，或前往「系統設定 → 隱私權與安全性」允許。

### Windows x64

1. 下載 Windows x64 onedir ZIP。
2. 完整解壓縮 ZIP，保留整個資料夾結構。
3. 執行解壓縮資料夾內的 `StickerToolkit.exe`。

請勿直接從 ZIP 內執行，也不要只複製或單獨散布 `StickerToolkit.exe`。

### Windows Security Notice

Windows 版本目前未使用 Microsoft Code Signing Certificate，因此第一次執行時可能會出現 Microsoft Defender SmartScreen。這不代表程式含有病毒，而是 Windows 對尚未建立信譽的未簽章程式所採用的正常保護機制。Sticker Toolkit 是開源專案，建議僅從本專案的 GitHub Release 下載；Release 同時提供 `SHA256SUMS.txt`，可用來驗證下載檔案的完整性。

若出現 `Windows protected your PC`：

1. 按下 `More info`（更多資訊）。
2. 再按 `Run anyway`（仍要執行）。

未來若專案採用 Windows Code Signing Certificate，此提示可能會逐漸消失。

## 功能

- 支援 `.png`、`.jpg`、`.jpeg` 4×4 貼圖合集
- 一次執行 Split → Trim → Safe Margin，各平台輸出器共用 16 張處理結果
- 移除透明空白或與邊界相連的近白背景
- 保持比例、透明背景、置中及安全留白
- LINE：自選 `main.png`、`tab.png`，規格驗證、Preview 與 ZIP
- WeChat：8～24 張素材驗證、240×240 貼圖、Banner、封面、panel icon、Preview 與 ZIP
- 可選 LINE、WeChat 或兩者一起輸出
- Banner 僅執行 Resize → Center → Contain，不切割、不拉伸、不使用 AI 或 API
- 中文錯誤訊息涵蓋解碼、切割、透明內容、Banner、PNG 驗證與 ZIP 寫入
- v1.3.1：可在切割前將與畫布外部連通的固定純色背景轉為透明 Alpha
- v1.3.2：新增 WeChat 批次單圖模式，可直接依 GUI 順序處理 16 張 PNG／JPG
- LINE main 與 WeChat cover 可維持自動產生，或選用自訂 PNG／JPG／JPEG 封面

### WeChat 批次單圖（v1.3.2）

桌面版可直接選擇 16 張獨立 PNG／JPG／JPEG，依清單順序上移或下移後，批次套用既有背景透明化與 Normalize 管線，再交由同一套 WeChat exporter 輸出 `01.png`～`16.png`、Banner、cover、panel icon、Preview 與 ZIP。此模式適合逐張 AI 生圖工作流，且必須另外選擇 Banner；輸出素材目錄使用 `{banner_stem}_wechat_sticker`。

LINE 與 WeChat 封面預設仍為自動產生；需要時可切換為自選圖片，程式會等比例 fit 至既有平台規格，不會拉伸。

## 輸出內容

### LINE

- `line_sticker/01.png`～`16.png`：370×320 px RGBA PNG
- `line_sticker/main.png`：240×240 px RGBA PNG
- `line_sticker/tab.png`：96×74 px RGBA PNG
- `output/preview/line/preview.png`：LINE 專屬總覽，包含 16 張、main、tab 與驗證
- `line_sticker.zip`：唯一的 LINE ZIP 套件，不產生重複副本

### WeChat

- `output/preview/wechat/wechat_preview.png`：WeChat 專屬總覽，顯示貼圖、Banner、cover、panel icon、ZIP 內容與驗證結果
- `wechat_sticker.zip`：唯一的 WeChat ZIP，結構如下：

```text
wechat_sticker.zip
├── 01.png                  # 240×240，最多 500KB
├── ...
├── 16.png
├── banner.png              # 750×400，最多 500KB；未提供時省略
├── cover.png               # 240×240 PNG，最多 500KB
└── panel_icon.png          # 50×50 PNG，最多 100KB
```

WeChat ZIP 不包含 `manifest.json` 或其他 JSON。貼圖數量驗證接受 8～24 張；目前 4×4 UI 仍預設產生 16 張。若缺少 Banner，仍會匯出貼圖、cover 與 panel icon 供檢查，但 Preview 會顯示「微信素材尚未完整，可能無法直接提交。」

### 輸出與 Preview 目錄

```text
output/
├── line_sticker/
├── wechat_sticker/
├── preview/
│   ├── line/
│   │   ├── selection.png
│   │   └── preview.png
│   └── wechat/
│       ├── selection.png
│       └── wechat_preview.png
├── line_sticker.zip
└── wechat_sticker.zip
```

重新輸出 LINE 只會重建 `output/line_sticker/`、`output/line_sticker.zip` 與 `output/preview/line/`；重新輸出 WeChat 同理，不會刪除另一平台的結果。所有生成內容都位於 `output/`，直接刪除該目錄即可完整清理。若偵測到 v1.2.2 遺留的專案根目錄 `preview/`，程式會在執行時安全移除。

### WeChat 素材最佳化

所有 PNG 先以 RGBA、`optimize=True` 與最高壓縮等級輸出。若仍超過上限，依序嘗試 256、128、64、32 色的最佳化 PNG；仍超限時停止匯出並顯示中文錯誤，不會把超規素材標示為成功。

### 純色背景轉透明（v1.3.1）

Sticker Toolkit 可在切割 4×4 合集前，從畫布邊界開始，只將與外部連通的指定純色轉為透明。這不是 AI 去背，最適合固定純色、無漸層、無陰影、無紋理的背景。

推薦 AI 生圖時使用純色淺米黃色背景，例如 `#FFF8EC`，背景僅作為後續自動去背使用。功能預設關閉；啟用後預設自動偵測背景色，容差維持為 `3`。純色 PNG 建議使用 `3～5`；JPEG 或有壓縮色差的圖片可提高至 `10～15`。數值越高越可能影響淺色細節。複雜背景不保證效果；若原圖已是真正透明 PNG，無需啟用。

AI 貼圖合集建議：

- `#FFF8EC` 是推薦值，不是強制值；程式也可自動偵測其他平坦純色背景。
- 背景應為單一純色，避免漸層、陰影、紋理或複雜背景。
- 建議在角色與貼圖內容周圍加入白色描邊，並以清楚的 4×4 格線分隔 16 張貼圖。
- 優先使用 PNG；純色 PNG tolerance 建議 `3–5`。
- JPEG 可能產生背景色差，tolerance 建議 `10–15`，可從 `12` 開始嘗試。

可直接提供給 AI 生圖的 Prompt 範例：

```text
Use a solid light cream background (#FFF8EC), with no gradients, shadows, or textures. The background is intended for automatic removal. Add a white outline around each sticker and clearly separate all stickers in a 4×4 grid.
```

## Development

以下內容僅供開發者、Contributor，以及需要自行修改原始碼的使用者。一般使用者請直接從 [GitHub Releases](https://github.com/saunter-lin/StickerToolkit/releases) 下載 macOS DMG 或 Windows x64 ZIP。

### 從原始碼啟動桌面介面

先安裝桌面版選用相依套件：

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -e '.[desktop]'
```

從專案根目錄啟動：

```bash
PYTHONPATH=src .venv/bin/python -m sticker_toolkit.ui.desktop
```

桌面版可選擇整合圖或 WeChat 批次單圖、LINE／微信／兩者、微信 Banner、自動或自選封面與輸出目錄；支援背景處理、真實進度、錯誤提示、結果摘要及跨平台開啟輸出資料夾。圖片處理全部交由 `StickerService` 執行，視窗不包含圖片演算法。

![Sticker Toolkit v1.3.0 Desktop GUI](docs/images/sticker-toolkit-v1.3.png)

選擇來源圖片後，Desktop 會建議同層的 `<來源檔名>_output` 作為輸出根目錄，例如 `berry.png` 對應 `berry_output/`。手動指定的輸出位置具有優先權，建議位置不可寫時會在開始處理前顯示錯誤，不會改用系統暫存目錄。

- macOS Log：`~/Library/Logs/StickerToolkit/sticker_toolkit.log`
- Windows Log：`%LOCALAPPDATA%/StickerToolkit/Logs/sticker_toolkit.log`

### 開發者操作與技術參考

#### 使用 input 資料夾

1. 將貼圖合集放入 `input/`。
2. 選用：將任意檔名的橫向 PNG Banner 放在同一資料夾。
3. 雙擊 `build.command`。若 macOS 阻擋，請在 Finder 對檔案按右鍵並選擇「打開」。
4. 選擇 LINE、WeChat 或同時輸出。
5. LINE 模式會繼續詢問 main 與 tab 的貼圖編號；WeChat 模式會詢問 cover 來源，panel icon 預設使用相同貼圖。若沒有 Banner，可輸入 Banner 路徑或直接略過。
6. 完成後會開啟 Preview 與 `output/`。

直接按 Enter 選擇預設值時，仍會輸出 LINE 並使用第 1 張作為 main 與 tab，保留 v1.1 操作方式。非互動模式遇到多張合集時，沿用舊版規則選擇最後修改時間最新者。

#### 拖放資料夾

可將資料夾拖到 `build.command` 上。假設資料夾內容如下：

```text
MySticker/
├── Berry.png
└── my_image.png
```

Banner 偵測順序如下：

1. `--banner` 手動指定路徑。
2. 不分大小寫的 `wechat_banner` 或 `banner` 檔名，支援 PNG、JPG、JPEG、WebP；檔名符合時不限制原始比例。
3. 其他剩餘圖片若為橫向，且套用 EXIF Orientation 後的寬高比與 `WECHAT_CONFIG.banner_size` 相差不超過 5%，即視為比例候選。
4. 仍找不到時提示手動輸入；直接按 Enter 可略過。

近方形圖片優先視為 4×4 合集，已選定的合集不會同時作為 Banner。多張同優先級 Banner 候選時，互動模式會列出檔名、方向修正後的尺寸與比例供選擇。所有 Banner 最後都經同一套 EXIF 方向校正、色彩轉換、等比例 contain 與置中流程。

### 命令列使用方式

```bash
python3 sticker_processor.py
python3 sticker_processor.py /path/to/MySticker --interactive
python3 sticker_processor.py --input /path/to/Berry.png --platform line --main 9 --tab 3
python3 sticker_processor.py --input /path/to/Berry.png --platform wechat --banner /path/to/any-name.png
python3 sticker_processor.py --input /path/to/Berry.png --platform both --main 9 --tab 3 --wechat-cover 5
```

`--platform` 支援 `line`、`wechat`、`both`；未指定時預設 `line`。

### 架構

```text
UI / CLI
   ↓
StickerService
   ↓
Core image-processing modules
   ↓
Filesystem outputs
```

- `src/sticker_toolkit/core/`：純 Python 圖片載入、切割、處理、輸出 facade、資料模型與例外；不依賴 UI
- `src/sticker_toolkit/services/`：唯一的流程協調入口 `StickerService`
- `src/sticker_toolkit/presets/`：LINE 與 WeChat 平台差異及驗證範圍
- `src/sticker_toolkit/ui/cli/`：命令列參數、互動、進度與結果顯示 adapter
- `src/sticker_toolkit/ui/desktop/`：PySide6 主視窗、ViewModel、控制器、QThread worker 與平台工具
- `core/`、`exporters/`：保留 v1.2 已驗證的演算法／輸出實作，透過新 Core API 漸進遷移
- `sticker_processor.py`：舊版命令的薄相容入口，不再保存圖片處理流程
- `cover.py`、`exporter.py`：v1.1 程式介面的相容層

Core 可在完全不 import CLI 或桌面 UI 的環境下使用。CLI 與桌面版都建立 `ProcessingOptions`，再呼叫同一個 `StickerService.process()`；結果、警告與錯誤分別透過 `ProcessingResult`、回傳值及自訂例外傳遞。桌面 worker 使用 Qt signal 將進度、結果與錯誤送回主執行緒。macOS arm64 DMG 與 Windows x64 onedir 均已完成原生環境建置及功能驗證。

#### 套件入口

```bash
PYTHONPATH=src python3 -m sticker_toolkit.ui.cli --input input/example.png --platform line
PYTHONPATH=src .venv/bin/python -m sticker_toolkit.ui.desktop
```

服務層可由 CLI、桌面控制器或背景 worker 共用：

```python
from pathlib import Path
from sticker_toolkit.core import ProcessingOptions
from sticker_toolkit.services import StickerService

result = StickerService().process(
    Path("input/sheet.png"),
    ProcessingOptions(platform="both", output_directory=Path("output")),
    progress_callback=lambda percent, message: print(percent, message),
)
```

### 調整尺寸與安全留白

所有平台尺寸集中在 `core/config.py`：

- `LINE_CONFIG.sticker_size`、`sticker_padding`
- `LINE_CONFIG.main_size`、`main_padding`
- `LINE_CONFIG.tab_size`、`tab_padding`
- `WECHAT_CONFIG` 集中管理 8～24 張數量範圍、240×240 貼圖、750×400 Banner、240×240 cover、50×50 panel icon，以及 500KB／100KB 上限

### 開發與測試

安裝 Core、Desktop 與開發工具：

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -e '.[desktop,dev]'
```

```bash
PYTHONPATH=src .venv/bin/python -m compileall -q src core exporters sticker_processor.py
QT_QPA_PLATFORM=offscreen PYTHONPATH=src .venv/bin/python -m unittest discover -s tests -v
.venv/bin/ruff check .
PYTHONPATH=src .venv/bin/mypy sticker_processor.py src/sticker_toolkit core exporters
```

### Build／封裝

安裝 PyInstaller：

```bash
.venv/bin/python -m pip install -e '.[desktop,build]'
```

macOS 建置、Bundle 驗證與 DMG：

```bash
PYTHON_BIN=.venv/bin/python packaging/build_macos.sh
packaging/verify_macos_app.sh
PYTHON_BIN=.venv/bin/python packaging/create_dmg.sh
```

Windows 已在原生 Windows x64 環境驗證。建議使用可重複建立 `.venv-win`、版本化 onedir 與 ZIP 的腳本：

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\build_windows.ps1 -Python "C:\path\to\python.exe"
```

詳細需求與實機驗證方式請參閱 [Windows x64 建置說明](docs/WINDOWS_BUILD.md)、[packaging/README.md](packaging/README.md) 與 [Windows 原生驗證清單](packaging/WINDOWS_TEST_CHECKLIST.md)。`build/`、`dist/`、`release/`、DMG、Log、cache 與測試產物皆不納入 Git。

## 已知限制

- 合集必須是規則排列的 4×4；不支援其他格數或不等寬排版。
- JPG 壓縮雜色可能影響白底移除，建議優先使用含透明背景的 PNG。
- `tab.png` 不使用角色臉部辨識模型，只會緊密裁切並放大完整主體。
- 從原始碼安裝相依套件時需要網路及 Python 3。
- macOS 正式封裝目前僅支援 Apple Silicon `arm64`，且未簽章、未公證。
- Windows 套件尚未簽章，可能出現 SmartScreen 或防毒誤報；必須保留完整 onedir 結構。

## 版本資訊

目前版本：`v1.3.2`

詳見 [CHANGELOG.md](CHANGELOG.md)。

## Roadmap

- 支援其他列數與欄數的合集圖
- 完成 Developer ID 簽章、公證與 Gatekeeper 發行驗證
- 評估 Windows code signing、SmartScreen reputation 與 onefile 發行格式
- 評估 Intel／Universal macOS 建置需求
- 提供裁切與安全留白即時調整
- 加入更多平台 exporter 與批次處理
