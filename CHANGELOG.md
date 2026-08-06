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
- WeChat ZIP 移除 `manifest.json`，Banner 統一輸出為 `wechat/banner/banner.png`。
- WeChat Banner 改為手動路徑、已知檔名、±5% 比例的分級備援偵測，並支援 EXIF Orientation。
