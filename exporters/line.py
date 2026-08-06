"""LINE 平台輸出。"""

from __future__ import annotations

from pathlib import Path

from PIL import Image

from core.config import LINE_CONFIG
from core.images import StickerError, contain

from .common import save_rgba_png, validate_png, write_zip

OLD_LINE_ZIP_NAMES = ("line_sticker_package.zip", "line_stickers.zip")


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
    for old_name in OLD_LINE_ZIP_NAMES:
        old_path = output_dir / old_name
        try:
            old_path.unlink(missing_ok=True)
        except OSError as exc:
            raise StickerError(f"無法清除舊版 LINE ZIP：{old_name}（{exc}）") from exc
    write_zip(zip_path, entries)
    return zip_path
