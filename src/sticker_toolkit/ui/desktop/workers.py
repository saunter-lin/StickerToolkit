"""不綁定特定 GUI framework 的背景工作骨架。"""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from threading import Thread

from sticker_toolkit.core import ProcessingOptions, ProcessingResult, ProgressCallback
from sticker_toolkit.services import StickerService

ResultCallback = Callable[[ProcessingResult], None]
ErrorCallback = Callable[[Exception], None]


def start_processing_worker(
    service: StickerService,
    source_path: Path,
    options: ProcessingOptions,
    progress_callback: ProgressCallback | None,
    result_callback: ResultCallback,
    error_callback: ErrorCallback,
) -> Thread:
    def run() -> None:
        try:
            result_callback(service.process(source_path, options, progress_callback))
        except Exception as exc:
            error_callback(exc)

    worker = Thread(target=run, name="sticker-toolkit-worker", daemon=True)
    worker.start()
    return worker
