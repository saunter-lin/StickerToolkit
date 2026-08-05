# Sticker Toolkit v1.1.0（macOS）

這個工具會把一張 4×4、共 16 格的 PNG/JPG 合集圖切開，清除格子外圍的純白或透明空白，再製作 LINE 貼圖所需檔案。V1.1 可分別選擇 `main.png` 與 `tab.png` 的來源。

## 功能

- 平均切割 4×4 合集圖為 16 張貼圖
- 移除與邊界相連的純白背景或透明空白
- 等比例縮放、置中並保留安全留白
- 分別選擇 `main.png` 與 `tab.png` 的來源貼圖
- 產生 16 格人工檢查預覽
- 驗證 PNG 格式、RGBA 模式、尺寸及內容邊界
- 自動建立 LINE 貼圖 ZIP

## 使用方法

1. 將 4×4 合集圖片放進 `input` 資料夾。支援 `.png`、`.jpg`、`.jpeg`。
2. 雙擊 `build.command`。
3. 若 macOS 阻擋執行，請在 Finder 對 `build.command` 按右鍵，選擇「打開」後確認。
4. 工具建立 16 張貼圖後會自動開啟帶編號的 `preview.png`。
5. 回到終端機，分別輸入 `main.png` 與 `tab.png` 要使用的編號（1～16）。兩者可以不同；直接按 Enter 會使用 01，與 V1 相容。
6. 完成後會再次開啟 `preview.png`，並自動開啟 `output` 資料夾。若不滿意，可再次雙擊 `build.command` 重新 Export。

若 `input` 有多張圖片，程式會使用「最後修改時間最新」的一張，並在終端機顯示所選檔名。原始圖片不會被修改。

首次執行時，若系統 Python 尚未安裝 Pillow，工具會在專案內建立 `.venv` 並安裝 `requirements.txt` 的依賴。電腦需已安裝 Python 3；首次安裝 Pillow 時需要網路。

## 輸出內容

- `01.png`～`16.png`：370×320 px RGBA PNG
- `main.png`：240×240 px RGBA PNG，使用指定貼圖並緊密裁切、放大、置中
- `tab.png`：96×74 px RGBA PNG，使用另一張指定貼圖並針對小尺寸緊密裁切、置中
- `preview.png`：16 張貼圖總覽（僅供檢查，不放入 ZIP）
- `line_stickers.zip`：包含 16 張貼圖、`main.png` 與 `tab.png`，共 18 個檔案

## LINE 貼圖尺寸

| 檔案 | 尺寸 | 格式 |
| --- | --- | --- |
| `01.png`～`16.png` | 370×320 px | RGBA PNG |
| `main.png` | 240×240 px | RGBA PNG |
| `tab.png` | 96×74 px | RGBA PNG |

程式只移除「與每格邊界相連」的近白背景，因此圖案內部封閉的白色區域會保留。JPG 壓縮可能使白底出現雜色；若效果不理想，建議使用 PNG 原圖。

## 調整安全留白

一般貼圖留白位於 `sticker_processor.py`，封面與標籤留白位於 `cover.py`：

- `STICKER_PADDING = 20`：16 張貼圖四周留白
- `MAIN_PADDING = 5`：主圖四周留白
- `TAB_PADDING = 5`：分頁圖四周留白

數值單位為像素，越大代表留白越多、圖案越小。

## 命令列用法（選用）

```bash
python3 sticker_processor.py
python3 sticker_processor.py --input /完整路徑/指定圖片.png
python3 sticker_processor.py --main 9 --tab 3
python3 sticker_processor.py --interactive --open-preview
```

未加入 `--interactive` 且沒有指定 `--main`／`--tab` 時，兩者預設使用第 1 張，保留 V1 的非互動行為。

## 程式模組

- `sticker_processor.py`：輸入選擇、4×4 切割與流程控制
- `cover.py`：`main.png`、`tab.png` 最佳化
- `preview.py`：16 格編號預覽
- `exporter.py`：PNG 驗證與 ZIP 打包

## 已知限制

- 輸入必須是規則排列的 4×4 合集圖；目前不支援其他格數或不等寬排版。
- 白底清除以與格子邊界相連的近白像素判斷；JPG 壓縮雜色可能影響結果，建議優先使用 PNG。
- `tab.png` 會緊密裁切並盡量放大完整主體，但不使用人臉或角色臉部辨識模型。
- 工具需在 macOS 安裝 Python 3；首次安裝 Pillow 時需要網路。

## 版本資訊

目前版本：`v1.1.0`

- 支援分別選擇 `main.png` 與 `tab.png`。
- 加入封面與小尺寸標籤最佳化。
- 保留 V1 的非互動預設行為。

## Roadmap

- 支援其他列數與欄數的合集圖
- 提供圖形化點選 main／tab 的介面
- 提供裁切與安全留白即時調整
- 加入批次處理與更多輸出預設

## 建議 Commit Message

```text
feat: add selectable cover and tab image with optimized export
```
