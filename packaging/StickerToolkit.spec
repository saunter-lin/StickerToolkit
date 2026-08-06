# -*- mode: python ; coding: utf-8 -*-
"""Cross-platform PyInstaller configuration for Sticker Toolkit."""

from pathlib import Path
import re
import sys

spec_root = Path(SPECPATH).resolve()
project_root = spec_root if (spec_root / "src").is_dir() else spec_root.parent
version_source = project_root / "src" / "sticker_toolkit" / "version.py"
version_match = re.search(
    r'^__version__\s*=\s*["\']([^"\']+)["\']',
    version_source.read_text(encoding="utf-8"),
    flags=re.MULTILINE,
)
if version_match is None:
    raise RuntimeError(f"Unable to read application version from {version_source}")

application_version = version_match.group(1)
release_match = re.match(r"(\d+\.\d+\.\d+)", application_version)
if release_match is None:
    raise RuntimeError(f"Invalid application version: {application_version}")
bundle_version = release_match.group(1)

entry_point = project_root / "packaging" / "desktop_entry.py"
icon_path = (
    project_root / "assets" / "icons" / "StickerToolkit.icns"
    if sys.platform == "darwin"
    else project_root / "assets" / "icons" / "StickerToolkit.ico"
)

datas = [(str(project_root / "assets" / "app_icon_packaging.png"), "assets")]
hiddenimports = ["PySide6.QtCore", "PySide6.QtGui", "PySide6.QtWidgets"]

analysis = Analysis(
    [str(entry_point)],
    pathex=[str(project_root), str(project_root / "src")],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
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
    name="Sticker Toolkit",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    icon=str(icon_path),
)

collected = COLLECT(
    executable,
    analysis.binaries,
    analysis.datas,
    strip=False,
    upx=False,
    name="Sticker Toolkit",
)

if sys.platform == "darwin":
    app = BUNDLE(
        collected,
        name="Sticker Toolkit.app",
        icon=str(icon_path),
        bundle_identifier="com.saunterlin.stickertoolkit",
        version=bundle_version,
        info_plist={
            "CFBundleDisplayName": "Sticker Toolkit",
            "CFBundleShortVersionString": bundle_version,
            "CFBundleVersion": bundle_version,
            "LSMinimumSystemVersion": "13.0",
            "NSHighResolutionCapable": True,
        },
    )
