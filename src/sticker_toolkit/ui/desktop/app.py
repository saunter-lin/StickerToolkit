"""桌面應用程式入口，只建立 Application、主視窗與事件迴圈。"""

from __future__ import annotations

import sys
from typing import cast

from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication

from sticker_toolkit.logging_config import configure_logging
from sticker_toolkit.resources import get_resource_path

from .main_window import MainWindow


def main() -> int:
    configure_logging()
    existing = QApplication.instance()
    application = QApplication(sys.argv) if existing is None else cast(QApplication, existing)
    application.setApplicationName("Sticker Toolkit")
    application.setOrganizationName("StickerToolkit")
    icon_path = get_resource_path("assets/app_icon.png")
    if icon_path.is_file():
        application.setWindowIcon(QIcon(str(icon_path)))
    window = MainWindow()
    window.show()
    return int(application.exec())
