"""以 Qt signal 將 StickerService 結果安全送回 UI thread。"""

from __future__ import annotations

import logging
from pathlib import Path

from PySide6.QtCore import QObject, Signal, Slot

from sticker_toolkit.core import ProcessingOptions

from .controllers import StickerController

logger = logging.getLogger(__name__)


class StickerWorker(QObject):
    progress_changed = Signal(int, str)
    completed = Signal(object)
    failed = Signal(object)
    finished = Signal()

    def __init__(
        self,
        controller: StickerController,
        source_path: Path,
        options: ProcessingOptions,
    ) -> None:
        super().__init__()
        self._controller = controller
        self._source_path = source_path
        self._options = options

    @Slot()
    def run(self) -> None:
        logger.info(
            "Processing started platform=%s source=%s output=%s",
            self._options.platform,
            self._source_path,
            self._options.output_directory,
        )
        try:
            result = self._controller.process(
                self._source_path,
                self._options,
                lambda percent, message: self.progress_changed.emit(percent, message),
            )
        except Exception as exc:
            logger.exception("Sticker processing failed")
            self.failed.emit(exc)
        else:
            logger.info("Processing completed platform=%s", self._options.platform)
            self.completed.emit(result)
        finally:
            self.finished.emit()
