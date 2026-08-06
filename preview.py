"""Sticker Toolkit 的 16 格選擇／輸出預覽。"""

from PIL import Image, ImageDraw, ImageFont

MACOS_FONT_CANDIDATES = (
    "/System/Library/Fonts/PingFang.ttc",
    "/System/Library/Fonts/STHeiti Medium.ttc",
)


def ui_font(size: int = 13) -> ImageFont.ImageFont | ImageFont.FreeTypeFont:
    for path in MACOS_FONT_CANDIDATES:
        try:
            return ImageFont.truetype(path, size=size)
        except OSError:
            continue
    return ImageFont.load_default()


def make_preview(stickers: list[Image.Image]) -> Image.Image:
    thumb_size = (185, 160)
    gap = 12
    label_height = 24
    width = gap + 4 * (thumb_size[0] + gap)
    height = gap + 4 * (thumb_size[1] + label_height + gap)
    preview = Image.new("RGBA", (width, height), (225, 229, 235, 255))
    draw = ImageDraw.Draw(preview)
    font = ui_font()
    for index, sticker in enumerate(stickers):
        row, col = divmod(index, 4)
        x = gap + col * (thumb_size[0] + gap)
        y = gap + row * (thumb_size[1] + label_height + gap)
        tile = Image.new("RGBA", thumb_size, "white")
        small = sticker.copy()
        small.thumbnail(thumb_size, Image.Resampling.LANCZOS)
        tile.alpha_composite(small, ((thumb_size[0] - small.width) // 2, (thumb_size[1] - small.height) // 2))
        preview.alpha_composite(tile, (x, y))
        draw.text((x, y + thumb_size[1] + 5), f"{index + 1:02d}.png", fill=(30, 30, 30, 255), font=font)
    return preview


def make_wechat_preview(
    stickers: list[Image.Image],
    banner: Image.Image | None,
    zip_contents: list[str],
    validation_messages: list[str],
    complete: bool,
) -> Image.Image:
    """顯示貼圖、Banner、ZIP 內容及微信素材完整性。"""
    grid = make_preview(stickers)
    extra_height = 540
    result = Image.new("RGBA", (grid.width, grid.height + extra_height), (225, 229, 235, 255))
    result.alpha_composite(grid, (0, 0))
    draw = ImageDraw.Draw(result)
    font = ui_font()
    y = grid.height + 12
    draw.text((12, y), "WeChat Banner", fill=(20, 20, 20, 255), font=font)
    banner_box = (220, 120)
    banner_x, banner_y = 12, y + 20
    tile = Image.new("RGBA", banner_box, "white")
    if banner is not None:
        small = banner.copy()
        small.thumbnail(banner_box, Image.Resampling.LANCZOS)
        tile.alpha_composite(small, ((banner_box[0] - small.width) // 2, (banner_box[1] - small.height) // 2))
    else:
        ImageDraw.Draw(tile).text((58, 52), "No Banner", fill=(130, 50, 50, 255), font=font)
    result.alpha_composite(tile, (banner_x, banner_y))
    list_x = 255
    draw.text((list_x, y), f"ZIP Contents ({len(zip_contents)})", fill=(20, 20, 20, 255), font=font)
    lines = zip_contents[:10]
    if len(zip_contents) > 10:
        lines.append(f"... and {len(zip_contents) - 10} more")
    for offset, name in enumerate(lines, 1):
        draw.text((list_x, y + offset * 18), name, fill=(40, 40, 40, 255), font=font)
    status_y = y + 235
    status_color = (24, 120, 55, 255) if complete else (170, 65, 35, 255)
    for offset, message in enumerate(validation_messages):
        draw.text((12, status_y + offset * 18), message, fill=(35, 35, 35, 255), font=font)
    final_message = "微信素材符合上傳規格。" if complete else "微信素材尚未完整，可能無法直接提交。"
    draw.text((12, status_y + len(validation_messages) * 18 + 5), final_message, fill=status_color, font=font)
    return result
