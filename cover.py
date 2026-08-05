"""Sticker Toolkit V1.1：main 與 tab 圖片建立功能。"""

from PIL import Image

MAIN_SIZE = (240, 240)
TAB_SIZE = (96, 74)
MAIN_PADDING = 5
TAB_PADDING = 5


def crop_transparent(image: Image.Image) -> Image.Image:
    rgba = image.convert("RGBA")
    bbox = rgba.getchannel("A").getbbox()
    if bbox is None:
        raise RuntimeError("選取的貼圖沒有可見內容。")
    return rgba.crop(bbox)


def fit_cover(image: Image.Image, size: tuple[int, int], padding: int) -> Image.Image:
    """緊密裁切後等比例放到安全區；相較一般貼圖約放大 10～20%。"""
    content = crop_transparent(image)
    available = (size[0] - padding * 2, size[1] - padding * 2)
    if available[0] <= 0 or available[1] <= 0:
        raise ValueError("封面安全留白過大。")
    content.thumbnail(available, Image.Resampling.LANCZOS)
    canvas = Image.new("RGBA", size, (0, 0, 0, 0))
    position = ((size[0] - content.width) // 2, (size[1] - content.height) // 2)
    canvas.alpha_composite(content, position)
    return canvas


def make_main(sticker: Image.Image) -> Image.Image:
    return fit_cover(sticker, MAIN_SIZE, MAIN_PADDING)


def make_tab(sticker: Image.Image) -> Image.Image:
    # 緊密裁切與較小留白，讓小尺寸標籤優先呈現可辨識的角色主體。
    return fit_cover(sticker, TAB_SIZE, TAB_PADDING)
