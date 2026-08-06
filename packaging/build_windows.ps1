param(
    [string]$Python = "python"
)

$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Split-Path -Parent $ScriptDir
Set-Location $ProjectRoot

if (-not $IsWindows) {
    throw "此腳本必須在原生 Windows 環境執行。"
}
if (-not (Test-Path "assets/icons/StickerToolkit.ico")) {
    throw "找不到 Windows App Icon。"
}
& $Python -c "import PyInstaller"
if ($LASTEXITCODE -ne 0) {
    throw "尚未安裝 PyInstaller，請先安裝 .[desktop,build]。"
}

Remove-Item -Recurse -Force "build/pyinstaller" -ErrorAction SilentlyContinue
Remove-Item -Recurse -Force "dist/Sticker Toolkit" -ErrorAction SilentlyContinue
& $Python -m PyInstaller --clean --noconfirm --distpath dist --workpath build/pyinstaller packaging/StickerToolkit.spec
if ($LASTEXITCODE -ne 0) {
    throw "PyInstaller 建置失敗。"
}
if (-not (Test-Path "dist/Sticker Toolkit/Sticker Toolkit.exe")) {
    throw "建置完成但找不到 Sticker Toolkit.exe。"
}
Write-Host "Windows onedir 建置完成：dist/Sticker Toolkit"
