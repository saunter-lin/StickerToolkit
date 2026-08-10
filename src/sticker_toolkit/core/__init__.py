"""不依賴 UI 的圖片處理 Core 公開 API。"""

from core.grid_cleanup import clean_grid_edge_fragments

from .background_alpha import (
    DEFAULT_SOLID_BACKGROUND_COLOR,
    DEFAULT_SOLID_BACKGROUND_TOLERANCE,
    MAX_SOLID_BACKGROUND_TOLERANCE,
    RGBColor,
    color_to_hex,
    detect_canvas_edge_color,
    detect_solid_background_color,
    parse_hex_color,
    remove_connected_solid_background,
)
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
    "DEFAULT_SOLID_BACKGROUND_COLOR",
    "DEFAULT_SOLID_BACKGROUND_TOLERANCE",
    "ExportError",
    "InvalidGridError",
    "InvalidSourceImageError",
    "MAX_SOLID_BACKGROUND_TOLERANCE",
    "OptionsCallback",
    "PlatformProcessingResult",
    "ProcessingError",
    "ProcessingOptions",
    "ProcessingResult",
    "ProgressCallback",
    "RGBColor",
    "StickerToolkitError",
    "UnsupportedFormatError",
    "build_shared_stickers",
    "clean_grid_edge_fragments",
    "color_to_hex",
    "contain",
    "crop_visible",
    "detect_canvas_edge_color",
    "detect_solid_background_color",
    "load_image",
    "parse_hex_color",
    "remove_connected_solid_background",
    "remove_edge_background",
    "split_grid",
]
