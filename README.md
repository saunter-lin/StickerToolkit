# Multi Platform Sticker Toolkit v1.2.0（macOS）

Sticker Toolkit 將一張規則排列的 4×4 貼圖合集切成 16 張，經過共用的 Trim、等比例縮放與 Safe Margin 管線後，可輸出 LINE、WeChat，或同時輸出兩種平台套件。程式不依靠合集檔名判斷來源。

## 功能

- 支援 `.png`、`.jpg`、`.jpeg` 4×4 貼圖合集
- 一次執行 Split → Trim → Safe Margin，平台 exporter 共用 16 張處理結果
- 移除透明空白或與邊界相連的近白背景
- 保持比例、透明背景、置中及安全留白
- LINE：自選 `main.png`、`tab.png`，規格驗證、Preview 與 ZIP
- WeChat：檔名優先、圖片尺寸／比例備援偵測 Banner、Preview 與 ZIP
- 可選 LINE、WeChat 或兩者一起輸出
- Banner 僅執行 Resize → Center → Contain，不切割、不拉伸、不使用 AI 或 API
- 中文錯誤訊息涵蓋解碼、切割、透明內容、Banner、PNG 驗證與 ZIP 寫入

## macOS 操作方式

### 使用 input 資料夾

1. 將貼圖合集放入 `input/`。
2. 選用：將任意檔名的橫向 PNG Banner 放在同一資料夾。
3. 雙擊 `build.command`。若 macOS 阻擋，請在 Finder 對檔案按右鍵並選擇「打開」。
4. 選擇 LINE、WeChat 或同時輸出。
5. LINE 模式會繼續詢問 main 與 tab 的貼圖編號；WeChat 模式若沒有 Banner，可輸入 Banner 路徑或直接略過。
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
python3 sticker_processor.py --input /path/to/Berry.png --platform both --main 9 --tab 3
```

`--platform` 支援 `line`、`wechat`、`both`；未指定時預設 `line`。

## 輸出內容

### LINE

- `01.png`～`16.png`：370×320 px RGBA PNG
- `main.png`：240×240 px RGBA PNG
- `tab.png`：96×74 px RGBA PNG
- `preview.png`：16 張貼圖檢查圖
- `line_sticker.zip`：唯一的 LINE ZIP 套件，不產生重複副本

### WeChat

- `wechat_preview.png`：顯示 16 張貼圖、Banner 與 ZIP 內容
- `wechat_sticker_package.zip`：ZIP 結構如下：

```text
wechat/
├── stickers/
│   ├── 01.png
│   ├── ...
│   └── 16.png
├── banner/
│   └── banner.png          # 未提供 Banner 時省略整個 banner/
```

WeChat ZIP 不包含 `manifest.json` 或其他 JSON；未提供 Banner 時，ZIP 僅有 `wechat/stickers/01.png`～`16.png`。

Banner 尺寸集中於 `core/config.py` 的 `WECHAT_CONFIG`。目前採用可調整的 750×400 contain 畫布，尚未宣稱為微信官方規格；發布到特定微信平台前請依最新官方文件確認，程式內保留 TODO。

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
- `WECHAT_CONFIG.banner_size`、`banner_padding`

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
- WeChat Banner 官方尺寸尚待依實際上架管道確認。
- `tab.png` 不使用角色臉部辨識模型，只會緊密裁切並放大完整主體。
- 首次安裝 Pillow 時需要網路，且 macOS 必須已有 Python 3。

## 版本資訊

目前版本：`v1.2.0`

詳見 [CHANGELOG.md](CHANGELOG.md)。

## Roadmap

- 確認並加入不同微信上架管道的官方尺寸 preset
- 支援其他列數與欄數的合集圖
- 提供圖形化平台、main、tab 與 Banner 選擇介面
- 提供裁切與安全留白即時調整
- 加入更多平台 exporter 與批次處理
