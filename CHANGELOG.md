# Changelog

本文件依據 Repository 內的 Commit、annotated Tag、GitHub Release 與實際程式內容整理。

## [v1.3.0] — 2026-08-06

### Added

- 新增 PySide6 桌面主視窗，可選擇來源圖片、LINE／微信／兩者、微信 Banner 與輸出目錄。
- 新增 4×4 格線驗證、Preview／ZIP 選項、處理結果摘要及使用者可理解的錯誤畫面。
- 使用 QThread worker 呼叫 `StickerService`，透過 Qt signals 回傳真實進度、完成結果與錯誤，避免阻塞 UI thread。
- 使用 QSettings 保存最近來源資料夾、輸出資料夾、平台與視窗大小。
- 新增 rotating log、跨平台開啟輸出資料夾，以及兼容原始碼／PyInstaller frozen 模式的資源路徑工具。
- 新增 ViewModel、Controller、Worker、GUI 狀態及桌面整合測試。
- 新增跨平台 App Icon 資源、PyInstaller `.spec` 與版本共用的封裝設定。
- 新增 macOS App／DMG 建置及 Bundle 驗證腳本，DMG 內含 Applications 捷徑與 SHA-256。
- 新增原生 Windows PowerShell 建置腳本與 Windows smoke-test 清單。
- 新增經 Windows 10 x64 原生環境驗證的 Windows onedir ZIP，包含 Qt、Pillow、圖示與 Python runtime。

### Changed

- 建立 `src/sticker_toolkit` 分層架構，將 Core、Presets、Services、CLI 與 Desktop UI 隔離。
- CLI 與 Desktop 共用 `StickerService`、`ProcessingOptions`、`ProcessingResult`、進度 callback 與自訂例外。
- 保留 v1.2.3 的圖片演算法、LINE／WeChat 素材、Preview 與 ZIP 結構。
- macOS 封裝目前限定已驗證的 Apple Silicon `arm64`，並明確標示為未簽章、未公證測試建置。
- macOS／Windows 封裝圖示改用透明外角的無標題簡化版本，移除 Dock 中的白色方形底板。
- Desktop 自動輸出位置改為來源圖片同層的 `<來源檔名>_output`；手動選擇的位置具有優先權，且與自動建議分開保存。

### Pending

- 評估 Apple Developer 簽章、公證，以及 Windows code signing／SmartScreen reputation。

## [v1.2.3] — 2026-08-06

### Fixed

- Preview 統一移至 `output/preview/line/` 與 `output/preview/wechat/`。
- 平台重新輸出只清理自己的素材、ZIP 與 Preview，保留另一平台結果。
- 執行時安全移除舊版專案根目錄的 `preview/`；所有生成內容可透過刪除 `output/` 一次清理。

## [v1.2.2] — 2026-08-06

### Fixed

- LINE 素材改為輸出至 `output/line_sticker/`。
- LINE ZIP 使用 `line_sticker/` 內部目錄，且只產生一份 ZIP。
- LINE／WeChat Preview 分平台保存，重新輸出不再互相覆蓋。

## [v1.2.1] — 2026-08-06

### Fixed

- WeChat ZIP 對齊實際上傳素材：平鋪圖片、不含資料夾或 `manifest.json`。
- WeChat 表情圖、Banner、cover 與 panel icon 對齊尺寸、格式及檔案大小限制。
- Banner 偵測加入已知檔名、精確尺寸、±5% 比例與 EXIF Orientation 備援。
- 驗證 LINE 與 WeChat 共用一次 Split／Trim／Safe Margin 管線。

## [v1.2.0] — 2026-08-06

### Added

- 新增 WeChat Export、平台化 exporter 與 LINE／WeChat 同時輸出。
- 新增共用 Split → Trim → Safe Margin 圖片管線、Folder Import、Banner 探索及 WeChat Preview。
- 新增微信 240×240 表情圖、750×400 Banner、240×240 cover、50×50 panel icon 與 PNG 最佳化。

### Changed

- LINE ZIP 統一為 `line_sticker.zip`，移除重複輸出。
- WeChat ZIP 統一為 `wechat_sticker.zip`，只包含實際圖片素材。
- 保留 v1.1 的 LINE 切圖、main／tab 選擇、Preview、驗證與 ZIP 流程。

## [v1.1.0] — 2026-08-05

### Added

- Repository 的第一個可驗證版本與 initial release。
- 將 4×4 PNG／JPG 合集平均切割為 16 張 LINE 貼圖。
- 移除與邊界相連的近白或透明背景，等比例縮放、置中並保留安全留白。
- 可分別選擇 `main.png` 與 `tab.png` 來源，並針對封面與小尺寸標籤輸出。
- 新增 16 格 Preview、PNG／RGBA／尺寸／內容驗證、ZIP 打包及 macOS `build.command`。

## v1.0

Repository 中沒有可獨立驗證的 v1.0 Commit、Tag 或 GitHub Release。v1.1.0 README 僅記錄其保留「V1 相容」預設行為，因此不另行推測或拆分 v1.0 功能；可驗證的版本歷史從 v1.1.0 開始。

[v1.3.0]: https://github.com/saunter-lin/StickerToolkit/compare/v1.2.3...v1.3.0
[v1.2.3]: https://github.com/saunter-lin/StickerToolkit/compare/v1.2.2...v1.2.3
[v1.2.2]: https://github.com/saunter-lin/StickerToolkit/compare/v1.2.1...v1.2.2
[v1.2.1]: https://github.com/saunter-lin/StickerToolkit/compare/v1.2.0...v1.2.1
[v1.2.0]: https://github.com/saunter-lin/StickerToolkit/compare/v1.1.0...v1.2.0
[v1.1.0]: https://github.com/saunter-lin/StickerToolkit/releases/tag/v1.1.0
