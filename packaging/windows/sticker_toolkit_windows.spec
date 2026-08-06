# -*- mode: python ; coding: utf-8 -*-
"""Windows x64 onedir configuration for Sticker Toolkit."""

from pathlib import Path
import re

from PyInstaller.utils.win32.versioninfo import (
    FixedFileInfo,
    StringFileInfo,
    StringStruct,
    StringTable,
    VarFileInfo,
    VarStruct,
    VSVersionInfo,
)

spec_root = Path(SPECPATH).resolve()
project_root = spec_root.parents[1]
version_source = project_root / "src" / "sticker_toolkit" / "version.py"
version_match = re.search(
    r'^__version__\s*=\s*["\']([^"\']+)["\']',
    version_source.read_text(encoding="utf-8"),
    flags=re.MULTILINE,
)
if version_match is None:
    raise RuntimeError(f"Unable to read application version from {version_source}")

application_version = version_match.group(1)
release_match = re.fullmatch(r"(\d+)\.(\d+)\.(\d+)", application_version)
if release_match is None:
    raise RuntimeError(f"Windows packaging requires an X.Y.Z version: {application_version}")
version_tuple = tuple(int(part) for part in release_match.groups()) + (0,)

entry_point = project_root / "packaging" / "desktop_entry.py"
icon_path = project_root / "assets" / "icons" / "StickerToolkit.ico"
app_icon = project_root / "assets" / "app_icon_packaging.png"
for required_path in (entry_point, icon_path, app_icon):
    if not required_path.is_file():
        raise RuntimeError(f"Required packaging file is missing: {required_path}")

version_info = VSVersionInfo(
    ffi=FixedFileInfo(
        filevers=version_tuple,
        prodvers=version_tuple,
        mask=0x3F,
        flags=0x0,
        OS=0x40004,
        fileType=0x1,
        subtype=0x0,
        date=(0, 0),
    ),
    kids=[
        StringFileInfo(
            [
                StringTable(
                    "040904B0",
                    [
                        StringStruct("CompanyName", "StickerToolkit"),
                        StringStruct("FileDescription", "Sticker Toolkit"),
                        StringStruct("FileVersion", application_version),
                        StringStruct("InternalName", "StickerToolkit"),
                        StringStruct("OriginalFilename", "StickerToolkit.exe"),
                        StringStruct("ProductName", "Sticker Toolkit"),
                        StringStruct("ProductVersion", application_version),
                    ],
                )
            ]
        ),
        VarFileInfo([VarStruct("Translation", [1033, 1200])]),
    ],
)

analysis = Analysis(
    [str(entry_point)],
    pathex=[str(project_root), str(project_root / "src")],
    binaries=[],
    datas=[(str(app_icon), "assets")],
    hiddenimports=[
        "PIL.Image",
        "PIL.ImageFile",
        "PIL.ImageQt",
        "PIL.JpegImagePlugin",
        "PIL.PngImagePlugin",
        "PIL.WebPImagePlugin",
        "PySide6.QtCore",
        "PySide6.QtGui",
        "PySide6.QtWidgets",
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=["pytest", "mypy", "ruff", "unittest"],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(analysis.pure)

executable = EXE(
    pyz,
    analysis.scripts,
    [],
    exclude_binaries=True,
    name="StickerToolkit",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    icon=str(icon_path),
    version=version_info,
)

collected = COLLECT(
    executable,
    analysis.binaries,
    analysis.datas,
    strip=False,
    upx=False,
    name="StickerToolkit",
)
