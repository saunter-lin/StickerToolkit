"""Sticker Toolkit 的 16 格選擇／輸出預覽。"""

from PIL import Image, ImageDraw, ImageFont


def make_preview(stickers: list[Image.Image]) -> Image.Image:
    thumb_size = (185, 160)
    gap = 12
    label_height = 24
    width = gap + 4 * (thumb_size[0] + gap)
    height = gap + 4 * (thumb_size[1] + label_height + gap)
    preview = Image.new("RGBA", (width, height), (225, 229, 235, 255))
    draw = ImageDraw.Draw(preview)
    font = ImageFont.load_default()
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
