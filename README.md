# Multi Platform Sticker Toolkit v1.3.0-dev（macOS）

Sticker Toolkit 將一張規則排列的 4×4 貼圖合集切成 16 張，經過共用的 Trim、等比例縮放與 Safe Margin 管線後，可輸出 LINE、WeChat，或同時輸出兩種平台套件。程式不依靠合集檔名判斷來源。

版本演進與相容性修正請參閱 [CHANGELOG.md](CHANGELOG.md)。v1.3 目前仍為開發版，尚未建立正式 Tag 或 GitHub Release。

## 功能

- 支援 `.png`、`.jpg`、`.jpeg` 4×4 貼圖合集
- 一次執行 Split → Trim → Safe Margin，平台 exporter 共用 16 張處理結果
- 移除透明空白或與邊界相連的近白背景
- 保持比例、透明背景、置中及安全留白
- LINE：自選 `main.png`、`tab.png`，規格驗證、Preview 與 ZIP
- WeChat：8～24 張素材驗證、240×240 貼圖、Banner、封面、panel icon、Preview 與 ZIP
- 可選 LINE、WeChat 或兩者一起輸出
- Banner 僅執行 Resize → Center → Contain，不切割、不拉伸、不使用 AI 或 API
- 中文錯誤訊息涵蓋解碼、切割、透明內容、Banner、PNG 驗證與 ZIP 寫入

## macOS 操作方式

### 桌面介面（v1.3 開發版）

