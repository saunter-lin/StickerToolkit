"""LINE 平台輸出。"""

from __future__ import annotations

from pathlib import Path

from PIL import Image

from core.config import LINE_CONFIG
from core.images import contain

from .common import save_rgba_png, validate_png, write_zip


def export_line(stickers: list[Image.Image], output_dir: Path, main_index: int, tab_index: int) -> Path:
    if LINE_CONFIG.main_size is None or LINE_CONFIG.tab_size is None:
        raise RuntimeError("LINE_CONFIG 缺少 main 或 tab 尺寸。")
    sticker_paths: list[Path] = []
    for index, sticker in enumerate(stickers, 1):
        path = output_dir / f"{index:02d}.png"
        save_rgba_png(sticker, path)
        validate_png(path, LINE_CONFIG.sticker_size)
        sticker_paths.append(path)
    main_path = output_dir / "main.png"
    tab_path = output_dir / "tab.png"
    main_image = contain(stickers[main_index - 1], LINE_CONFIG.main_size, LINE_CONFIG.main_padding)
    save_rgba_png(main_image, main_path)
    save_rgba_png(contain(stickers[tab_index - 1], LINE_CONFIG.tab_size, LINE_CONFIG.tab_padding), tab_path)
    validate_png(main_path, LINE_CONFIG.main_size)
    validate_png(tab_path, LINE_CONFIG.tab_size)
    zip_path = output_dir / LINE_CONFIG.zip_name
    entries = [(path, path.name) for path in [*sticker_paths, main_path, tab_path]]
    write_zip(zip_path, entries)
    # v1 相容：保留原始 ZIP 名稱，內容與正式 v1.2 套件相同。
    write_zip(output_dir / "line_stickers.zip", entries)
    return zip_path
