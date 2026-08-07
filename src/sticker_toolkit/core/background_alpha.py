"""固定純色背景偵測與外部連通區域 Alpha 轉換。"""

from __future__ import annotations

from collections import deque
from collections.abc import Iterable
from statistics import median
from typing import cast

from PIL import Image

from .exceptions import ProcessingError

RGBColor = tuple[int, int, int]
DEFAULT_SOLID_BACKGROUND_COLOR = "#FFF8EC"
DEFAULT_SOLID_BACKGROUND_TOLERANCE = 3
MAX_SOLID_BACKGROUND_TOLERANCE = 30
_DETECTION_COLOR_SPREAD = 12
_MIN_BOUNDARY_MATCH_RATIO = 0.70


def parse_hex_color(value: str) -> RGBColor:
    """將 #RRGGBB 色碼轉成 RGB，格式錯誤時提供中文錯誤。"""
    normalized = value.strip().upper().removeprefix("#")
    if len(normalized) != 6:
        raise ProcessingError("純色背景色必須使用 #RRGGBB 格式。")
    try:
        channels = tuple(int(normalized[index : index + 2], 16) for index in (0, 2, 4))
    except ValueError as exc:
        raise ProcessingError("純色背景色必須使用 #RRGGBB 格式。") from exc
    return channels  # type: ignore[return-value]


def color_to_hex(color: RGBColor) -> str:
    return f"#{color[0]:02X}{color[1]:02X}{color[2]:02X}"


def _median_color(colors: Iterable[RGBColor]) -> RGBColor:
    values = list(colors)
    if not values:
        raise ProcessingError("圖片沒有可用於偵測背景色的像素。")
    channels = tuple(int(round(median(channel))) for channel in zip(*values, strict=True))
    return channels  # type: ignore[return-value]


def _is_near(color: RGBColor, target: RGBColor, tolerance: int) -> bool:
    return all(
        abs(channel - expected) <= tolerance
        for channel, expected in zip(color, target, strict=True)
    )


def _image_colors(image: Image.Image) -> Iterable[RGBColor]:
    flattened = getattr(image, "get_flattened_data", None)
    if callable(flattened):
        return cast(Iterable[RGBColor], flattened())
    return cast(Iterable[RGBColor], image.getdata())


