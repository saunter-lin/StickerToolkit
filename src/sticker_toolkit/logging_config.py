"""桌面應用程式 logging 設定。"""

from __future__ import annotations

import logging
import os
import platform
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path

from sticker_toolkit.version import __version__


def get_log_directory() -> Path:
    if sys.platform == "darwin":
        return Path.home() / "Library" / "Logs" / "StickerToolkit"
    if sys.platform == "win32":
        base = Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local"))
        return base / "StickerToolkit" / "Logs"
    base = Path(os.environ.get("XDG_STATE_HOME", Path.home() / ".local" / "state"))
    return base / "sticker-toolkit"


def configure_logging(console: bool = True) -> Path:
    directory = get_log_directory()
    directory.mkdir(parents=True, exist_ok=True)
    log_path = directory / "sticker_toolkit.log"
    handlers: list[logging.Handler] = [
        RotatingFileHandler(log_path, maxBytes=1_000_000, backupCount=3, encoding="utf-8")
    ]
    if console:
        handlers.append(logging.StreamHandler())
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        handlers=handlers,
        force=True,
    )
    logging.getLogger(__name__).info(
        "Sticker Toolkit %s started on %s (%s)",
        __version__,
        platform.system(),
        platform.platform(),
    )
    return log_path
