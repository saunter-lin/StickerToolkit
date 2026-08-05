#!/usr/bin/env python3
"""建立供端到端測試使用的 4×4 合集圖。"""

from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

root = Path(__file__).resolve().parent
target = root / "input" / "test_sticker_sheet.png"
target.parent.mkdir(exist_ok=True)
cell_w, cell_h = 420, 360
sheet = Image.new("RGB", (cell_w * 4, cell_h * 4), "white")
font = ImageFont.load_default(size=28)

for index in range(16):
    row, col = divmod(index, 4)
    x0, y0 = col * cell_w, row * cell_h
    draw = ImageDraw.Draw(sheet)
    color = ((index * 47 + 70) % 210, (index * 83 + 60) % 210, (index * 31 + 90) % 210)
    cx, cy = x0 + cell_w // 2, y0 + 155
    # 耳朵、臉、尾巴與文字刻意延伸到不同方向，測試內容不被裁掉。
    draw.polygon([(cx - 95, cy - 75), (cx - 55, cy - 145), (cx - 20, cy - 65)], fill=color, outline="black", width=5)
    draw.polygon([(cx + 20, cy - 65), (cx + 70, cy - 145), (cx + 98, cy - 65)], fill=color, outline="black", width=5)
    draw.ellipse((cx - 105, cy - 85, cx + 105, cy + 105), fill=color, outline="black", width=5)
    draw.ellipse((cx - 50, cy - 25, cx - 34, cy - 9), fill="white")
    draw.ellipse((cx + 34, cy - 25, cx + 50, cy - 9), fill="white")
    draw.arc((cx + 85, cy + 20, cx + 160, cy + 105), 265, 90, fill=color, width=18)
    label = f"TEST {index + 1:02d}"
    box = draw.textbbox((0, 0), label, font=font, stroke_width=1)
    draw.text((cx - (box[2] - box[0]) // 2, y0 + 285), label, font=font, fill="black", stroke_width=1, stroke_fill="black")

sheet.save(target, "PNG")
print(target)