def _corner_medians(image: Image.Image, inset: int = 0) -> list[RGBColor]:
    rgb = image.convert("RGB")
    width, height = rgb.size
    patch = max(1, min(8, width // 40, height // 40))
    inset = min(inset, max(0, (width - patch) // 2), max(0, (height - patch) // 2))
    boxes = (
        (inset, inset, inset + patch, inset + patch),
        (width - inset - patch, inset, width - inset, inset + patch),
        (inset, height - inset - patch, inset + patch, height - inset),
        (width - inset - patch, height - inset - patch, width - inset, height - inset),
    )
    return [
        _median_color(_image_colors(crop))
        for crop in (rgb.crop(box) for box in boxes)
    ]


def _boundary_colors(image: Image.Image, inset: int = 0) -> list[RGBColor]:
    rgb = image.convert("RGB")
    width, height = rgb.size
    inset = min(inset, max(0, (width - 1) // 2), max(0, (height - 1) // 2))
    pixels = rgb.load()
    if pixels is None:
        raise ProcessingError("無法存取圖片像素。")
    step = max(1, min(width, height) // 100)
    samples: list[RGBColor] = []
    for x in range(inset, width - inset, step):
        samples.extend(
            (
                cast(RGBColor, pixels[x, inset]),
                cast(RGBColor, pixels[x, height - 1 - inset]),
            )
        )
    for y in range(inset, height - inset, step):
        samples.extend(
            (
                cast(RGBColor, pixels[inset, y]),
                cast(RGBColor, pixels[width - 1 - inset, y]),
            )
        )
    return samples


def detect_canvas_edge_color(image: Image.Image) -> RGBColor | None:
    """偵測畫布最外框代表色，用於處理額外的純色邊框。"""
    if image.width == 0 or image.height == 0:
        return None
    boundary = _boundary_colors(image)
    candidate = _median_color(boundary)
    matching_colors = [
        color
        for color in boundary
        if _is_near(color, candidate, _DETECTION_COLOR_SPREAD)
    ]
    if len(matching_colors) / len(boundary) < _MIN_BOUNDARY_MATCH_RATIO:
        return None
    return _median_color(matching_colors)


def detect_solid_background_color(image: Image.Image) -> RGBColor | None:
    """以內縮角落與邊界多數色判斷真正的固定純色背景。"""
    if image.width == 0 or image.height == 0:
        return None
    inset = max(1, min(image.width, image.height) // 100)
    return _validated_background_candidate(image, inset)


def _validated_background_candidate(image: Image.Image, inset: int) -> RGBColor | None:
    corners = _corner_medians(image, inset)
    candidate = _median_color(corners)
    if any(
        abs(color[channel] - candidate[channel]) > _DETECTION_COLOR_SPREAD
        for color in corners
        for channel in range(3)
    ):
        return None
    boundary = _boundary_colors(image, inset)
    matching = sum(
        _is_near(color, candidate, _DETECTION_COLOR_SPREAD) for color in boundary
    )
    if matching / len(boundary) < _MIN_BOUNDARY_MATCH_RATIO:
        return None
    matching_colors = [
        color
        for color in (*corners, *boundary)
        if _is_near(color, candidate, _DETECTION_COLOR_SPREAD)
    ]
    return _median_color(matching_colors)


def remove_connected_solid_background(
    source: Image.Image,
    background_color: RGBColor,
    tolerance: int = DEFAULT_SOLID_BACKGROUND_TOLERANCE,
    *,
    grid_size: tuple[int, int] | None = None,
) -> Image.Image:
    """只把與畫布邊界連通的指定純色轉為透明，保留封閉區域。"""
    if not 0 <= tolerance <= MAX_SOLID_BACKGROUND_TOLERANCE:
        raise ProcessingError("純色背景容差必須介於 0～30。")
    image = source.convert("RGBA")
    pixels = image.load()
    if pixels is None:
        raise ProcessingError("無法存取圖片像素。")
    width, height = image.size
    seen = bytearray(width * height)
    queue: deque[tuple[int, int]] = deque()

    def can_visit(x: int, y: int) -> bool:
        red, green, blue, alpha = cast(tuple[int, int, int, int], pixels[x, y])
        return alpha == 0 or _is_near((red, green, blue), background_color, tolerance)

    def add(x: int, y: int) -> None:
        index = y * width + x
        if not seen[index] and can_visit(x, y):
            seen[index] = 1
            queue.append((x, y))

    for x in range(width):
        add(x, 0)
        add(x, height - 1)
    for y in range(height):
        add(0, y)
        add(width - 1, y)

    if grid_size is not None:
        rows, columns = grid_size
        x_edges = [round(index * width / columns) for index in range(columns + 1)]
        y_edges = [round(index * height / rows) for index in range(rows + 1)]
        scan = max(1, min(width // columns, height // rows) // 20)
        for row in range(rows):
            top, bottom = y_edges[row], y_edges[row + 1]
            for column in range(columns):
                left, right = x_edges[column], x_edges[column + 1]
                for offset in range(scan + 1):
                    for x in range(left, right):
                        add(x, min(bottom - 1, top + offset))
                        add(x, max(top, bottom - 1 - offset))
                    for y in range(top, bottom):
                        add(min(right - 1, left + offset), y)
                        add(max(left, right - 1 - offset), y)

    while queue:
        x, y = queue.popleft()
        red, green, blue, alpha = cast(tuple[int, int, int, int], pixels[x, y])
        if alpha != 0:
            pixels[x, y] = (red, green, blue, 0)
        if x:
            add(x - 1, y)
        if x + 1 < width:
            add(x + 1, y)
        if y:
            add(x, y - 1)
        if y + 1 < height:
            add(x, y + 1)
    return image
