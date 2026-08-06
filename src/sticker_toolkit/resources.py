"""原始碼與 PyInstaller frozen 模式共用的資源路徑。"""

from __future__ import annotations

import sys
from pathlib import Path


def get_resource_path(relative_path: str | Path) -> Path:
    frozen_root = getattr(sys, "_MEIPASS", None)
    if frozen_root is not None:
        return Path(str(frozen_root)) / relative_path
    return Path(__file__).resolve().parents[2] / relative_path
