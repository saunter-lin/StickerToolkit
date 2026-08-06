"""桌面控制器骨架，只組合 options 並呼叫 Service。"""

from pathlib import Path

from sticker_toolkit.core import ProcessingOptions, ProcessingResult, ProgressCallback
from sticker_toolkit.services import StickerService

from .view_model import DesktopFormData, build_processing_options


class StickerController:
    def __init__(self, service: StickerService | None = None) -> None:
        self.service = service or StickerService()

    def process(
        self,
        source_path: Path,
        options: ProcessingOptions,
        progress_callback: ProgressCallback | None = None,
    ) -> ProcessingResult:
        return self.service.process(source_path, options, progress_callback)

    @staticmethod
    def build_request(data: DesktopFormData) -> tuple[Path, ProcessingOptions]:
        options = build_processing_options(data)
        return Path(data.source_path).expanduser().resolve(), options
