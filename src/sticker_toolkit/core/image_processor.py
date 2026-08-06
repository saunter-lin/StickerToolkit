"""去邊、留白、縮放與畫布合成 API。"""

from PIL import Image

from core.images import (
    StickerError,
)
from core.images import (
    build_shared_stickers as _build_shared_stickers,
)
from core.images import (
    contain as _contain,
)
from core.images import (
    crop_visible as _crop_visible,
)
from core.images import (
    remove_edge_background as _remove_edge_background,
)

from .exceptions import ProcessingError


def remove_edge_background(source: Image.Image) -> Image.Image:
    try:
        return _remove_edge_background(source)
    except StickerError as exc:
        raise ProcessingError(str(exc)) from exc


def crop_visible(image: Image.Image, label: str = "圖片") -> Image.Image:
    try:
        return _crop_visible(image, label)
    except StickerError as exc:
        raise ProcessingError(str(exc)) from exc


def contain(image: Image.Image, size: tuple[int, int], padding: int) -> Image.Image:
    try:
        return _contain(image, size, padding)
    except StickerError as exc:
        raise ProcessingError(str(exc)) from exc


def build_shared_stickers(
    source: Image.Image, size: tuple[int, int], padding: int
) -> list[Image.Image]:
    try:
        return _build_shared_stickers(source, size, padding)
    except StickerError as exc:
        raise ProcessingError(str(exc)) from exc
