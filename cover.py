"""v1.1 相容層；新程式請使用 core.config 與 core.images。"""

from PIL import Image

from core.config import LINE_CONFIG
from core.images import contain, crop_visible

MAIN_SIZE = LINE_CONFIG.main_size
TAB_SIZE = LINE_CONFIG.tab_size
MAIN_PADDING = LINE_CONFIG.main_padding
TAB_PADDING = LINE_CONFIG.tab_padding


def crop_transparent(image: Image.Image) -> Image.Image:
    return crop_visible(image)


def fit_cover(image: Image.Image, size: tuple[int, int], padding: int) -> Image.Image:
    return contain(image, size, padding)


def make_main(sticker: Image.Image) -> Image.Image:
    if MAIN_SIZE is None:
        raise RuntimeError("LINE_CONFIG 缺少 main 尺寸。")
    return fit_cover(sticker, MAIN_SIZE, MAIN_PADDING)


def make_tab(sticker: Image.Image) -> Image.Image:
    if TAB_SIZE is None:
        raise RuntimeError("LINE_CONFIG 缺少 tab 尺寸。")
    return fit_cover(sticker, TAB_SIZE, TAB_PADDING)
