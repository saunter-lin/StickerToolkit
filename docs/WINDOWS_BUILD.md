# Windows x64 建置說明

## 環境

- Windows 10/11 x64 實體環境
- Windows x64 Python 3.10 以上
- PowerShell 5.1 以上
- 專案版本取自 `src/sticker_toolkit/version.py`，建置腳本不會修改或推測版本

## 建置

在專案根目錄執行：

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\build_windows.ps1 -Python "C:\path\to\python.exe"
```

腳本會驗證 Windows x64 Python、建立或沿用 `.venv-win`、更新 pip/setuptools/wheel、安裝 desktop/build 依賴、清除本次 Windows 建置暫存、執行 PyInstaller onedir 建置，最後建立：

- `release/windows/StickerToolkit-vX.Y.Z-Windows-x64/`
- `release/windows/StickerToolkit-vX.Y.Z-Windows-x64.zip`

## 測試

1. 解壓 ZIP，雙擊 `StickerToolkit.exe`，確認沒有命令列視窗。
2. 確認視窗標題、中文文字和程式圖示正常。
3. 從含中文及空格的路徑選擇 PNG/JPEG/WebP 合集圖片。
4. 分別執行 LINE、微信及 LINE＋微信輸出。
5. 確認 `line_sticker`、`wechat_sticker`、`preview/line`、`preview/wechat` 與各 ZIP 結構符合既有規則。
6. 將整個發布資料夾複製到另一個含中文及空格的路徑後再次啟動與輸出。
7. 在未安裝 Python、未啟用虛擬環境的使用者環境測試，確認程式只依賴發布資料夾。

無 Console 模式的未預期錯誤會寫入 `%LOCALAPPDATA%\StickerToolkit\Logs\sticker_toolkit.log`，並顯示 GUI 錯誤訊息。

## SmartScreen 與簽章

目前成品未進行程式碼簽章。Windows SmartScreen 可能顯示「Windows 已保護您的電腦」；確認檔案來源後，可選擇「其他資訊」再按「仍要執行」。公開發布時建議以受信任的 Windows code-signing 憑證簽署 EXE。

## 清理

可刪除以下產物後重新建置：

- `.venv-win/`
- `build/windows-pyinstaller/`
- `dist/windows-pyinstaller/`
- `release/windows/StickerToolkit-vX.Y.Z-Windows-x64/`
- `release/windows/StickerToolkit-vX.Y.Z-Windows-x64.zip`

建置腳本會自動清理後四項中與本次版本相符的舊產物；刪除 `.venv-win` 後，下次建置會重新建立虛擬環境。
