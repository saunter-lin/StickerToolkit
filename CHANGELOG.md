# Changelog

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
