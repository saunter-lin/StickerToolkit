"""集中管理跨平台檔案管理器操作。"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path


def open_in_file_manager(path: Path) -> None:
    target = path.expanduser().resolve()
    if not target.exists():
        raise FileNotFoundError(f"找不到輸出目錄：{target}")
    if sys.platform == "darwin":
        subprocess.Popen(["open", str(target)])
    elif sys.platform == "win32":
        os.startfile(str(target))  # type: ignore[attr-defined]
    else:
        subprocess.Popen(["xdg-open", str(target)])
