"""平台共用的圖片載入、切割、去背與安全留白管線。"""

from __future__ import annotations

from collections import deque
from pathlib import Path

from PIL import Image, ImageOps, UnidentifiedImageError

WHITE_THRESHOLD = 248
GRID_ROWS = 4
GRID_COLUMNS = 4
EXPECTED_STICKERS = GRID_ROWS * GRID_COLUMNS


class StickerError(RuntimeError):
    """可直接顯示給使用者的圖片處理錯誤。"""


def load_image(path: Path, label: str = "圖片") -> Image.Image:
    try:
        with Image.open(path) as opened:
            oriented = ImageOps.exif_transpose(opened)
            oriented.load()
            return oriented.convert("RGBA")
    except UnidentifiedImageError as exc:
        raise StickerError(f"{label}不是有效或支援的圖片：{path.name}") from exc
    except (OSError, ValueError) as exc:
        raise StickerError(f"{label}解碼失敗：{path.name}（{exc}）") from exc


def remove_edge_background(source: Image.Image) -> Image.Image:
    """只清除與格子邊界連通的透明或近白背景。"""
    image = source.convert("RGBA")
    pixels = image.load()
    if pixels is None:
        raise StickerError("無法存取圖片像素。")
    width, height = image.size
    seen = bytearray(width * height)
    queue: deque[tuple[int, int]] = deque()

    def is_background(x: int, y: int) -> bool:
        pixel = pixels[x, y]
        if not isinstance(pixel, tuple) or len(pixel) != 4:
            raise StickerError("圖片像素格式不是 RGBA。")
        red, green, blue, alpha = pixel
        return alpha == 0 or (
            alpha > 0 and red >= WHITE_THRESHOLD and green >= WHITE_THRESHOLD and blue >= WHITE_THRESHOLD
        )

    def add(x: int, y: int) -> None:
        index = y * width + x
        if not seen[index] and is_background(x, y):
            seen[index] = 1
            queue.append((x, y))

    for x in range(width):
        add(x, 0)
        add(x, height - 1)
    for y in range(height):
        add(0, y)
        add(width - 1, y)
    while queue:
        x, y = queue.popleft()
        pixels[x, y] = (255, 255, 255, 0)
        if x:
            add(x - 1, y)
        if x + 1 < width:
            add(x + 1, y)
        if y:
            add(x, y - 1)
        if y + 1 < height:
            add(x, y + 1)
    return image


def crop_visible(image: Image.Image, label: str = "圖片") -> Image.Image:
    rgba = image.convert("RGBA")
    bbox = rgba.getchannel("A").getbbox()
    if bbox is None:
        raise StickerError(f"{label}完全透明，沒有可輸出的內容。")
    return rgba.crop(bbox)


def contain(image: Image.Image, size: tuple[int, int], padding: int) -> Image.Image:
    content = crop_visible(image)
    available = (size[0] - padding * 2, size[1] - padding * 2)
    if available[0] <= 0 or available[1] <= 0:
        raise StickerError("安全留白過大，畫布沒有可用空間。")
    content.thumbnail(available, Image.Resampling.LANCZOS)
    canvas = Image.new("RGBA", size, (0, 0, 0, 0))
    canvas.alpha_composite(content, ((size[0] - content.width) // 2, (size[1] - content.height) // 2))
    return canvas


def split_grid(image: Image.Image) -> list[Image.Image]:
    width, height = image.size
    if width < GRID_COLUMNS or height < GRID_ROWS:
        raise StickerError("貼圖合集尺寸太小，無法切割成 4×4。")
    x_edges = [round(index * width / GRID_COLUMNS) for index in range(GRID_COLUMNS + 1)]
    y_edges = [round(index * height / GRID_ROWS) for index in range(GRID_ROWS + 1)]
    cells = [
        image.crop((x_edges[column], y_edges[row], x_edges[column + 1], y_edges[row + 1]))
        for row in range(GRID_ROWS)
        for column in range(GRID_COLUMNS)
    ]
    if len(cells) != EXPECTED_STICKERS:
        raise StickerError(f"切割失敗：預期 16 張，實際得到 {len(cells)} 張。")
    return cells


def build_shared_stickers(
    source: Image.Image,
    size: tuple[int, int],
    padding: int,
    *,
    remove_cell_edge_background: bool = True,
) -> list[Image.Image]:
    """只執行一次 Split → Trim → Safe Margin。"""
    stickers: list[Image.Image] = []
    for index, cell in enumerate(split_grid(source), 1):
        try:
            prepared = remove_edge_background(cell) if remove_cell_edge_background else cell.convert("RGBA")
            stickers.append(contain(prepared, size, padding))
        except StickerError as exc:
            raise StickerError(f"第 {index:02d} 格處理失敗：{exc}") from exc
    if len(stickers) != EXPECTED_STICKERS:
        raise StickerError(f"處理失敗：預期 16 張，實際得到 {len(stickers)} 張。")
    return stickers
