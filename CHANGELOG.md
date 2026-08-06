# Changelog

## v1.3.0-dev

### Changed

- 新增 `src/sticker_toolkit` 套件，將 Core、Services、Presets 與 UI adapters 分層。
- CLI 改為建立 `ProcessingOptions` 並呼叫唯一的 `StickerService` 流程。
- 圖片處理結果改以 `ProcessingResult` 回傳，錯誤使用明確例外階層。
- 新增可選進度 callback、桌面控制器與背景 worker 骨架，準備後續封裝。
- 保留 v1.2.3 的圖片演算法、LINE／WeChat 素材與 ZIP 結構。

### Development

- 新增 `python -m sticker_toolkit.ui.cli` 與預留的桌面 module 入口。
- 整理 `pyproject.toml` 的核心、build 與 dev dependencies。

## v1.2.3

### Fixed

- Preview 統一移至 `output/preview/line/` 與 `output/preview/wechat/`。
- 平台重新輸出只清理自己的素材、ZIP 與 Preview，保留另一平台結果。
- 執行時安全移除 v1.2.2 遺留在專案根目錄的 `preview/`。
- 所有生成素材、預覽與 ZIP 現在都可透過刪除 `output/` 一次清理。

## v1.2.2

### Fixed

- LINE 素材改為輸出至獨立的 `output/line_sticker/`。
- LINE ZIP 使用 `line_sticker/` 內部資料夾，且仍只產生一份 ZIP。
- Preview 改為 `preview/line/` 與 `preview/wechat/` 分平台保存。
- 平台重新輸出只清理自己的正式素材與 Preview，不再互相覆蓋或混放。

## v1.2.1

### Fixed

- WeChat ZIP 改為真正的平鋪圖片結構，不含任何資料夾或 JSON。
- 微信驗證摘要加入格式與每張表情圖的實際檔案大小。
- 將 Banner 目標比例與 ±5% 容差集中至 `WECHAT_CONFIG`。
- 明確驗證 LINE 與 WeChat 共用同一次 Split／Trim／Safe Margin 管線。

## v1.2.0

### Added

- WeChat Export
- Multi Platform Architecture
- Shared Sticker Pipeline
- Folder Import 與任意檔名 Banner 尺寸／比例偵測
- WeChat Preview 與純圖片 ZIP

### Compatibility

- 保留 v1.1 的 LINE 切割、main／tab 選擇、Preview、驗證與 ZIP 流程。
- 未指定平台時仍預設輸出 LINE。

### Changed

- LINE 統一只輸出 `line_sticker.zip`，移除重複 ZIP。
- WeChat ZIP 移除 `manifest.json`，並統一為 `wechat_sticker/` 純圖片結構。
- WeChat Banner 改為手動路徑、已知檔名、±5% 比例的分級備援偵測，並支援 EXIF Orientation。
- WeChat Export 對齊 240×240 表情圖、750×400 Banner、240×240 cover 與 50×50 panel icon 規格。
- WeChat 加入 8～24 張數量驗證、素材檔案上限、PNG 最佳化與完整性狀態。
- WeChat ZIP 統一為 `wechat_sticker.zip`，內容只保留實際上傳圖片。
