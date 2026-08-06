"""來源圖片載入 API。"""

from pathlib import Path

from PIL import Image

from core.images import StickerError
from core.images import load_image as _load_image

from .exceptions import InvalidSourceImageError


def load_image(path: Path, label: str = "圖片") -> Image.Image:
    try:
        return _load_image(path, label)
    except StickerError as exc:
        raise InvalidSourceImageError(str(exc)) from exc
