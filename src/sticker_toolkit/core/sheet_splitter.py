"""貼圖合集切割 API。"""

from PIL import Image

from core.images import StickerError
from core.images import split_grid as _split_grid

from .exceptions import InvalidGridError


def split_grid(image: Image.Image, rows: int = 4, columns: int = 4) -> list[Image.Image]:
    if (rows, columns) != (4, 4):
        raise InvalidGridError("目前貼圖合集必須使用 4×4 格線。")
    try:
        return _split_grid(image)
    except StickerError as exc:
        raise InvalidGridError(str(exc)) from exc