先安裝桌面 optional dependency：

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -e '.[desktop]'
```

從專案根目錄啟動：

```bash
PYTHONPATH=src .venv/bin/python -m sticker_toolkit.ui.desktop
```

桌面版目前可選擇來源圖片、LINE／微信／兩者、微信 Banner 與輸出目錄；支援 4×4 設定驗證、Preview／ZIP 選項、背景處理、真實進度、錯誤提示、結果摘要及跨平台開啟輸出資料夾。圖片處理全部交由 `StickerService` 執行，視窗不包含圖片演算法。

選擇來源圖片後，Desktop 會建議同層的 `<來源檔名>_output` 作為輸出根目錄，例如 `berry.png` 對應 `berry_output/`、`my.sticker.sheet.png` 對應 `my.sticker.sheet_output/`。在本次操作中手動按「選擇目錄」後，自訂位置優先，不會因重新選擇來源而被覆蓋；只有有效且由使用者手動選擇的目錄會由 QSettings 恢復。建議位置不可寫時會在開始處理前顯示錯誤，不會改用系統暫存目錄。

桌面設定使用 Qt `QSettings`，macOS 通常保存於 `~/Library/Preferences/` 的 StickerToolkit 設定中。封裝版與原始碼版使用相同的處理核心；原始碼版需準備 Python 環境，封裝版則自帶 Python、Qt 與 Pillow。Log 位於：

```text
~/Library/Logs/StickerToolkit/sticker_toolkit.log
```

Windows Log 預設位於 `%LOCALAPPDATA%/StickerToolkit/Logs/`。應用資源一律透過 `get_resource_path()` 取得，兼容原始碼與 PyInstaller frozen 模式。

目前 Repository 尚未納入正式 GUI 截圖；畫面會在正式 Release 視覺確認後補上，避免以開發中介面冒充正式發布畫面。

### macOS 封裝版（v1.3.0-dev）

目前封裝驗證平台為 Apple Silicon `arm64`，尚未宣稱支援 Intel 或 Universal。DMG 檔名格式為：

```text
StickerToolkit-v<version>-macOS-<arch>.dmg
```

開啟 DMG 後，將 `Sticker Toolkit.app` 拖到 `Applications` 捷徑，再從「應用程式」啟動。App 目前是 unsigned／未公證測試建置；若 Gatekeeper 阻擋，請在 Finder 對 App 按右鍵選擇「打開」，再確認開啟，或前往「系統設定 → 隱私權與安全性」允許。專案不會宣稱已完成 Apple Developer 簽章或 notarization。

Windows 封裝設定與 `.ico` 已備妥，但正式 EXE 必須在原生 Windows 10／11 環境建置與驗證；目前沒有可發布的 Windows 產物。

封裝使用 `assets/app_icon_packaging.png`：外角透明、移除底部標題與副標題，保留貼圖格、魔法棒、星光與聊天氣泡。原始品牌圖仍保存在 `assets/app_icon.png`，不會被封裝流程覆蓋。

### 使用 input 資料夾

1. 將貼圖合集放入 `input/`。
2. 選用：將任意檔名的橫向 PNG Banner 放在同一資料夾。
3. 雙擊 `build.command`。若 macOS 阻擋，請在 Finder 對檔案按右鍵並選擇「打開」。
4. 選擇 LINE、WeChat 或同時輸出。
5. LINE 模式會繼續詢問 main 與 tab 的貼圖編號；WeChat 模式會詢問 cover 來源，panel icon 預設使用相同貼圖。若沒有 Banner，可輸入 Banner 路徑或直接略過。
6. 完成後會開啟 Preview 與 `output/`。

直接按 Enter 選擇預設值時，仍會輸出 LINE 並使用第 1 張作為 main 與 tab，保留 v1.1 操作方式。非互動模式遇到多張合集時，沿用舊版規則選擇最後修改時間最新者。

### 拖放資料夾

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

## 命令列使用方式

```bash
python3 sticker_processor.py
python3 sticker_processor.py /path/to/MySticker --interactive
python3 sticker_processor.py --input /path/to/Berry.png --platform line --main 9 --tab 3
python3 sticker_processor.py --input /path/to/Berry.png --platform wechat --banner /path/to/any-name.png
python3 sticker_processor.py --input /path/to/Berry.png --platform both --main 9 --tab 3 --wechat-cover 5
```

`--platform` 支援 `line`、`wechat`、`both`；未指定時預設 `line`。

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

## 架構

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

Core 可在完全不 import CLI 或桌面 UI 的環境下使用。CLI 與桌面版都建立 `ProcessingOptions`，再呼叫同一個 `StickerService.process()`；結果、警告與錯誤分別透過 `ProcessingResult`、回傳值及自訂例外傳遞。桌面 worker 使用 Qt signal 將進度、結果與錯誤送回主執行緒。macOS arm64 PyInstaller／DMG 測試封裝已完成；Windows 正式產物仍待原生環境驗證。

### 新套件入口

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

## 調整尺寸與安全留白

所有平台尺寸集中在 `core/config.py`：

- `LINE_CONFIG.sticker_size`、`sticker_padding`
- `LINE_CONFIG.main_size`、`main_padding`
- `LINE_CONFIG.tab_size`、`tab_padding`
- `WECHAT_CONFIG` 集中管理 8～24 張數量範圍、240×240 貼圖、750×400 Banner、240×240 cover、50×50 panel icon，以及 500KB／100KB 上限

## 開發與測試

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

### 封裝

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

Windows 請在原生 Windows PowerShell 執行：

```powershell
packaging\build_windows.ps1 -Python .venv\Scripts\python
```

詳細需求、產物位置與 Windows 驗證項目請參閱 [packaging/README.md](packaging/README.md) 與 [Windows 原生驗證清單](packaging/WINDOWS_TEST_CHECKLIST.md)。`build/`、`dist/`、DMG、Log、cache 與測試產物皆不納入 Git。

## 已知限制

- 合集必須是規則排列的 4×4；不支援其他格數或不等寬排版。
- JPG 壓縮雜色可能影響白底移除，建議優先使用含透明背景的 PNG。
- `tab.png` 不使用角色臉部辨識模型，只會緊密裁切並放大完整主體。
- 首次安裝 Pillow 時需要網路，且 macOS 必須已有 Python 3。
- macOS 測試封裝目前僅驗證 Apple Silicon `arm64`，且未簽章、未公證。
- Windows EXE 尚待原生 Windows 環境建置、完整 smoke test 與防毒誤報檢查。

## 版本資訊

目前版本：`v1.3.0-dev`

詳見 [CHANGELOG.md](CHANGELOG.md)。

## Roadmap

- 支援其他列數與欄數的合集圖
- 完成 Developer ID 簽章、公證與 Gatekeeper 發行驗證
- 在原生 Windows 環境完成 EXE 建置、測試與發行格式選擇
- 評估 Intel／Universal macOS 建置需求
- 提供裁切與安全留白即時調整
- 加入更多平台 exporter 與批次處理
