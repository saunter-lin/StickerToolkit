# Changelog

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
