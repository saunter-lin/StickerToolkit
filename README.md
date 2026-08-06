# Multi Platform Sticker Toolkit v1.2.3（macOS）

Sticker Toolkit 將一張規則排列的 4×4 貼圖合集切成 16 張，經過共用的 Trim、等比例縮放與 Safe Margin 管線後，可輸出 LINE、WeChat，或同時輸出兩種平台套件。程式不依靠合集檔名判斷來源。

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
Sticker Sheet
    ↓
core/images.py：Split → Trim → Safe Margin（一次）
    ↓
Shared Sticker Images
    ├── exporters/line.py
    └── exporters/wechat.py
```

- `core/config.py`：`LINE_CONFIG`、`WECHAT_CONFIG` 與集中尺寸
- `core/paths.py`：集中管理 output、平台素材、ZIP 與 Preview 路徑
- `core/discovery.py`：檔案／資料夾輸入、圖片尺寸分析、合集與 Banner 候選選擇
- `core/images.py`：共用圖片管線
- `exporters/common.py`：共用 PNG 驗證與 ZIP 寫入
- `exporters/line.py`：LINE exporter
- `exporters/wechat.py`：WeChat exporter
- `sticker_processor.py`：維持原本終端流程的控制器
- `cover.py`、`exporter.py`：v1.1 程式介面的相容層

## 調整尺寸與安全留白

所有平台尺寸集中在 `core/config.py`：

- `LINE_CONFIG.sticker_size`、`sticker_padding`
- `LINE_CONFIG.main_size`、`main_padding`
- `LINE_CONFIG.tab_size`、`tab_padding`
- `WECHAT_CONFIG` 集中管理 8～24 張數量範圍、240×240 貼圖、750×400 Banner、240×240 cover、50×50 panel icon，以及 500KB／100KB 上限

## 開發與測試

```bash
python3 -m compileall -q .
python3 -m unittest discover -s tests -v
ruff check .
mypy sticker_processor.py core exporters
```

## 已知限制

- 合集必須是規則排列的 4×4；不支援其他格數或不等寬排版。
- JPG 壓縮雜色可能影響白底移除，建議優先使用含透明背景的 PNG。
- `tab.png` 不使用角色臉部辨識模型，只會緊密裁切並放大完整主體。
- 首次安裝 Pillow 時需要網路，且 macOS 必須已有 Python 3。

## 版本資訊

目前版本：`v1.2.3`

詳見 [CHANGELOG.md](CHANGELOG.md)。

## Roadmap

- 支援其他列數與欄數的合集圖
- 提供圖形化平台、main、tab 與 Banner 選擇介面
- 提供裁切與安全留白即時調整
- 加入更多平台 exporter 與批次處理
