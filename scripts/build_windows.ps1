[CmdletBinding()]
param(
    [string]$Python = ""
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Split-Path -Parent $ScriptDir
$VenvDir = Join-Path $ProjectRoot ".venv-win"
$VenvPython = Join-Path $VenvDir "Scripts\python.exe"
$SpecPath = Join-Path $ProjectRoot "packaging\windows\sticker_toolkit_windows.spec"
$BuildPath = Join-Path $ProjectRoot "build\windows-pyinstaller"
$DistPath = Join-Path $ProjectRoot "dist\windows-pyinstaller"
$ReleaseRoot = Join-Path $ProjectRoot "release\windows"

function Invoke-Python {
    param([string]$Executable, [string[]]$Arguments)
    & $Executable @Arguments
    if ($LASTEXITCODE -ne 0) {
        throw "Python command failed with exit code $LASTEXITCODE"
    }
}

function Assert-WindowsX64Python {
    param([string]$Executable)
    if (-not (Test-Path -LiteralPath $Executable -PathType Leaf)) {
        throw "Python executable not found: $Executable"
    }
    Invoke-Python $Executable @(
        "-c",
        "import platform,struct,sys; assert sys.platform=='win32', sys.platform; assert platform.machine().upper() in ('AMD64','X86_64'), platform.machine(); assert struct.calcsize('P')*8==64, struct.calcsize('P')*8; print(f'Validated Python: {sys.version.split()[0]} Windows {platform.machine()} 64-bit')"
    )
}

if ($env:OS -ne "Windows_NT") {
    throw "This build script requires native Windows."
}
Set-Location $ProjectRoot

if (-not (Test-Path -LiteralPath $VenvPython -PathType Leaf)) {
    if ([string]::IsNullOrWhiteSpace($Python)) {
        $Python = "python"
    }
    Assert-WindowsX64Python $Python
    Invoke-Python $Python @("-m", "venv", $VenvDir)
}

Assert-WindowsX64Python $VenvPython
Invoke-Python $VenvPython @("-m", "pip", "install", "--upgrade", "pip", "setuptools", "wheel")
Invoke-Python $VenvPython @("-m", "pip", "install", "-e", ".[desktop,build]")

$VersionOutput = & $VenvPython -c "from sticker_toolkit.version import __version__; print(__version__)"
if ($LASTEXITCODE -ne 0) { throw "Unable to read project version." }
$Version = ($VersionOutput | Select-Object -Last 1).Trim()
if ($Version -notmatch '^\d+\.\d+\.\d+$') {
    throw "Invalid project version: $Version"
}

$ReleaseName = "StickerToolkit-v$Version-Windows-x64"
$ReleaseDirectory = Join-Path $ReleaseRoot $ReleaseName
$ZipPath = Join-Path $ReleaseRoot "$ReleaseName.zip"
$BuiltDirectory = Join-Path $DistPath "StickerToolkit"

foreach ($Target in @($BuildPath, $DistPath, $ReleaseDirectory, $ZipPath)) {
    if (Test-Path -LiteralPath $Target) {
        Remove-Item -LiteralPath $Target -Recurse -Force
    }
}
New-Item -ItemType Directory -Path $ReleaseRoot -Force | Out-Null

Invoke-Python $VenvPython @(
    "-m", "PyInstaller",
    "--clean",
    "--noconfirm",
    "--distpath", $DistPath,
    "--workpath", $BuildPath,
    $SpecPath
)

$ExePath = Join-Path $BuiltDirectory "StickerToolkit.exe"
if (-not (Test-Path -LiteralPath $ExePath -PathType Leaf)) {
    throw "Build completed but executable was not found: $ExePath"
}
Move-Item -LiteralPath $BuiltDirectory -Destination $ReleaseDirectory
Compress-Archive -LiteralPath $ReleaseDirectory -DestinationPath $ZipPath -CompressionLevel Optimal

$ReleaseSize = (Get-ChildItem -LiteralPath $ReleaseDirectory -File -Recurse | Measure-Object Length -Sum).Sum
$ZipSize = (Get-Item -LiteralPath $ZipPath).Length
$PyInstallerVersion = (& $VenvPython -m PyInstaller --version | Select-Object -Last 1).Trim()

Write-Host "Version: $Version"
Write-Host "PyInstaller: $PyInstallerVersion"
Write-Host "Release: $ReleaseDirectory"
Write-Host ("Release size: {0:N2} MiB" -f ($ReleaseSize / 1MB))
Write-Host "ZIP: $ZipPath"
Write-Host ("ZIP size: {0:N2} MiB" -f ($ZipSize / 1MB))
