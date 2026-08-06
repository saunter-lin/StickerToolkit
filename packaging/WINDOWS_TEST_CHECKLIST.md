# Windows 原生驗證清單

Windows 封裝尚未在原生 Windows 環境建置或驗證；不得將目前內容視為正式 Windows Release。

- [ ] 在乾淨的 Windows 10／11 x64 環境安裝 Python 與 `.[desktop,build]`
- [ ] 執行 `packaging/build_windows.ps1`
- [ ] 從 Explorer 啟動 `Sticker Toolkit.exe`
- [ ] 驗證來源圖片選擇、LINE／WeChat／兩者平台選擇
- [ ] 驗證 Worker、真實 Progress、成功／失敗後 UI 恢復
- [ ] 驗證 Settings 保存與 Log 產生位置
- [ ] 驗證開啟輸出資料夾
- [ ] 驗證包含中文與空白的來源、輸出路徑
- [ ] 以 Windows Defender 與常用防毒軟體檢查誤報
- [ ] 比較 onedir 與 onefile 的啟動速度、誤報及 Qt plugin 相容性，再決定正式格式
- [ ] 在無 Python、無開發虛擬環境的電腦執行完整 smoke test
