#!/usr/bin/env python3
"""舊版 CLI 相容入口；實際流程位於 sticker_toolkit.ui.cli。"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from sticker_toolkit.ui.cli.main import (  # noqa: E402
    choose_banner,
    choose_number,
    choose_platform,
    main,
    run_process,
)

__all__ = ["choose_banner", "choose_number", "choose_platform", "main", "run_process"]

if __name__ == "__main__":
    raise SystemExit(main())
