#!/usr/bin/env python3
"""將 4×4 合集圖切割並製作 LINE 貼圖檔案。"""

from __future__ import annotations

import argparse
import sys
import subprocess
from collections import deque
from pathlib import Path

from PIL import Image, UnidentifiedImageError

from cover import MAIN_PADDING, MAIN_SIZE, TAB_PADDING, TAB_SIZE, make_main, make_tab
from exporter import create_zip, validate_png
from preview import make_preview

ROOT = Path(__file__).resolve().parent
INPUT_DIR = ROOT / "input"
OUTPUT_DIR = ROOT / "output"
STICKER_SIZE = (370, 320)

# 日後若要調整一般貼圖四周安全留白，修改此數值（單位：像素）。
STICKER_PADDING = 20

WHITE_THRESHOLD = 248
SUPPORTED_EXTENSIONS = {".png", ".jpg", ".jpeg"}


def newest_input() -> Path:
    INPUT_DIR.mkdir(exist_ok=True)
    files = [p for p in INPUT_DIR.iterdir() if p.is_file() and p.suffix.lower() in SUPPORTED_EXTENSIONS]
    if not files:
        raise RuntimeError("input 資料夾中找不到 PNG、JPG 或 JPEG 圖片。")
    return max(files, key=lambda p: (p.stat().st_mtime_ns, p.name))


def remove_edge_background(source: Image.Image) -> Image.Image:
    """將透明像素保留為透明，並只清除與邊界連通的近白背景。"""
    image = source.convert("RGBA")
    pixels = image.load()
    width, height = image.size
    seen = bytearray(width * height)
    queue: deque[tuple[int, int]] = deque()

    def is_background(x: int, y: int) -> bool:
        r, g, b, a = pixels[x, y]
        return a == 0 or (a > 0 and r >= WHITE_THRESHOLD and g >= WHITE_THRESHOLD and b >= WHITE_THRESHOLD)

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


def content_crop(image: Image.Image) -> Image.Image:
    alpha = image.getchannel("A")
    bbox = alpha.getbbox()
    if bbox is None:
        raise RuntimeError("偵測到空白格，沒有可輸出的貼圖內容。")
    return image.crop(bbox)


def fit_on_canvas(content: Image.Image, size: tuple[int, int], padding: int) -> Image.Image:
    max_width = size[0] - padding * 2
    max_height = size[1] - padding * 2
    if max_width <= 0 or max_height <= 0:
        raise ValueError("安全留白過大，畫布沒有可用空間。")
    fitted = content.copy()
    fitted.thumbnail((max_width, max_height), Image.Resampling.LANCZOS)
    canvas = Image.new("RGBA", size, (0, 0, 0, 0))
    position = ((size[0] - fitted.width) // 2, (size[1] - fitted.height) // 2)
    canvas.alpha_composite(fitted, position)
    return canvas


def split_grid(image: Image.Image) -> list[Image.Image]:
    width, height = image.size
    if width < 4 or height < 4:
        raise RuntimeError("輸入圖片尺寸太小，無法切成 4×4。")
    x_edges = [round(i * width / 4) for i in range(5)]
    y_edges = [round(i * height / 4) for i in range(5)]
    return [
        image.crop((x_edges[col], y_edges[row], x_edges[col + 1], y_edges[row + 1]))
        for row in range(4)
        for col in range(4)
    ]


def choose_sticker(label: str, supplied: int | None, interactive: bool) -> int:
    if supplied is not None:
        if 1 <= supplied <= 16:
            return supplied
        raise RuntimeError(f"{label} 必須是 1～16。")
    if not interactive:
        return 1
    while True:
        answer = input(f"請選擇 {label} 使用的貼圖（1～16，直接 Enter 使用 01）：").strip()
        if not answer:
            return 1
        if answer.isdigit() and 1 <= int(answer) <= 16:
            return int(answer)
        print("輸入無效，請輸入 1～16。")


def open_on_macos(path: Path) -> None:
    if sys.platform == "darwin":
        subprocess.run(["open", str(path)], check=False)


def process(source_path: Path, main_choice: int | None, tab_choice: int | None, interactive: bool, open_preview: bool) -> None:
    OUTPUT_DIR.mkdir(exist_ok=True)
    try:
        with Image.open(source_path) as opened:
            source = opened.convert("RGBA")
    except (UnidentifiedImageError, OSError) as exc:
        raise RuntimeError(f"無法讀取圖片 {source_path.name}：{exc}") from exc

    print(f"選用輸入圖片：{source_path.name}")
    cells = split_grid(source)
    contents = [content_crop(remove_edge_background(cell)) for cell in cells]
    stickers = [fit_on_canvas(content, STICKER_SIZE, STICKER_PADDING) for content in contents]

    sticker_paths: list[Path] = []
    for index, sticker in enumerate(stickers, 1):
        path = OUTPUT_DIR / f"{index:02d}.png"
        sticker.save(path, "PNG")
        sticker_paths.append(path)

    preview_path = OUTPUT_DIR / "preview.png"
    make_preview(stickers).save(preview_path, "PNG")
    print(f"16 張貼圖縮圖已建立：{preview_path}")
    if open_preview:
        open_on_macos(preview_path)

    selected_main = choose_sticker("main.png", main_choice, interactive)
    selected_tab = choose_sticker("tab.png", tab_choice, interactive)
    main_path = OUTPUT_DIR / "main.png"
    tab_path = OUTPUT_DIR / "tab.png"
    make_main(stickers[selected_main - 1]).save(main_path, "PNG")
    make_tab(stickers[selected_tab - 1]).save(tab_path, "PNG")

    for path in sticker_paths:
        validate_png(path, STICKER_SIZE)
    validate_png(main_path, MAIN_SIZE)
    validate_png(tab_path, TAB_SIZE)

    zip_path = OUTPUT_DIR / "line_stickers.zip"
    create_zip(zip_path, [*sticker_paths, main_path, tab_path])
    print("\n====================================")
    print("Sticker Toolkit Export Finished")
    print(f"Input：\n{source_path.name}")
    print("Sticker：\n16")
    print(f"Main：\n{selected_main:02d}.png")
    print(f"Tab：\n{selected_tab:02d}.png")
    print("Output：\noutput/")
    print("ZIP：\nline_stickers.zip")
    print("====================================")
    if open_preview:
        open_on_macos(preview_path)


def main() -> int:
    parser = argparse.ArgumentParser(description="Sticker Toolkit V1.1")
    parser.add_argument("--input", type=Path, help="指定圖片；未指定時使用 input 中最新修改者")
    parser.add_argument("--main", type=int, help="main.png 使用的貼圖編號（1～16）")
    parser.add_argument("--tab", type=int, help="tab.png 使用的貼圖編號（1～16）")
    parser.add_argument("--interactive", action="store_true", help="在終端機互動選擇 main 與 tab")
    parser.add_argument("--open-preview", action="store_true", help="在 macOS 自動開啟 preview.png")
    args = parser.parse_args()
    try:
        selected = args.input.resolve() if args.input else newest_input()
        if not selected.is_file():
            raise RuntimeError(f"找不到輸入圖片：{selected}")
        process(selected, args.main, args.tab, args.interactive, args.open_preview)
        return 0
    except Exception as exc:
        print(f"錯誤：{exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
