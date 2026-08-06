# Windows 原生驗證清單

Windows onedir 已在 Windows 10 Pro 22H2 x64 原生環境完成建置與程式化驗證；正式公開前仍需完成下列未勾選的人工檢查。

- [x] 在原生 Windows 10 x64 環境安裝 Python 與 `.[desktop,build]`
- [x] 執行 `scripts/build_windows.ps1` 並產生版本化 onedir ZIP
- [ ] 從 Explorer 啟動 `Sticker Toolkit.exe`
- [x] 程式化啟動 EXE、維持執行並建立頂層視窗
- [x] 驗證 LINE／WeChat 處理與既有 Preview／ZIP 結構
- [x] 驗證包含中文與空白的來源、輸出及複製後執行路徑
- [ ] 人工驗證 Worker、真實 Progress、成功／失敗後 UI 恢復
- [ ] 人工驗證 Settings 保存、Log 位置及開啟輸出資料夾
- [ ] 人工確認中文字型、圖示、檔案選擇器及無 Console 視窗
- [ ] 以 Windows Defender 與常用防毒軟體檢查誤報
- [ ] 比較 onedir 與 onefile 的啟動速度、誤報及 Qt plugin 相容性，再決定正式格式
- [ ] 在無 Python、無開發虛擬環境的電腦執行完整 smoke test
