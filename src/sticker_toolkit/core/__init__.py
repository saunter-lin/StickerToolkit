"""不依賴 UI 的圖片處理 Core 公開 API。"""

from .exceptions import (
    ExportError,
    InvalidGridError,
    InvalidSourceImageError,
    ProcessingError,
    StickerToolkitError,
    UnsupportedFormatError,
)
from .image_processor import build_shared_stickers, contain, crop_visible, remove_edge_background
from .loader import load_image
from .models import (
    OptionsCallback,
    PlatformProcessingResult,
    ProcessingOptions,
    ProcessingResult,
    ProgressCallback,
)
from .sheet_splitter import split_grid

__all__ = [
    "ExportError",
    "InvalidGridError",
    "InvalidSourceImageError",
    "OptionsCallback",
    "PlatformProcessingResult",
    "ProcessingError",
    "ProcessingOptions",
    "ProcessingResult",
    "ProgressCallback",
    "StickerToolkitError",
    "UnsupportedFormatError",
    "build_shared_stickers",
    "contain",
    "crop_visible",
    "load_image",
    "remove_edge_background",
    "split_grid",
]
