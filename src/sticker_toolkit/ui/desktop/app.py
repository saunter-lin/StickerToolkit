"""桌面應用程式入口，只建立 Application、主視窗與事件迴圈。"""

from __future__ import annotations

import logging
import sys
from types import TracebackType
from typing import cast

from PySide6.QtCore import QLocale, QSettings
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication, QMessageBox

from sticker_toolkit.logging_config import configure_logging
from sticker_toolkit.resources import get_resource_path

from .i18n import normalize_language, tr
from .main_window import MainWindow

logger = logging.getLogger(__name__)


def _show_unhandled_exception(
    exception_type: type[BaseException],
    exception: BaseException,
    traceback: TracebackType | None,
) -> None:
    """Log otherwise invisible failures in a frozen windowed application."""
    logger.critical(
        "Unhandled desktop exception",
        exc_info=(exception_type, exception, traceback),
    )
    application = QApplication.instance()
    if isinstance(application, QApplication):
        if sys.platform == "win32":
            settings = QSettings(
                QSettings.Format.IniFormat,
                QSettings.Scope.UserScope,
                "StickerToolkit",
                "StickerToolkit",
            )
        else:
            settings = QSettings("StickerToolkit", "StickerToolkit")
        saved_language = settings.value("language")
        language = normalize_language(
            str(saved_language) if saved_language is not None else None,
            QLocale.system().name(),
        )
        QMessageBox.critical(
            None,
            tr(language, "error.unexpected_title"),
            tr(language, "error.unexpected", error=f"{exception_type.__name__}: {exception}"),
        )


def main() -> int:
    configure_logging(console=not bool(getattr(sys, "frozen", False)))
    sys.excepthook = _show_unhandled_exception
    existing = QApplication.instance()
    application = QApplication(sys.argv) if existing is None else cast(QApplication, existing)
    application.setApplicationName("Sticker Toolkit")
    application.setOrganizationName("StickerToolkit")
    icon_path = get_resource_path("assets/app_icon_packaging.png")
    if icon_path.is_file():
        application.setWindowIcon(QIcon(str(icon_path)))
    window = MainWindow()
    window.show()
    return int(application.exec())
